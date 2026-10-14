#!/usr/bin/env python3
"""Run isolated CoverUp A/B repetitions and collect independent coverage metrics."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path.cwd()

def run(cmd, env, logfile):
    start = time.perf_counter()
    with logfile.open('w', encoding='utf-8') as out:
        out.write('COMMAND: ' + ' '.join(map(str, cmd)) + '\n\n')
        out.flush()
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, round(time.perf_counter() - start, 3)

def coverage_data(path):
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        totals = data.get('totals', {})
        return {f'cov_{k}': totals.get(k) for k in ('percent_covered', 'num_statements', 'missing_lines', 'num_branches', 'missing_branches', 'num_partial_branches')}
    except (ValueError, OSError):
        return {}

def extract_coverup(logpath):
    if not logpath.exists():
        return {}
    s = logpath.read_text(encoding='utf-8', errors='replace')
    result = {}
    # Keep raw progress lines for manual verification; formats differ across versions.
    lines = [x for x in s.splitlines() if re.search(r'\bG\s*=\s*\d+|\bF\s*=\s*\d+|\bU\s*=\s*\d+|\bR\s*=\s*\d+', x)]
    if lines:
        last = lines[-1]
        for key in ('G','F','U','R'):
            match = re.search(r'\b'+key+r'\s*=\s*(\d+)', last)
            if match: result[key] = int(match.group(1))
        result['coverup_last_progress'] = last[:400]
    result['coverup_log_bytes'] = logpath.stat().st_size
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=3)
    ap.add_argument('--variants', nargs='+', choices=['a','b'], default=['a','b'])
    ap.add_argument('--source-tests', default='experiment_a/tests')
    ap.add_argument('--output', default='results/repeated_study')
    ap.add_argument('--model', default='gpt-4o')
    args = ap.parse_args()
    source = (ROOT / args.source_tests).resolve()
    if not source.is_dir():
        ap.error(f'Original tests directory not found: {source}')
    generated = list(source.glob('test_coverup*.py'))
    if generated:
        ap.error(f'Source tests already contain generated tests: {generated}. Provide a CLEAN original tests directory.')
    outroot = (ROOT / args.output).resolve()
    outroot.mkdir(parents=True, exist_ok=True)
    rows = []
    for variant in args.variants:
        for index in range(1, args.runs + 1):
            name = f'{variant}_run_{index:02d}'
            out = outroot / name
            if out.exists():
                ap.error(f'{out} already exists; refusing to overwrite a previous run.')
            out.mkdir(parents=True)
            tests = out / 'tests'
            shutil.copytree(source, tests, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', '*.pyc', '.coverage*'))
            env = os.environ.copy()
            py_paths = [str(ROOT / 'fastapi')]
            if variant == 'b':
                patch = ROOT / 'experiment_b' / 'runtime'
                if not (patch / 'sitecustomize.py').exists():
                    ap.error(f'B prompt patch not found: {patch / "sitecustomize.py"}')
                py_paths.insert(0, str(patch))
            if env.get('PYTHONPATH'):
                py_paths.append(env['PYTHONPATH'])
            env['PYTHONPATH'] = os.pathsep.join(py_paths)
            env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
            env.pop('PYTEST_ADDOPTS', None)
            row = {'variant': variant.upper(), 'run': index, 'output_dir': str(out.relative_to(ROOT)), 'model': args.model, 'max_attempts': 2 if variant == 'a' else 5}
            baseline_json = out / 'baseline_coverage.json'
            cmd_base = [sys.executable, '-m', 'pytest', str(tests), '-p', 'pytest_cov', '--cov=fastapi.encoders', '--cov-branch', '--cov-report=term-missing', f'--cov-report=json:{baseline_json}', '-W', 'ignore::DeprecationWarning']
            rc, elapsed = run(cmd_base, env, out / 'baseline_pytest.log')
            row.update(baseline_exit_code=rc, baseline_seconds=elapsed)
            row.update({'baseline_'+k: v for k,v in coverage_data(baseline_json).items()})
            if rc != 0:
                row['status'] = 'BASELINE_FAILED'
                rows.append(row)
                print(f'{name}: baseline FAILED; skipping CoverUp', flush=True)
                continue
            cover_env = env.copy()
            cover_env['PYTEST_ADDOPTS'] = '-p pytest_repeat'
            log = out / 'coverup.log'
            cmd = ['coverup', 'fastapi/fastapi/encoders.py', '--tests-dir', str(tests), '--model', args.model, '--prompt', 'gpt-v2', '--no-add-to-pythonpath', '--no-isolate-tests', '--pytest-args=-W ignore::DeprecationWarning', '--max-concurrency', '1', '--max-attempts', str(row['max_attempts']), '--max-backoff', '8', '--log-file', str(log), '--save-coverage-to', str(out), '--debug']
            print(f'{name}: running CoverUp ...', flush=True)
            rc, elapsed = run(cmd, cover_env, out / 'coverup_console.log')
            row.update(coverup_exit_code=rc, coverup_wall_seconds=elapsed)
            row.update(extract_coverup(log))
            final_json = out / 'final_coverage.json'
            cmd_final = [sys.executable, '-m', 'pytest', str(tests), '-p', 'pytest_cov', '--cov=fastapi.encoders', '--cov-branch', '--cov-report=term-missing', f'--cov-report=json:{final_json}', '-W', 'ignore::DeprecationWarning']
            rc_final, elapsed_final = run(cmd_final, env, out / 'final_pytest.log')
            row.update(final_exit_code=rc_final, final_seconds=elapsed_final)
            row.update({'final_'+k: v for k,v in coverage_data(final_json).items()})
            row['generated_test_files'] = ';'.join(p.name for p in sorted(tests.glob('test_coverup*.py')))
            row['status'] = 'OK' if rc == 0 and rc_final == 0 else 'REVIEW'
            (out / 'metrics.json').write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding='utf-8')
            rows.append(row)
            print(f'{name}: status={row["status"]}, CoverUp={elapsed}s, final coverage={row.get("final_cov_percent_covered", "N/A")}', flush=True)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with (outroot / 'summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f'\nSummary: {outroot / "summary.csv"}')

if __name__ == '__main__':
    main()
