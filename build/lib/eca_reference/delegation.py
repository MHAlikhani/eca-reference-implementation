"""Delegation-chain attenuation for the local reference profile.

HMAC is used only to make examples/tests self-contained. It is not a
recommended multi-party key-distribution architecture.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Mapping

from .canonical import canonical_request_bytes
from .constants import RISK_RANK
from .errors import SemanticValidationError
from .semantics import parse_time


def delegation_signing_bytes(delegation: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in delegation.items() if key != "signature"}
    return b"ECA-DELEGATION-HMAC-V1\x00" + canonical_request_bytes(unsigned)


def sign_delegation(delegation: dict[str, Any], secret: bytes) -> dict[str, Any]:
    if not secret:
        raise ValueError("HMAC secret must not be empty")
    signed = dict(delegation)
    signed["signature"] = hmac.new(secret, delegation_signing_bytes(signed), hashlib.sha256).hexdigest()
    return signed


def verify_delegation_chain(
    chain_root_to_leaf: list[dict[str, Any]],
    issuer_keys: Mapping[str, bytes],
    revoked_ids: set[str] | None = None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify signatures, ancestry, expiry, issuer continuity and attenuation.

    The chain must be ordered root-to-leaf. `issuer_keys` is a local test trust
    map. Production deployments must substitute their native credential
    verifier and governance/key-rotation controls.
    """
    if not chain_root_to_leaf:
        raise SemanticValidationError("delegation chain must not be empty")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise SemanticValidationError("verification time must be timezone-aware")
    current = current.astimezone(timezone.utc)
    revoked = revoked_ids or set()
    previous: dict[str, Any] | None = None
    for index, delegation in enumerate(chain_root_to_leaf):
        required = {"delegation_id", "issuer_ref", "subject_ref", "parent_ref", "actions", "resources", "risk_ceiling", "not_before", "expires_at", "signature"}
        missing = required - set(delegation)
        if missing:
            raise SemanticValidationError(f"delegation[{index}] missing fields: {sorted(missing)}")
        delegation_id = delegation["delegation_id"]
        for field in ("delegation_id", "issuer_ref", "subject_ref"):
            if not isinstance(delegation.get(field), str) or not delegation[field]:
                raise SemanticValidationError(f"delegation[{index}].{field} must be a non-empty string")
        if not isinstance(delegation["actions"], list) or not delegation["actions"] or any(not isinstance(x, str) or not x for x in delegation["actions"]):
            raise SemanticValidationError(f"delegation[{index}].actions must be a non-empty list of strings")
        if not isinstance(delegation["resources"], list) or not delegation["resources"] or any(not isinstance(x, str) or not x for x in delegation["resources"]):
            raise SemanticValidationError(f"delegation[{index}].resources must be a non-empty list of strings")
        if not isinstance(delegation["signature"], str):
            raise SemanticValidationError(f"delegation[{index}].signature must be a string")
        if delegation_id in revoked:
            raise SemanticValidationError(f"delegation {delegation_id} is durably revoked")
        key = issuer_keys.get(delegation["issuer_ref"])
        if key is None or not isinstance(key, bytes) or not key:
            raise SemanticValidationError(f"no trusted verification key (or key is empty/invalid) for issuer {delegation['issuer_ref']}")
        expected = hmac.new(key, delegation_signing_bytes(delegation), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, delegation["signature"]):
            raise SemanticValidationError(f"delegation {delegation_id} signature is invalid")
        start = parse_time(delegation["not_before"], f"delegation[{index}].not_before")
        end = parse_time(delegation["expires_at"], f"delegation[{index}].expires_at")
        if end <= start or not (start <= current < end):
            raise SemanticValidationError(f"delegation {delegation_id} is not currently valid")
        if delegation["risk_ceiling"] not in RISK_RANK:
            raise SemanticValidationError(f"delegation {delegation_id} has an unknown risk ceiling")
        if not delegation["actions"] or not delegation["resources"]:
            raise SemanticValidationError(f"delegation {delegation_id} must grant a non-empty action/resource scope")
        if previous is None:
            if delegation["parent_ref"] is not None:
                raise SemanticValidationError("root delegation must have parent_ref=null")
        else:
            if delegation["parent_ref"] != previous["delegation_id"]:
                raise SemanticValidationError(f"delegation {delegation_id} does not reference the immediately preceding parent")
            if delegation["issuer_ref"] != previous["subject_ref"]:
                raise SemanticValidationError(f"delegation {delegation_id} issuer is not the parent delegate")
            if not set(delegation["actions"]).issubset(set(previous["actions"])):
                raise SemanticValidationError(f"delegation {delegation_id} expands its parent's action scope")
            if not set(delegation["resources"]).issubset(set(previous["resources"])):
                raise SemanticValidationError(f"delegation {delegation_id} expands its parent's resource scope")
            if RISK_RANK[delegation["risk_ceiling"]] > RISK_RANK[previous["risk_ceiling"]]:
                raise SemanticValidationError(f"delegation {delegation_id} expands its parent's risk ceiling")
            parent_start = parse_time(previous["not_before"], "parent.not_before")
            parent_end = parse_time(previous["expires_at"], "parent.expires_at")
            if start < parent_start or end > parent_end:
                raise SemanticValidationError(f"delegation {delegation_id} validity interval is not contained in its parent")
        previous = delegation
    return {
        "valid": True,
        "chain_length": len(chain_root_to_leaf),
        "root_delegation_id": chain_root_to_leaf[0]["delegation_id"],
        "leaf_delegation_id": chain_root_to_leaf[-1]["delegation_id"],
        "subject_ref": chain_root_to_leaf[-1]["subject_ref"],
        "effective_actions": sorted(set(chain_root_to_leaf[-1]["actions"])),
        "effective_resources": sorted(set(chain_root_to_leaf[-1]["resources"])),
        "risk_ceiling": chain_root_to_leaf[-1]["risk_ceiling"],
        "verified_at": current.isoformat().replace("+00:00", "Z"),
        "cryptographic_profile": "local-HMAC-demo-only",
    }
