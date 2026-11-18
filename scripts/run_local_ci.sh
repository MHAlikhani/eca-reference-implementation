#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p reports dist
LOG="$ROOT/reports/local-ci.log"
exec > >(tee "$LOG") 2>&1

printf 'ECA LOCAL CI START %s\n' "$(date -u +%FT%TZ)"
printf 'Python: '; python --version
printf 'Java: '; java -version 2>&1 | head -1

python - <<'PY'
import sys
assert sys.version_info >= (3, 11), f"Python >=3.11 required, got {sys.version}"
print("PASS: supported Python runtime")
try:
    import yaml
    from pathlib import Path
    workflow = yaml.safe_load(Path('.github/workflows/verification.yml').read_text())
    assert isinstance(workflow, dict) and 'jobs' in workflow
    assert {'python', 'tla'} <= set(workflow['jobs'])
    print('PASS: GitHub Actions workflow YAML parses and contains python/tla jobs')
except ImportError:
    print('SKIP: PyYAML unavailable; workflow YAML parse not run')
PY

python -m compileall -q src tests examples scripts
printf 'PASS: Python compileall\n'
bash scripts/run_tests.sh
bash scripts/check_package.sh
python scripts/check_tla_config.py tla/ECA_Lifecycle.tla tla/ECA_Lifecycle.cfg
python scripts/audit_tla_lexically.py tla/ECA_Lifecycle.tla
python scripts/run_explicit_state_check.py

# Install the built wheel into an isolated target directory and invoke its CLI.
TMP_SITE="$(mktemp -d)"
trap 'rm -rf "$TMP_SITE"' EXIT
python -m pip install --no-index --no-deps --target "$TMP_SITE" dist/eca_reference-2.0.0-py3-none-any.whl
PYTHONPATH="$TMP_SITE" python - "$TMP_SITE" <<'PY'
import sys
from pathlib import Path
import eca_reference
assert Path(eca_reference.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve()), eca_reference.__file__
from eca_reference.cli import main
raise SystemExit(main(['examples/municipal-composite-contract.example.json', '--phase', 'PRE', '--now', '2026-11-18T12:00:00+00:00']))
PY

if [[ -f tools/tla2tools.jar ]]; then
  bash scripts/run_tla.sh 2>&1 | tee reports/tla-official-run.log
  echo 'OFFICIAL_TLA=PASS' > reports/local-ci-formal-status.txt
else
  echo 'OFFICIAL_TLA=BLOCKED_NO_PINNED_JAR' | tee reports/local-ci-formal-status.txt
  echo 'Alternative finite-state exhaustive checker passed; this does not replace SANY/TLC parsing or checking.'
fi

printf 'ECA LOCAL CI PASS %s\n' "$(date -u +%FT%TZ)"
