#!/usr/bin/env python3
"""Check that every TLC config reference names a declared model predicate.

This is a name-consistency check, not a TLA+ parser or model checker.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

model = Path(sys.argv[1] if len(sys.argv) > 1 else "tla/ECA_Lifecycle.tla")
config = Path(sys.argv[2] if len(sys.argv) > 2 else "tla/ECA_Lifecycle.cfg")
source = model.read_text(encoding="utf-8")
cfg = config.read_text(encoding="utf-8")
definitions = set(re.findall(r"(?m)^([A-Za-z][A-Za-z0-9_]*)\s*==", source))
invariants = re.findall(r"(?m)^INVARIANT\s+([A-Za-z][A-Za-z0-9_]*)\s*$", cfg)
specs = re.findall(r"(?m)^SPECIFICATION\s+([A-Za-z][A-Za-z0-9_]*)\s*$", cfg)
if specs != ["Spec"] or "Spec" not in definitions:
    raise SystemExit("FAIL: cfg must reference the declared Spec definition exactly once")
if not invariants:
    raise SystemExit("FAIL: cfg contains no INVARIANT declarations")
missing = sorted(set(invariants) - definitions)
if missing:
    raise SystemExit(f"FAIL: cfg invariant(s) not defined in module: {missing}")
if len(invariants) != len(set(invariants)):
    raise SystemExit("FAIL: duplicate invariant reference in cfg")
required = {
    "TypeOK", "NoReserveWithoutActionReady", "NoDispatchWithoutCapturedReadiness",
    "NoEffectWithoutDispatchIntent", "NoFalseTerminalReceipt", "PostClosureRequiresGuardClosure",
    "UnknownHasNoVerifiedReceipt", "PostClosureSoundness",
    "AccountabilityClosureSoundness", "NonceIsNotReused",
}
missing_required = sorted(required - set(invariants))
if missing_required:
    raise SystemExit(f"FAIL: required invariant(s) omitted from cfg: {missing_required}")
print(f"PASS: {len(invariants)} TLC invariants and Spec references resolve by name")
print("LIMIT: this check does not establish TLA+ grammar validity or model-checking results.")
