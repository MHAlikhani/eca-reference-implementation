from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest

from eca_reference.errors import ReadinessError, ReplayError, StateTransitionError
from eca_reference.journal import ExecutionJournal
from eca_reference.receipts import verify_target_receipt
from eca_reference.runtime import LocalReferenceRuntime
from eca_reference.target import SQLiteTargetSimulator
from tests.factories import make_contract, make_native_authorization, make_enforcement_assessment

SECRET = b"receipt-key-for-tests-only"


def readiness_assessment(digest: str, action_ready: bool = True):
    return {
        "action_ready": action_ready,
        "request_digest": digest,
        "failures": [] if action_ready else ["not ready"],
        "pre_trace_closure": {"trace_closed": True},
        "evaluated_at": "2026-11-18T12:00:00Z",
    }


def dispatch_action(runtime, reservation, contract, **kwargs):
    return runtime.dispatch(
        reservation["reservation_id"],
        idempotency_key=kwargs.pop("idempotency_key"),
        contract=contract,
        native_authorization=kwargs.pop("native_authorization", make_native_authorization(contract)),
        enforcement_assessment=kwargs.pop("enforcement_assessment", make_enforcement_assessment(contract)),
        now=kwargs.pop("now", datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)),
        **kwargs,
    )


def setup_runtime(tmp_path: Path):
    journal = ExecutionJournal(tmp_path / "authority.sqlite3")
    target = SQLiteTargetSimulator(tmp_path / "target.sqlite3", SECRET)
    runtime = LocalReferenceRuntime(journal, target, SECRET)
    contract = make_contract()
    reservation = runtime.reserve(
        contract=contract,
        native_authorization=make_native_authorization(contract),
        enforcement_assessment=make_enforcement_assessment(contract),
        now=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
    )
    return runtime, journal, target, contract, reservation


def test_reservation_requires_action_ready(tmp_path):
    journal = ExecutionJournal(tmp_path / "journal.sqlite3")
    with pytest.raises(ReadinessError):
        journal.reserve(request_digest="d", nonce="n", authorization_ref="a", action="x", target="t", readiness_assessment=readiness_assessment("d", False))


def test_reservation_is_idempotent_for_same_nonce_and_same_request(tmp_path):
    journal = ExecutionJournal(tmp_path / "journal.sqlite3")
    args = dict(request_digest="sha256:abc", nonce="nonce-123456789012", authorization_ref="auth:1", action="x", target="t", readiness_assessment=readiness_assessment("sha256:abc", True))
    first = journal.reserve(**args)
    second = journal.reserve(**args)
    assert first["reservation_id"] == second["reservation_id"]


def test_nonce_replay_for_different_request_is_rejected(tmp_path):
    journal = ExecutionJournal(tmp_path / "journal.sqlite3")
    journal.reserve(request_digest="sha256:one", nonce="nonce-123456789012", authorization_ref="auth:1", action="x", target="t", readiness_assessment=readiness_assessment("sha256:one", True))
    with pytest.raises(ReplayError):
        journal.reserve(request_digest="sha256:two", nonce="nonce-123456789012", authorization_ref="auth:1", action="x", target="t", readiness_assessment=readiness_assessment("sha256:two", True))


def test_dispatch_persists_intent_before_terminal_outcome(tmp_path):
    runtime, journal, target, contract, reservation = setup_runtime(tmp_path)
    result = dispatch_action(runtime, reservation, contract, idempotency_key="idem-42")
    assert result["state"] == "COMMITTED"
    events = [event["event_type"] for event in journal.events(reservation["reservation_id"])]
    assert events == ["RESERVED", "DISPATCH_INTENT", "OUTCOME_COMMITTED"]


def test_lost_receipt_produces_unknown_and_reconciliation_resolves_it(tmp_path):
    runtime, journal, target, contract, reservation = setup_runtime(tmp_path)
    reservation_id = reservation["reservation_id"]
    unknown = dispatch_action(runtime, reservation, contract, idempotency_key="idem-lost", lose_receipt_after_target=True)
    assert unknown["state"] == "UNKNOWN"
    reconciled = runtime.reconcile(reservation_id, idempotency_key="idem-lost", contract=contract)
    assert reconciled["state"] == "RECONCILED"
    assert reconciled["terminal_outcome"] == "COMMITTED"


def test_unknown_state_cannot_be_dispatched_again(tmp_path):
    runtime, journal, target, contract, reservation = setup_runtime(tmp_path)
    reservation_id = reservation["reservation_id"]
    dispatch_action(runtime, reservation, contract, idempotency_key="idem-unknown", lose_receipt_after_target=True)
    with pytest.raises(ValueError, match="RESERVED"):
        dispatch_action(runtime, reservation, contract, idempotency_key="idem-unknown")


