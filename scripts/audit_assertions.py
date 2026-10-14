#!/usr/bin/env python3
"""Export all generated test functions and their assertions for human oracle review."""
import argparse
import ast
import csv
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('test_paths', nargs='+', help='Python files or directories to scan recursively')
ap.add_argument('--output', default='results/assertion_audit.csv')
args = ap.parse_args()
files = []
for path in map(Path, args.test_paths):
    if path.is_file() and path.suffix == '.py': files.append(path)
    elif path.is_dir(): files.extend(path.rglob('test_coverup*.py'))
files = sorted(set(files))
rows = []
for file in files:
    source = file.read_text(encoding='utf-8')
    try: tree = ast.parse(source, filename=str(file))
    except SyntaxError as e:
        rows.append({'file':str(file),'test':'PARSE_ERROR','line':e.lineno,'assertion':str(e),'expected_value_source':'','specification_reference':'','assertion_echo_risk':'','review_notes':''})
        continue
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith('test_'): continue
        assertions = [a for a in ast.walk(node) if isinstance(a, ast.Assert)]
        if not assertions:
            rows.append({'file':str(file),'test':node.name,'line':node.lineno,'assertion':'NO_ASSERT_FOUND','expected_value_source':'','specification_reference':'','assertion_echo_risk':'','review_notes':''})
        for a in assertions:
            rows.append({'file':str(file),'test':node.name,'line':a.lineno,'assertion':ast.get_source_segment(source,a) or ast.unparse(a),'expected_value_source':'','specification_reference':'','assertion_echo_risk':'','review_notes':''})
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
fields = ['file','test','line','assertion','expected_value_source','specification_reference','assertion_echo_risk','review_notes']
with output.open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f'Wrote {len(rows)} assertion rows from {len(files)} files to {output}')
