"""Synchronous single-host lifecycle adapter for the local reference release."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from .contract import evaluate_action_readiness
from .errors import ReadinessError
from .journal import ExecutionJournal
from .receipts import verify_target_receipt
from .target import SQLiteTargetSimulator


class LocalReferenceRuntime:
    """Reserve and dispatch only after local evaluation of native assessments.

    It re-evaluates immediately before persisting dispatch intent. This narrows
    but does not eliminate distributed check-to-use races between independently
    operated authorization services, enforcement points, and target systems.
    """

    def __init__(self, journal: ExecutionJournal, target: SQLiteTargetSimulator, receipt_secret: bytes):
        self.journal = journal
        self.target = target
        self.receipt_secret = receipt_secret

    @staticmethod
    def _readiness_snapshot(
        contract: dict[str, Any], readiness: dict[str, Any],
        native_authorization: dict[str, Any], enforcement_assessment: dict[str, Any],
    ) -> dict[str, Any]:
        """Persist identifiers and decisions, not raw bearer tokens or secrets."""
        return {
            **readiness,
            "action_id": contract["action"]["action_id"],
            "action": contract["action"]["action_class"],
            "target": contract["action"]["target"],
            "native_authorization_ref": native_authorization.get("native_ref"),
            "native_verifier_ref": native_authorization.get("verifier_ref"),
            "native_verdict": native_authorization.get("verdict"),
            "native_valid_until": native_authorization.get("valid_until"),
            "native_revocation_state": native_authorization.get("revocation_state"),
            "native_replay_state": native_authorization.get("replay_state"),
            "native_verified_at": native_authorization.get("verified_at"),
            "enforcement_assessed_at": enforcement_assessment.get("assessed_at"),
            "enforcement_point_ref": enforcement_assessment.get("enforcement_point_ref"),
            "enforcement_adapter_version": enforcement_assessment.get("adapter_version"),
            "enforcement_bypass_controlled": enforcement_assessment.get("bypass_controlled"),
            "active_guard_refs": list(enforcement_assessment.get("active_guard_refs", [])) if isinstance(enforcement_assessment.get("active_guard_refs", []), list) else [],
        }

    def reserve(
        self, *, contract: dict[str, Any], native_authorization: dict[str, Any],
        enforcement_assessment: dict[str, Any], now: datetime | None = None,
    ) -> dict[str, Any]:
        readiness = evaluate_action_readiness(contract, native_authorization, enforcement_assessment, now=now)
        snapshot = self._readiness_snapshot(contract, readiness, native_authorization, enforcement_assessment)
        if readiness["action_ready"] is not True:
            raise ReadinessError(f"reservation refused: ACTION_READY is false: {readiness['failures']}")
        request = contract["action"]["request"]
        return self.journal.reserve(
            request_digest=contract["action"]["request_digest"],
            nonce=request["nonce"],
            authorization_ref=native_authorization["native_ref"],
            action=request["action"],
            target=request["target"],
            readiness_assessment=snapshot,
        )

    def dispatch(
        self, reservation_id: str, *, idempotency_key: str,
        contract: dict[str, Any], native_authorization: dict[str, Any],
        enforcement_assessment: dict[str, Any],
        lose_receipt_after_target: bool = False, target_outcome: str = "COMMITTED",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        reservation = self.journal.get(reservation_id)
        if reservation["state"] != "RESERVED":
            raise ValueError("dispatch requires a RESERVED action")
        request = contract["action"]["request"]
        expected = {
            "request_digest": contract["action"]["request_digest"],
            "nonce": request["nonce"],
            "action": request["action"],
            "target": request["target"],
        }
        if any(reservation[field] != value for field, value in expected.items()):
            raise ValueError("dispatch contract does not match the reserved material request")
        if reservation["authorization_ref"] != native_authorization.get("native_ref"):
            raise ValueError("dispatch native authorization reference differs from the reservation")

        # Re-evaluate at the dispatch boundary, not only when reserving.
        readiness = evaluate_action_readiness(contract, native_authorization, enforcement_assessment, now=now)
        snapshot = self._readiness_snapshot(contract, readiness, native_authorization, enforcement_assessment)
        if readiness["action_ready"] is not True:
            self.journal.cancel_reserved(reservation_id, f"dispatch-time ACTION_READY failed: {readiness['failures']}")
            raise ReadinessError(f"dispatch cancelled: ACTION_READY is false: {readiness['failures']}")
        self.journal.persist_dispatch_intent(reservation_id, snapshot)

        try:
            receipt = self.target.apply(
                idempotency_key=idempotency_key,
                request_digest=contract["action"]["request_digest"],
                nonce=request["nonce"], target=request["target"], action=request["action"],
                outcome=target_outcome,
            )
        except Exception:
            # Once dispatch intent is durable and the target call is attempted,
            # an exception cannot safely be interpreted as proof of no effect.
            return self.journal.record_outcome(reservation_id, "UNKNOWN")
        if lose_receipt_after_target:
            return self.journal.record_outcome(reservation_id, "UNKNOWN")
        verified = verify_target_receipt(
            receipt, self.receipt_secret,
            expected_request_digest=contract["action"]["request_digest"],
            expected_nonce=request["nonce"], expected_target=request["target"],
            expected_action=request["action"],
        )
        if not verified:
            return self.journal.record_outcome(reservation_id, "UNKNOWN")
        verification = self._receipt_verification(receipt)
        return self.journal.record_outcome(reservation_id, receipt["outcome"], receipt, verification)

    def reconcile(
        self, reservation_id: str, *, idempotency_key: str,
        contract: dict[str, Any],
    ) -> dict[str, Any]:
        reservation = self.journal.get(reservation_id)
        if reservation["state"] != "UNKNOWN":
            raise ValueError("reconciliation is permitted only for UNKNOWN outcomes")
        request = contract["action"]["request"]
        if (
            reservation["request_digest"] != contract["action"]["request_digest"]
            or reservation["nonce"] != request["nonce"]
            or reservation["action"] != request["action"]
            or reservation["target"] != request["target"]
        ):
            raise ValueError("reconciliation contract does not match the reserved action")
        receipt = self.target.lookup(idempotency_key)
        if receipt is None or not verify_target_receipt(
            receipt, self.receipt_secret,
            expected_request_digest=contract["action"]["request_digest"],
            expected_nonce=request["nonce"], expected_target=request["target"],
            expected_action=request["action"],
        ):
            raise ValueError("target evidence is not available or does not verify; state remains UNKNOWN")
        return self.journal.reconcile_unknown(
            reservation_id, outcome=receipt["outcome"], verified_receipt=receipt,
            receipt_verification=self._receipt_verification(receipt),
        )

    @staticmethod
    def _receipt_verification(receipt: dict[str, Any]) -> dict[str, Any]:
        return {
            "verification_status": "VERIFIED",
            "verification_ref": f"receipt-verification:{receipt.get('target_event_ref', 'unknown')}",
            "verifier_ref": "local-hmac-target-receipt-verifier",
            "verification_method": "HMAC-SHA256-ECA-TARGET-RECEIPT-V1",
            "trust_profile_ref": "local-test-hmac-profile",
            "limitations": ["shared HMAC test secret; not a production key-custody or signer-separation model"],
        }
