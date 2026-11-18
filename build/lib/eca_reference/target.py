"""Idempotent SQLite target simulator; not a production actuator adapter."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .receipts import sign_target_receipt


class SQLiteTargetSimulator:
    def __init__(self, database: str | Path, receipt_secret: bytes):
        self.database = str(database)
        self.receipt_secret = receipt_secret
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database) as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA synchronous=FULL")
            con.execute("CREATE TABLE IF NOT EXISTS target_effects (idempotency_key TEXT PRIMARY KEY, request_digest TEXT NOT NULL, target TEXT NOT NULL, action TEXT NOT NULL, outcome TEXT NOT NULL, receipt_json TEXT NOT NULL)")

    def apply(self, *, idempotency_key: str, request_digest: str, nonce: str, target: str, action: str, outcome: str = "COMMITTED") -> dict[str, Any]:
        if any(not isinstance(value, str) or not value for value in (idempotency_key, request_digest, nonce, target, action)):
            raise ValueError("idempotency key, request digest, nonce, target and action must be non-empty strings")
        if outcome not in {"COMMITTED", "REJECTED"}:
            raise ValueError("target simulator outcome must be COMMITTED or REJECTED")
        con = sqlite3.connect(self.database, timeout=15.0, isolation_level=None)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM target_effects WHERE idempotency_key=?", (idempotency_key,)).fetchone()
            if row:
                previous_receipt = json.loads(row[5])
                if row[1] != request_digest or row[2] != target or row[3] != action or previous_receipt.get("nonce") != nonce:
                    raise ValueError("idempotency key was reused for a different material action or nonce")
                con.execute("COMMIT")
                return previous_receipt
            receipt = sign_target_receipt({
                "idempotency_key": idempotency_key,
                "request_digest": request_digest,
                "nonce": nonce,
                "target": target,
                "action": action,
                "outcome": outcome,
                "target_event_ref": f"target-event:{idempotency_key}",
            }, self.receipt_secret)
            con.execute("INSERT INTO target_effects VALUES(?,?,?,?,?,?)", (idempotency_key, request_digest, target, action, outcome, json.dumps(receipt, sort_keys=True)))
            con.execute("COMMIT")
            return receipt
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    def lookup(self, idempotency_key: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.database) as con:
            row = con.execute("SELECT receipt_json FROM target_effects WHERE idempotency_key=?", (idempotency_key,)).fetchone()
            return json.loads(row[0]) if row else None
