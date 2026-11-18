#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p reports
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python -m compileall -q src tests examples scripts
python -m coverage erase
python -m coverage run --branch -m pytest -q --junitxml=reports/junit-results.xml | tee reports/test-run.log
python -m coverage report --fail-under=80 | tee reports/coverage-report.txt
python -m coverage json -o reports/coverage.json
