import json
from pathlib import Path

import pytest

from eca_reference.canonical import canonical_request_bytes, request_digest, strict_json_loads
from eca_reference.errors import CanonicalizationError

VECTORS = json.loads((Path(__file__).parents[1] / "vectors" / "canonicalization-v1.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("vector", VECTORS["positive_vectors"], ids=lambda vector: vector["id"])
def test_positive_canonicalization_interoperability_vectors(vector):
    request = strict_json_loads(vector["input_json"])
    assert canonical_request_bytes(request).decode("utf-8") == vector["expected_canonical_utf8"]
    assert request_digest(request) == vector["expected_request_digest"]


@pytest.mark.parametrize("vector", VECTORS["negative_vectors"], ids=lambda vector: vector["id"])
def test_negative_canonicalization_interoperability_vectors(vector):
    with pytest.raises(CanonicalizationError) as exc:
        request = strict_json_loads(vector["input_json"])
        canonical_request_bytes(request)
    assert vector["expected_error_contains"] in str(exc.value)
