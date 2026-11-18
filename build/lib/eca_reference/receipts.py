"""Target receipt helpers for deterministic tests and local demonstrations."""
from __future__ import annotations

import hashlib
import hmac
from typing import Any

from .canonical import canonical_request_bytes
from .errors import CanonicalizationError


def sign_target_receipt(receipt: dict[str, Any], secret: bytes) -> dict[str, Any]:
    if not secret:
        raise ValueError("receipt secret must not be empty")
    signed = dict(receipt)
    signed.pop("mac", None)
    mac = hmac.new(secret, b"ECA-TARGET-RECEIPT-V1\x00" + canonical_request_bytes(signed), hashlib.sha256).hexdigest()
    signed["mac"] = mac
    return signed


def verify_target_receipt(receipt: dict[str, Any], secret: bytes, *, expected_request_digest: str, expected_nonce: str, expected_target: str, expected_action: str) -> bool:
    if not secret or not isinstance(receipt, dict):
        return False
    supplied = receipt.get("mac")
    if not isinstance(supplied, str):
        return False
    unsigned = {key: value for key, value in receipt.items() if key != "mac"}
    try:
        expected = hmac.new(secret, b"ECA-TARGET-RECEIPT-V1\x00" + canonical_request_bytes(unsigned), hashlib.sha256).hexdigest()
    except (CanonicalizationError, TypeError, ValueError):
        return False
    return (
        hmac.compare_digest(expected, supplied)
        and receipt.get("request_digest") == expected_request_digest
        and receipt.get("nonce") == expected_nonce
        and receipt.get("target") == expected_target
        and receipt.get("action") == expected_action
        and receipt.get("outcome") in {"COMMITTED", "REJECTED"}
        and bool(receipt.get("target_event_ref"))
    )