def test_receipt_binding_mismatch_fails_verification(tmp_path):
    runtime, journal, target, contract, reservation = setup_runtime(tmp_path)
    receipt = target.apply(idempotency_key="key", request_digest=contract["action"]["request_digest"], nonce="nonce-other", target=contract["action"]["target"], action=contract["action"]["action_class"])
    assert verify_target_receipt(receipt, SECRET, expected_request_digest=contract["action"]["request_digest"], expected_nonce=contract["action"]["request"]["nonce"], expected_target=contract["action"]["target"], expected_action=contract["action"]["action_class"]) is False


def test_target_idempotency_returns_same_receipt_for_same_binding(tmp_path):
    target = SQLiteTargetSimulator(tmp_path / "target.sqlite3", SECRET)
    args = dict(idempotency_key="once", request_digest="sha256:digest", nonce="nonce-abc", target="t", action="a")
    first = target.apply(**args)
    second = target.apply(**args)
    assert first == second


def test_target_rejects_idempotency_key_reuse_for_different_binding(tmp_path):
    target = SQLiteTargetSimulator(tmp_path / "target.sqlite3", SECRET)
    target.apply(idempotency_key="once", request_digest="sha256:first", nonce="n", target="t", action="a")
    with pytest.raises(ValueError, match="different material action"):
        target.apply(idempotency_key="once", request_digest="sha256:second", nonce="n", target="t", action="a")


def test_reconciliation_requires_unknown_state(tmp_path):
    runtime, journal, target, contract, reservation = setup_runtime(tmp_path)
    with pytest.raises(ValueError, match="UNKNOWN"):
        runtime.reconcile(reservation["reservation_id"], idempotency_key="missing", contract=contract)


def test_illegal_journal_transition_is_rejected(tmp_path):
    journal = ExecutionJournal(tmp_path / "journal.sqlite3")
    reservation = journal.reserve(request_digest="sha256:d", nonce="nonce-123456789", authorization_ref="auth", action="a", target="t", readiness_assessment=readiness_assessment("sha256:d"))
    with pytest.raises(StateTransitionError):
        journal.record_outcome(
            reservation["reservation_id"], "COMMITTED",
            {"request_digest": "sha256:d", "nonce": "nonce-123456789", "target": "t", "action": "a", "outcome": "COMMITTED"},
            {"verification_status": "VERIFIED", "verification_ref": "v:1", "verifier_ref": "verifier:1", "verification_method": "test", "trust_profile_ref": "trust:test"},
        )


def test_same_nonce_concurrent_reservations_create_one_record(tmp_path):
    journal = ExecutionJournal(tmp_path / "journal.sqlite3")
    args = dict(request_digest="sha256:concurrent", nonce="nonce-concurrent-123456", authorization_ref="auth:one", action="a", target="t", readiness_assessment=readiness_assessment("sha256:concurrent"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: journal.reserve(**args), range(16)))
    assert len({result["reservation_id"] for result in results}) == 1


def test_terminal_journal_outcome_requires_receipt(tmp_path):
    journal = ExecutionJournal(tmp_path / "journal.sqlite3")
    reservation = journal.reserve(request_digest="sha256:d", nonce="nonce-receipt-required", authorization_ref="auth", action="a", target="t", readiness_assessment=readiness_assessment("sha256:d"))
    journal.persist_dispatch_intent(reservation["reservation_id"], readiness_assessment("sha256:d"))
    with pytest.raises(ValueError, match="require a verified receipt"):
        journal.record_outcome(reservation["reservation_id"], "COMMITTED")


def test_target_idempotency_key_cannot_be_reused_with_different_nonce(tmp_path):
    target = SQLiteTargetSimulator(tmp_path / "target.sqlite3", SECRET)
    target.apply(idempotency_key="nonce-key", request_digest="sha256:d", nonce="nonce-one", target="t", action="a")
    with pytest.raises(ValueError, match="different material action or nonce"):
        target.apply(idempotency_key="nonce-key", request_digest="sha256:d", nonce="nonce-two", target="t", action="a")


def test_target_exception_after_dispatch_intent_is_recorded_as_unknown(tmp_path):
    runtime, journal, target, contract, reservation = setup_runtime(tmp_path)
    class FailingTarget:
        def apply(self, **kwargs):
            raise TimeoutError("simulated uncertain transport")
    runtime.target = FailingTarget()
    result = dispatch_action(runtime, reservation, contract, idempotency_key="timeout-key")
    assert result["state"] == "UNKNOWN"


def test_runtime_rechecks_revocation_before_dispatch_and_cancels(tmp_path):
    runtime, journal, target, contract, reservation = setup_runtime(tmp_path)
    auth = make_native_authorization(contract)
    auth["revocation_state"] = "REVOKED"
    with pytest.raises(ReadinessError, match="dispatch cancelled"):
        dispatch_action(runtime, reservation, contract, idempotency_key="revoked", native_authorization=auth)
    assert journal.get(reservation["reservation_id"])["state"] == "CANCELLED"
