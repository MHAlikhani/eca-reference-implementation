#!/usr/bin/env python3
"""Independent exhaustive checker for the finite ECA lifecycle abstraction.

This is NOT SANY, TLC, or a TLA+ parser. It is an independently executable
transition-system mirror used when the official TLA+ JAR is unavailable.
It exhaustively explores every allowed initial Boolean valuation and every
reachable successor in the finite abstraction, then checks the ten invariants
listed in ECA_Lifecycle.cfg. Keep the mirror and TLA+ module synchronized.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from itertools import product
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "tla" / "ECA_Lifecycle.tla"
CONFIG = ROOT / "tla" / "ECA_Lifecycle.cfg"

@dataclass(frozen=True, slots=True)
class S:
    requestValid: bool
    preTraceClosed: bool
    preObligationsDischarged: bool
    nativePermit: bool
    nativeBindingExact: bool
    requiredApprovalsPresent: bool
    boundaryActive: bool
    nativeAuthorizationVerified: bool
    concurrentGuardsActive: bool
    revocationClear: bool
    postTraceClosed: bool
    postDutiesDischarged: bool
    challengeRouteAvailable: bool
    reviewResolved: bool
    phase: str
    nonceConsumed: bool
    dispatchReadinessCaptured: bool
    reservationReadinessCaptured: bool
    receiptVerified: bool
    concurrentGuardClosureRecorded: bool
    concurrentGuardClosureEvidenceVerified: bool
    effectResult: str
    postClosed: bool
    accountabilityClosed: bool

    def base_ready(self) -> bool:
        return all((self.requestValid, self.preTraceClosed,
                    self.preObligationsDischarged, self.nativePermit,
                    self.nativeBindingExact, self.requiredApprovalsPresent,
                    self.boundaryActive, self.nativeAuthorizationVerified,
                    self.concurrentGuardsActive, self.revocationClear))

TERMINAL = {"COMMITTED", "REJECTED", "RECONCILED"}
PHASES = {"IDLE", "RESERVED", "INTENT", "UNKNOWN", "COMMITTED", "REJECTED", "RECONCILED", "CANCELLED"}
EFFECTS = {"NONE", "UNKNOWN", "COMMITTED", "REJECTED"}


def initial_states():
    # Exactly the 14 unconstrained Boolean inputs in TLA+ Init.
    for bits in product((False, True), repeat=14):
        (requestValid, preTraceClosed, preObligationsDischarged, nativePermit,
         nativeBindingExact, requiredApprovalsPresent, boundaryActive,
         nativeAuthorizationVerified, concurrentGuardsActive, postTraceClosed,
         postDutiesDischarged, challengeRouteAvailable, reviewResolved,
         concurrentGuardClosureEvidenceVerified) = bits
        yield S(requestValid, preTraceClosed, preObligationsDischarged,
                nativePermit, nativeBindingExact, requiredApprovalsPresent,
                boundaryActive, nativeAuthorizationVerified,
                concurrentGuardsActive, True, postTraceClosed,
                postDutiesDischarged, challengeRouteAvailable, reviewResolved,
                "IDLE", False, False, False, False, False,
                concurrentGuardClosureEvidenceVerified, "NONE", False, False)


def successors(s: S):
    # Reserve
    if s.phase == "IDLE" and s.base_ready() and not s.nonceConsumed:
        yield "Reserve", replace(s, phase="RESERVED", nonceConsumed=True,
                                  reservationReadinessCaptured=True)
    # Dispatch (second readiness check)
    if s.phase == "RESERVED" and s.base_ready() and s.nonceConsumed:
        yield "Dispatch", replace(s, phase="INTENT", dispatchReadinessCaptured=True)
    # CancelAfterReadinessLoss
    if s.phase == "RESERVED" and not s.base_ready():
        yield "CancelAfterReadinessLoss", replace(s, phase="CANCELLED")
    # Revoke
    if s.revocationClear:
        yield "Revoke", replace(s, revocationClear=False)
    # TargetCommit / TargetReject / LoseReceipt
    if s.phase == "INTENT":
        yield "TargetCommit", replace(s, phase="COMMITTED", receiptVerified=True,
                                       effectResult="COMMITTED")
        yield "TargetReject", replace(s, phase="REJECTED", receiptVerified=True,
                                       effectResult="REJECTED")
        yield "LoseReceipt", replace(s, phase="UNKNOWN", receiptVerified=False,
                                      effectResult="UNKNOWN")
        if s.concurrentGuardsActive:
            yield "ConcurrentGuardLost", replace(s, phase="UNKNOWN",
                concurrentGuardsActive=False, receiptVerified=False,
                effectResult="UNKNOWN")
    # ReconcileCommit / ReconcileReject
    if s.phase == "UNKNOWN":
        yield "ReconcileCommit", replace(s, phase="RECONCILED", receiptVerified=True,
                                         effectResult="COMMITTED")
        yield "ReconcileReject", replace(s, phase="RECONCILED", receiptVerified=True,
                                         effectResult="REJECTED")
    # RecordConcurrentGuardClosure
    if s.phase in TERMINAL and s.concurrentGuardClosureEvidenceVerified and not s.concurrentGuardClosureRecorded:
        yield "RecordConcurrentGuardClosure", replace(s, concurrentGuardClosureRecorded=True)
    # ClosePost
    if (s.phase in TERMINAL and s.dispatchReadinessCaptured and s.receiptVerified
        and s.concurrentGuardClosureRecorded and s.postTraceClosed
        and s.postDutiesDischarged and s.challengeRouteAvailable):
        yield "ClosePost", replace(s, postClosed=True)
    # CloseAccountability
    if s.postClosed and s.challengeRouteAvailable and s.reviewResolved:
        yield "CloseAccountability", replace(s, accountabilityClosed=True)


def invariants(s: S):
    return {
        "TypeOK": (
            all(isinstance(v, bool) for v in (
                s.requestValid, s.preTraceClosed, s.preObligationsDischarged,
                s.nativePermit, s.nativeBindingExact, s.requiredApprovalsPresent,
                s.boundaryActive, s.nativeAuthorizationVerified,
                s.concurrentGuardsActive, s.revocationClear, s.postTraceClosed,
                s.postDutiesDischarged, s.challengeRouteAvailable, s.reviewResolved,
                s.nonceConsumed, s.dispatchReadinessCaptured,
                s.reservationReadinessCaptured, s.receiptVerified,
                s.concurrentGuardClosureRecorded,
                s.concurrentGuardClosureEvidenceVerified, s.postClosed,
                s.accountabilityClosed))
            and s.phase in PHASES and s.effectResult in EFFECTS),
        "NoReserveWithoutActionReady": s.phase == "IDLE" or (s.reservationReadinessCaptured and s.nonceConsumed),
        "PostClosureRequiresGuardClosure": not s.postClosed or s.concurrentGuardClosureRecorded,
        "NoDispatchWithoutCapturedReadiness": s.phase not in (TERMINAL | {"INTENT", "UNKNOWN"}) or s.dispatchReadinessCaptured,
        "NoEffectWithoutDispatchIntent": s.phase not in (TERMINAL | {"UNKNOWN"}) or (s.dispatchReadinessCaptured and s.nonceConsumed),
        "NoFalseTerminalReceipt": s.phase not in TERMINAL or s.receiptVerified,
        "UnknownHasNoVerifiedReceipt": s.phase != "UNKNOWN" or not s.receiptVerified,
        "PostClosureSoundness": (not s.postClosed or (s.phase in TERMINAL and s.dispatchReadinessCaptured
            and s.receiptVerified and s.concurrentGuardClosureRecorded and s.postTraceClosed
            and s.postDutiesDischarged and s.challengeRouteAvailable)),
        "AccountabilityClosureSoundness": (not s.accountabilityClosed or
            (s.postClosed and s.challengeRouteAvailable and s.reviewResolved)),
        "NonceIsNotReused": not s.nonceConsumed or s.phase != "IDLE",
    }


def main() -> int:
    cfg = CONFIG.read_text(encoding="utf-8")
    model = MODEL.read_text(encoding="utf-8")
    expected = re.findall(r"^INVARIANT\s+(\w+)\s*$", cfg, re.M)
    defined = set(re.findall(r"^(\w+)\s*==", model, re.M))
    missing = [name for name in expected if name not in defined]
    if missing:
        print("FAIL: invariant names missing from TLA+ source:", ", ".join(missing))
        return 2
    next_block = re.search(r"^Next ==\n(?P<body>.*?)(?=^Spec ==)", model, re.M | re.S)
    if not next_block:
        print("FAIL: could not locate TLA+ Next operator")
        return 2
    tla_actions = set(re.findall(r"^\s*\\/\s+(\w+)\s*$", next_block.group("body"), re.M))
    mirrored_actions = {
        "Reserve", "Dispatch", "CancelAfterReadinessLoss", "Revoke",
        "TargetCommit", "TargetReject", "LoseReceipt", "ConcurrentGuardLost",
        "ReconcileCommit", "ReconcileReject", "RecordConcurrentGuardClosure",
        "ClosePost", "CloseAccountability",
    }
    if tla_actions != mirrored_actions:
        print("FAIL: transition mirror differs from TLA+ Next actions")
        print("TLA-only:", sorted(tla_actions - mirrored_actions))
        print("Mirror-only:", sorted(mirrored_actions - tla_actions))
        return 2
    queue = deque()
    seen = set()
    for state in initial_states():
        if state not in seen:
            seen.add(state)
            queue.append(state)
    transitions = 0
    checked = 0
    while queue:
        state = queue.popleft()
        checked += 1
        bad = [name for name, ok in invariants(state).items() if not ok]
        if bad:
            print("FAIL: invariant violation", bad, "state=", state)
            return 1
        for _action, nxt in successors(state):
            transitions += 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    print("PASS: independent exhaustive finite-state exploration")
    print(f"Initial valuations: {2**14:,}")
    print(f"Reachable states checked: {checked:,}")
    print(f"Transitions explored: {transitions:,}")
    print(f"Safety invariants checked: {len(expected)} ({', '.join(expected)})")
    print(f"Transition operators cross-checked against TLA+ Next: {len(tla_actions)}")
    print("LIMIT: this checker is a Python mirror, not SANY/TLC and not a TLA+ grammar or refinement proof.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
