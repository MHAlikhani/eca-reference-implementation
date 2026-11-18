#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p reports dist
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python - <<'PY' | tee reports/package-check.log
from eca_reference.schema import validate_schema_definition
from eca_reference.contract import validate_contract
from eca_reference.canonical import strict_json_loads
from datetime import datetime, timezone
from pathlib import Path
import json
validate_schema_definition()
p = Path('examples/municipal-composite-contract.example.json')
contract = strict_json_loads(p.read_text(encoding='utf-8'))
result = validate_contract(contract, now=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc))
assert result['valid'] is True
print('PASS: Draft 2020-12 schema self-check')
print('PASS: synthetic example structural/semantic validation')
print('example request digest:', result['request_digest'])
PY
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist . 2>&1 | tee -a reports/package-check.log
python - <<'PY' | tee -a reports/package-check.log
from pathlib import Path
wheels = list(Path('dist').glob('eca_reference-2.0.0-*.whl'))
assert len(wheels) == 1, f'expected one wheel, found {wheels}'
print('PASS: wheel built:', wheels[0].name)
PY
