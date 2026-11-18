"""Command-line validator for ETC JSON contracts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .canonical import strict_json_loads
from .contract import evaluate_trace_closure, validate_contract
from .errors import ECAError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eca-validate", description="Validate an ECA ETC contract (structural + local semantic checks).")
    parser.add_argument("contract", type=Path, help="path to ETC JSON file")
    parser.add_argument("--phase", choices=["PRE", "POST", "ACCOUNTABILITY"], help="also report closure for a lifecycle phase")
    parser.add_argument("--now", help="evaluation time as RFC 3339; defaults to current UTC")
    args = parser.parse_args(argv)
    try:
        contract = strict_json_loads(args.contract.read_text(encoding="utf-8"))
        from datetime import datetime
        now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else None
        result = {"contract_validation": validate_contract(contract, now=now)}
        if args.phase:
            result["trace_closure"] = evaluate_trace_closure(contract, args.phase, now=now)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ECAError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
