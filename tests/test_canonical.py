import pytest

from eca_reference.canonical import canonical_request_bytes, request_digest, strict_json_loads
from eca_reference.errors import CanonicalizationError


def test_object_key_order_does_not_change_digest():
    a = {"a": 1, "b": {"x": 2, "y": 3}}
    b = {"b": {"y": 3, "x": 2}, "a": 1}
    assert request_digest(a) == request_digest(b)


def test_unicode_is_normalized_to_nfc():
    assert canonical_request_bytes({"label": "cafe\u0301"}) == canonical_request_bytes({"label": "caf\u00e9"})


def test_float_is_rejected_instead_of_runtime_serialized():
    with pytest.raises(CanonicalizationError, match="floating-point"):
        canonical_request_bytes({"amount": 1.25})


def test_non_finite_json_constant_is_rejected():
    with pytest.raises(CanonicalizationError, match="non-finite"):
        strict_json_loads('{"x": NaN}')


def test_duplicate_json_keys_are_rejected():
    with pytest.raises(CanonicalizationError, match="duplicate"):
        strict_json_loads('{"x": 1, "x": 2}')


def test_keys_colliding_after_unicode_normalization_are_rejected():
    with pytest.raises(CanonicalizationError, match="collide"):
        canonical_request_bytes({"caf\u00e9": 1, "cafe\u0301": 2})


def test_large_integer_is_rejected():
    with pytest.raises(CanonicalizationError, match="64-bit"):
        canonical_request_bytes({"n": 2**80})


def test_nested_depth_limit_is_enforced():
    value = 1
    for _ in range(70):
        value = [value]
    with pytest.raises(CanonicalizationError, match="nesting depth"):
        canonical_request_bytes({"nested": value})


def test_digest_uses_sha256_prefix():
    assert request_digest({"a": 1}).startswith("sha256:")
    assert len(request_digest({"a": 1})) == 71
