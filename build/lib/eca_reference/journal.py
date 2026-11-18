"""Single-host SQLite journal for reservations and action outcomes.

This module persists evaluator reports and external-verifier assessments. It
is a persistence component, not an authorization oracle: callers must obtain
real assessments from their owning trust domains before submitting them.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ReadinessError, ReplayError, StateTransitionError

_ALLOWED_STATES = {"RESERVED", "DISPATCH_INTENT", "COMMITTED", "REJECTED", "UNKNOWN", "RECONCILED", "CANCELLED"}
_TERMINAL = {"COMMITTED", "REJECTED"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _validate_readiness(assessment: dict[str, Any] | None, request_digest: str, label: str) -> None:
    if not isinstance(assessment, dict) or assessment.get("action_ready") is not True:
        raise ReadinessError(f"{label} requires an affirmative ACTION_READY assessment")
    if assessment.get("request_digest") != request_digest:
        raise ReadinessError(f"{label} readiness assessment is not bound to the request digest")
    if assessment.get("failures") != []:
        raise ReadinessError(f"{label} readiness assessment contains failures")
    pre = assessment.get("pre_trace_closure")
    if not isinstance(pre, dict) or pre.get("trace_closed") is not True:
        raise ReadinessError(f"{label} requires TRACE_CLOSED_PRE")
    if not assessment.get("evaluated_at"):
        raise ReadinessError(f"{label} readiness assessment has no evaluation timestamp")


def _require_verified_assessment(assessment: dict[str, Any] | None, label: str) -> None:
    if not isinstance(assessment, dict) or assessment.get("verification_status") != "VERIFIED":
        raise ValueError(f"{label} requires a VERIFIED assessment")
    for field in ("verification_ref", "verifier_ref", "verification_method", "trust_profile_ref"):
        if not assessment.get(field):
            raise ValueError(f"{label} requires {field}")


class ExecutionJournal:
    """Durable local state transitions and nonce uniqueness on one SQLite DB."""

    def __init__(self, database: str | Path):
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.database, timeout=15.0, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        return con

    def _initialize(self) -> None:
        con = self._connect()
        try:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    nonce TEXT NOT NULL UNIQUE,
                    authorization_ref TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('RESERVED','DISPATCH_INTENT','COMMITTED','REJECTED','UNKNOWN','RECONCILED','CANCELLED')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    receipt_json TEXT,
                    terminal_outcome TEXT,
                    readiness_json TEXT,
                    dispatch_readiness_json TEXT,
                    receipt_verification_json TEXT
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reservation_id TEXT NOT NULL REFERENCES reservations(reservation_id),
                    event_type TEXT NOT NULL,
                    event_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
            """)
            # Minimal forward-only migration for databases created by an early
            # 2.0.0 development snapshot. It does not rewrite existing records.
            columns = {row[1] for row in con.execute("PRAGMA table_info(reservations)").fetchall()}
            for column in ("readiness_json", "dispatch_readiness_json", "receipt_verification_json"):
                if column not in columns:
                    con.execute(f"ALTER TABLE reservations ADD COLUMN {column} TEXT")
        finally:
            con.close()

    def reserve(
        self, *, request_digest: str, nonce: str, authorization_ref: str,
        action: str, target: str, readiness_assessment: dict[str, Any],
    ) -> dict[str, Any]:
        _validate_readiness(readiness_assessment, request_digest, "reservation")
        if not all([request_digest, nonce, authorization_ref, action, target]):
            raise ValueError("reservation fields must be non-empty")
        now = _now_iso()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            existing = con.execute("SELECT * FROM reservations WHERE nonce=?", (nonce,)).fetchone()
            if existing:
                if existing["request_digest"] == request_digest and existing["authorization_ref"] == authorization_ref:
                    con.execute("COMMIT")
                    return dict(existing)
                raise ReplayError("nonce has already been reserved for a different request or authorization")
            reservation_id = str(uuid.uuid4())
            con.execute(
                """INSERT INTO reservations
                   (reservation_id,request_digest,nonce,authorization_ref,action,target,state,created_at,updated_at,
                    receipt_json,terminal_outcome,readiness_json,dispatch_readiness_json,receipt_verification_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (reservation_id, request_digest, nonce, authorization_ref, action, target, "RESERVED", now, now,
                 None, None, _json(readiness_assessment), None, None),
            )
            con.execute(
                "INSERT INTO events(reservation_id,event_type,event_at,payload_json) VALUES(?,?,?,?)",
                (reservation_id, "RESERVED", now, _json({"request_digest": request_digest, "readiness_assessment": readiness_assessment})),
            )
            con.execute("COMMIT")
            return self.get(reservation_id)
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def _transition(
        self, reservation_id: str, expected: set[str], new_state: str,
        event_type: str, payload: dict[str, Any] | None = None,
        *, dispatch_readiness: dict[str, Any] | None = None,
        receipt: dict[str, Any] | None = None,
        receipt_verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if new_state not in _ALLOWED_STATES:
            raise ValueError(f"unsupported state {new_state}")
        now = _now_iso()
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT state FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            if row is None:
                raise StateTransitionError(f"unknown reservation {reservation_id}")
            if row["state"] not in expected:
                raise StateTransitionError(f"cannot transition {row['state']} to {new_state}")
            con.execute(
                """UPDATE reservations SET state=?, updated_at=?,
                   receipt_json=COALESCE(?,receipt_json),
                   terminal_outcome=COALESCE(?,terminal_outcome),
                   dispatch_readiness_json=COALESCE(?,dispatch_readiness_json),
                   receipt_verification_json=COALESCE(?,receipt_verification_json)
                   WHERE reservation_id=?""",
                (new_state, now, _json(receipt) if receipt is not None else None,
                 (payload or {}).get("terminal_outcome"),
                 _json(dispatch_readiness) if dispatch_readiness is not None else None,
                 _json(receipt_verification) if receipt_verification is not None else None,
                 reservation_id),
            )
            event_payload = dict(payload or {})
            if dispatch_readiness is not None:
                event_payload["dispatch_readiness_assessment"] = dispatch_readiness
            if receipt_verification is not None:
                event_payload["receipt_verification"] = receipt_verification
            con.execute(
                "INSERT INTO events(reservation_id,event_type,event_at,payload_json) VALUES(?,?,?,?)",
                (reservation_id, event_type, now, _json(event_payload)),
            )
            con.execute("COMMIT")
            return self.get(reservation_id)
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def persist_dispatch_intent(self, reservation_id: str, readiness_assessment: dict[str, Any]) -> dict[str, Any]:
        reservation = self.get(reservation_id)
        _validate_readiness(readiness_assessment, reservation["request_digest"], "dispatch intent")
        return self._transition(
            reservation_id, {"RESERVED"}, "DISPATCH_INTENT", "DISPATCH_INTENT",
            {"request_digest": reservation["request_digest"]}, dispatch_readiness=readiness_assessment,
        )

    def cancel_reserved(self, reservation_id: str, reason: str) -> dict[str, Any]:
        if not reason:
            raise ValueError("cancellation reason must be non-empty")
        return self._transition(reservation_id, {"RESERVED"}, "CANCELLED", "CANCELLED", {"reason": reason})

    def record_outcome(
        self, reservation_id: str, outcome: str, receipt: dict[str, Any] | None = None,
        receipt_verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if outcome not in {"COMMITTED", "REJECTED", "UNKNOWN"}:
            raise ValueError("outcome must be COMMITTED, REJECTED, or UNKNOWN")
        if outcome in _TERMINAL:
            if not receipt:
                raise ValueError("terminal COMMITTED/REJECTED outcomes require a verified receipt")
            _require_verified_assessment(receipt_verification, "terminal outcome")
            reservation = self.get(reservation_id)
            expected = {"request_digest": reservation["request_digest"], "nonce": reservation["nonce"], "target": reservation["target"], "action": reservation["action"], "outcome": outcome}
            if any(receipt.get(field) != value for field, value in expected.items()):
                raise ValueError("terminal receipt is not bound to the reserved request, nonce, action, target and outcome")
        elif receipt is not None or receipt_verification is not None:
            raise ValueError("UNKNOWN must not carry a terminal receipt or receipt-verification assessment")
        return self._transition(
            reservation_id, {"DISPATCH_INTENT"}, outcome, f"OUTCOME_{outcome}",
            {"receipt": receipt, "terminal_outcome": outcome}, receipt=receipt,
            receipt_verification=receipt_verification,
        )

    def reconcile_unknown(
        self, reservation_id: str, *, outcome: str, verified_receipt: dict[str, Any],
        receipt_verification: dict[str, Any],
    ) -> dict[str, Any]:
        if outcome not in _TERMINAL:
            raise ValueError("reconciliation outcome must resolve to COMMITTED or REJECTED")
        if not verified_receipt:
            raise ValueError("reconciliation requires a target receipt")
        _require_verified_assessment(receipt_verification, "reconciliation")
        reservation = self.get(reservation_id)
        expected = {"request_digest": reservation["request_digest"], "nonce": reservation["nonce"], "target": reservation["target"], "action": reservation["action"], "outcome": outcome}
        if any(verified_receipt.get(field) != value for field, value in expected.items()):
            raise ValueError("reconciliation receipt is not bound to the reserved request, nonce, action, target and outcome")
        return self._transition(
            reservation_id, {"UNKNOWN"}, "RECONCILED", "RECONCILED",
            {"receipt": verified_receipt, "terminal_outcome": outcome},
            receipt=verified_receipt, receipt_verification=receipt_verification,
        )

    def get(self, reservation_id: str) -> dict[str, Any]:
        con = self._connect()
        try:
            row = con.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            if row is None:
                raise StateTransitionError(f"unknown reservation {reservation_id}")
            return dict(row)
        finally:
            con.close()

    def events(self, reservation_id: str) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            rows = con.execute("SELECT * FROM events WHERE reservation_id=? ORDER BY event_id", (reservation_id,)).fetchall()
            return [dict(row) for row in rows]
        finally:
            con.close()
