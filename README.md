# CoverUp Study — FastAPI Encoder Test Generation

## Setup

Run commands from the **project root** (except the Git commands with `-C fastapi`). The `fastapi/` source repository is excluded from Git and must be cloned separately.

```bash
# Clone the target project
 git clone https://github.com/fastapi/fastapi.git fastapi
 git -C fastapi checkout 0.115.6
 git -C fastapi rev-parse HEAD
 git -C fastapi describe --tags --always

# Python environment
python3 -m venv venv
source venv/bin/activate
python3 --version  # Experiment environment: Python 3.10.9
python3 -m pip install -r requirements.txt

# Check which FastAPI is imported
PYTHONPATH="$PWD/fastapi" python3 -c 'import fastapi; print(fastapi.__file__, fastapi.__version__)'

# API key (required only for non-dry runs)
export OPENAI_API_KEY="YOUR_API_KEY"
test -n "$OPENAI_API_KEY" && echo "API Key configured"

mkdir -p results/experiment_a results/experiment_b
```

## Baseline (independent pytest-cov)

```bash
PYTHONPATH="$PWD/fastapi" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest baseline/tests/ -p pytest_cov \
  --cov=fastapi.encoders --cov-branch --cov-report=term-missing \
  --cov-report=json:results/experiment_a/baseline_coverage.json \
  -W ignore::DeprecationWarning
```

Recorded baseline: **18 passed, 3 skipped; 82.24% combined coverage**.

## Experiment A — Default CoverUp

```bash
# Dry run (no LLM API calls)
PYTHONPATH="$PWD/fastapi" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_a/tests --model gpt-4o --prompt gpt-v2 \
  --no-add-to-pythonpath --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" --dry-run --debug

# Actual run (uses paid API)
PYTHONPATH="$PWD/fastapi" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_a/tests --model gpt-4o --prompt gpt-v2 \
  --no-add-to-pythonpath --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" \
  --max-concurrency 1 --max-attempts 2 --max-backoff 8 \
  --log-file results/experiment_a/coverup.log \
  --save-coverage-to results/experiment_a --debug
```

Original run: **G=0, F=2; SlipCover 89.2% → 89.2%**.

## Experiment B — Environment-aware Prompt

Uses `experiment_b/runtime/sitecustomize.py` for Pydantic v2 guidance, with `--max-attempts 5`.

```bash
# Dry run (no LLM API calls)
PYTHONPATH="$PWD/experiment_b/runtime:$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_b/tests --model gpt-4o --prompt gpt-v2 \
  --no-add-to-pythonpath --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" --dry-run --debug

# Actual run (uses paid API)
PYTHONPATH="$PWD/experiment_b/runtime:$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_b/tests --model gpt-4o --prompt gpt-v2 \
  --no-add-to-pythonpath --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" \
  --max-concurrency 1 --max-attempts 5 --max-backoff 8 \
  --log-file results/experiment_b/coverup.log \
  --save-coverage-to results/experiment_b --debug
```

Original run: **G=1, F=2; SlipCover 89.2% → 93.2%**.

> **Note:** `experiment_b/tests/` already contains an AI-generated test. For a fresh baseline or independent reproduction, start from `baseline/tests/` rather than treating the existing B tests as the baseline.

## Independent final coverage

```bash
# Experiment A
PYTHONPATH="$PWD/fastapi" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest experiment_a/tests/ -p pytest_cov \
  --cov=fastapi.encoders --cov-branch --cov-report=term-missing \
  --cov-report=json:results/experiment_a/final_coverage.json \
  -W ignore::DeprecationWarning

# Experiment B
PYTHONPATH="$PWD/fastapi" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest experiment_b/tests/ -p pytest_cov \
  --cov=fastapi.encoders --cov-branch --cov-report=term-missing \
  --cov-report=json:results/experiment_b/final_coverage.json \
  -W ignore::DeprecationWarning
```

Original Experiment B validation: **26 passed, 3 skipped; ~89% pytest-cov coverage**.

## Three repeated runs per variant

```bash
python3 scripts/run_experiments.py \
  --runs 3 --variants a b \
  --source-tests baseline/tests \
  --output results/repeated_study

python3 scripts/audit_assertions.py results/repeated_study \
  --output results/assertion_audit_all.csv
```

| Metric | A (default) | B (prompt + more attempts) |
|---|---:|---:|
| Mean final coverage (pytest-cov) | 85.75% | 88.38% |
| Mean coverage gain | +3.51 pp | +6.14 pp |
| Runs improving coverage | 1/3 | 3/3 |
| Mean CoverUp wall time | 37.08 s | 61.59 s |

Six runs together: **40 API requests, 289,194 tokens, US$0.53** (dashboard before/after difference, assuming no other usage). Average **~US$0.088 per run**. Results: `results/repeated_study/summary.csv`.

**Interpretation:** B changes both the prompt and the maximum attempts, so the effect cannot be attributed to the prompt alone. Coverage does not establish bug-detection ability.
