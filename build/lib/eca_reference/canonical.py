"""Deterministic ECA request encoding.

This is a deliberately narrow canonicalization profile, not RFC 8785/JCS.
It rejects floating-point values and normalizes strings to NFC so that this
profile can be implemented consistently across languages without relying on
runtime-specific float formatting.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any

from .constants import CANONICALIZATION_PROFILE
from .errors import CanonicalizationError

_MIN_INT = -(2**63)
_MAX_INT = 2**63 - 1


def _normalise(value: Any, path: str = "$", *, max_depth: int = 64) -> Any:
    if max_depth < 0:
        raise CanonicalizationError(f"maximum nesting depth exceeded at {path}")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value < _MIN_INT or value > _MAX_INT:
            raise CanonicalizationError(f"integer outside signed 64-bit range at {path}")
        return value
    if isinstance(value, float):
        raise CanonicalizationError(f"binary floating-point values are prohibited at {path}; use an integer or canonical decimal string")
    if isinstance(value, str):
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
            raise CanonicalizationError(f"unpaired surrogate code point at {path}")
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalise(v, f"{path}[{i}]", max_depth=max_depth - 1) for i, v in enumerate(value)]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        original_keys: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"object key is not a string at {path}")
            normalized_key = _normalise(key, f"{path}.<key>", max_depth=max_depth - 1)
            if normalized_key in result:
                raise CanonicalizationError(
                    f"object keys collide after NFC normalization at {path}: {original_keys[normalized_key]!r} and {key!r}"
                )
            original_keys[normalized_key] = key
            result[normalized_key] = _normalise(item, f"{path}.{normalized_key}", max_depth=max_depth - 1)
        return result
    raise CanonicalizationError(f"unsupported value type {type(value).__name__} at {path}")


def canonical_request_bytes(request: dict[str, Any]) -> bytes:
    """Return UTF-8 bytes for the ECA canonical request profile v1."""
    if not isinstance(request, dict):
        raise CanonicalizationError("request must be a JSON object")
    normalized = _normalise(request)
    if "canonicalization_profile" in normalized and normalized["canonicalization_profile"] != CANONICALIZATION_PROFILE:
        raise CanonicalizationError("request declares an unsupported canonicalization profile")
    normalized["canonicalization_profile"] = CANONICALIZATION_PROFILE
    try:
        text = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError(str(exc)) from exc
    return text.encode("utf-8", errors="strict")


def request_digest(request: dict[str, Any]) -> str:
    """Return a lowercase SHA-256 digest using the `sha256:<hex>` notation."""
    return "sha256:" + hashlib.sha256(canonical_request_bytes(request)).hexdigest()


def strict_json_loads(data: str | bytes) -> Any:
    """Parse JSON while rejecting duplicate keys and non-finite numbers."""
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            normalized = unicodedata.normalize("NFC", key)
            if normalized in out:
                raise CanonicalizationError(f"duplicate JSON object key after NFC normalization: {key!r}")
            out[normalized] = value
        return out

    def reject_constant(value: str) -> None:
        raise CanonicalizationError(f"non-finite JSON number is prohibited: {value}")

    try:
        return json.loads(data, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise CanonicalizationError(f"invalid JSON: {exc}") from exc
