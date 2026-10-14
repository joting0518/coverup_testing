# 建立虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 確認 Python 版本
python3 --version

# 安裝套件
python3 -m pip install -r requirements.txt

# 將 Git Commit Hash 記錄到實驗報告，確保三次 Run 使用相同的原始碼
git -C fastapi rev-parse HEAD
f5c6e9b4f9cadc1bf0f9a1fd672e621206b63007
git -C fastapi describe --tags --always
0.143.0
# 這樣實際測試的原始碼才會是 FastAPI 0.115.6。
git checkout 0.115.6

# 確認 Encoder 的既有測試
find tests -iname '*encoder*'
tests/test_datetime_custom_encoder.py
tests/test_jsonable_encoder.py
tests/test_tutorial/test_encoder

# 實際跑一次官方的測試
python3 -m pytest tests/test_jsonable_encoder.py -q

# 測量紀錄baseline
python3 -m pytest tests/test_jsonable_encoder.py \
  --cov=fastapi.encoders \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=html:../results/experiment_a/baseline/htmlcov \
  --cov-report=json:../results/experiment_a/baseline/coverage.json \
  -W ignore::pytest_cov.CentralCovContextWarning \
  2>&1 | tee ../results/experiment_a/baseline/pytest_output.txt

# 設定 api key
export OPENAI_API_KEY="api-key"                                                        
test -n "$OPENAI_API_KEY" && echo "API Key configured"

# 修改使用的 fastapi，不用 venv 提供的
PYTHONPATH="$PWD/fastapi" \
python3 -c "import fastapi; print(fastapi.__file__)"

# Baseline Coverage（Experiment A）
使用原始測試，不呼叫 GPT-4o，透過 pytest-cov 建立 Baseline。

PYTHONPATH="$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest experiment_a/tests/ \
  -p pytest_cov \
  --cov=fastapi.encoders \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=json:results/experiment_a/baseline_coverage.json \
  -W ignore::DeprecationWarning

18 passed, 3 skipped，pytest-cov Coverage 82%。

# Experiment A：Original CoverUp
A-1. Dry Run（免費）
只分析未覆蓋程式碼，不呼叫 GPT-4o。
PYTHONPATH="$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_a/tests \
  --model gpt-4o \
  --prompt gpt-v2 \
  --no-add-to-pythonpath \
  --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" \
  --dry-run \
  --debug

A-2. 正式執行（產生 API 費用）
PYTHONPATH="$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_a/tests \
  --model gpt-4o \
  --prompt gpt-v2 \
  --no-add-to-pythonpath \
  --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" \
  --max-concurrency 1 \
  --max-attempts 2 \
  --max-backoff 8 \
  --log-file results/experiment_a/coverup.log \
  --save-coverage-to results/experiment_a \
  --debug


原始結果：G=0, F=2，SlipCover 89.2% → 89.2%。

# experiment B
Experiment B：Prompt-enhanced CoverUp
Experiment B 使用 experiment_b/runtime/sitecustomize.py，加入 Pydantic V2 環境資訊及錯誤修正指引，並將 --max-attempts 從 2 增加至 5。
B-1. Baseline Coverage
確保 experiment_b/tests/ 尚未加入 AI-generated tests 時執行，才能取得真正的 Baseline。若目前已包含 test_coverup_1.py，請勿直接把結果當成 Baseline。
PYTHONPATH="$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest experiment_b/tests/test_jsonable_encoder.py \
  -p pytest_cov \
  --cov=fastapi.encoders \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=json:results/experiment_b/baseline_coverage.json \
  -W ignore::DeprecationWarning


B-2. Dry Run（免費）
PYTHONPATH="$PWD/experiment_b/runtime:$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_b/tests \
  --model gpt-4o \
  --prompt gpt-v2 \
  --no-add-to-pythonpath \
  --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" \
  --dry-run \
  --debug


注意：現在 Experiment B 已有生成的測試，重新 Dry Run 可能會得到較高的初始 Coverage，而非當初的 89.2%。
B-3. 正式執行（產生 API 費用）
PYTHONPATH="$PWD/experiment_b/runtime:$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTEST_ADDOPTS="-p pytest_repeat" \
coverup fastapi/fastapi/encoders.py \
  --tests-dir experiment_b/tests \
  --model gpt-4o \
  --prompt gpt-v2 \
  --no-add-to-pythonpath \
  --no-isolate-tests \
  --pytest-args="-W ignore::DeprecationWarning" \
  --max-concurrency 1 \
  --max-attempts 5 \
  --max-backoff 8 \
  --log-file results/experiment_b/coverup.log \
  --save-coverage-to results/experiment_b \
  --debug


原始結果：G=1, F=2，SlipCover 89.2% → 93.2%。

# pytest-cov 最終驗證
Experiment A
PYTHONPATH="$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest experiment_a/tests/ \
  -p pytest_cov \
  --cov=fastapi.encoders \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=json:results/experiment_a/final_coverage.json \
  -W ignore::DeprecationWarning


Experiment B
PYTHONPATH="$PWD/fastapi" \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest experiment_b/tests/ \
  -p pytest_cov \
  --cov=fastapi.encoders \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=json:results/experiment_b/final_coverage.json \
  -W ignore::DeprecationWarning


Experiment B 已驗證：26 passed, 3 skipped，Coverage 89%。