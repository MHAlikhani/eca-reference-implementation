from __future__ import annotations
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from factories import make_contract
from eca_reference.contract import validate_contract
from datetime import datetime, timezone
contract = make_contract()
validate_contract(contract, now=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc))
out = Path(__file__).with_name("municipal-composite-contract.example.json")
out.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(out)
