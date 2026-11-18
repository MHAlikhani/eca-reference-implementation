from copy import deepcopy
from datetime import datetime, timezone

import pytest

from eca_reference.contract import validate_contract
from eca_reference.errors import SchemaValidationError, SemanticValidationError
from eca_reference.schema import schema_document, validate_schema_definition
from tests.factories import NOW, make_contract


def test_schema_is_valid_draft_2020_12():
    validate_schema_definition()
    assert schema_document()["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_example_contract_is_structurally_and_semantically_valid():
    result = validate_contract(make_contract(), now=NOW)
    assert result["valid"] is True
    assert result["request_state"] == "CURRENT"
    assert result["action_validity_state"] == "CURRENT"
    assert result["relation_count"] == 12


def test_unknown_relation_type_fails_schema_validation():
    contract = make_contract()
    contract["relations"][0]["type"] = "supports"
    with pytest.raises(SchemaValidationError):
        validate_contract(contract, now=NOW)


def test_wrong_relation_direction_fails_semantic_validation():
    contract = make_contract()
    relation = contract["relations"][0]
    relation["source"], relation["target"] = relation["target"], relation["source"]
    with pytest.raises(SemanticValidationError, match="requires action->mission"):
        validate_contract(contract, now=NOW)


def test_missing_relation_endpoint_fails_semantic_validation():
    contract = make_contract()
    contract["relations"][0]["target"] = "node:does-not-exist"
    with pytest.raises(SemanticValidationError, match="unknown node"):
        validate_contract(contract, now=NOW)


def test_duplicate_node_ids_fail():
    contract = make_contract()
    contract["nodes"].append(deepcopy(contract["nodes"][0]))
    with pytest.raises(SemanticValidationError, match="duplicate"):
        validate_contract(contract, now=NOW)


def test_duplicate_relation_ids_fail():
    contract = make_contract()
    contract["relations"].append(deepcopy(contract["relations"][0]))
    with pytest.raises(SemanticValidationError, match="duplicate"):
        validate_contract(contract, now=NOW)


def test_request_digest_mismatch_fails():
    contract = make_contract()
    contract["action"]["request"]["target"] = "junction:substituted"
    contract["action"]["target"] = "junction:substituted"
    with pytest.raises(SemanticValidationError, match="digest mismatch"):
        validate_contract(contract, now=NOW)


def test_action_projection_mismatch_fails():
    contract = make_contract()
    contract["action"]["target"] = "junction:substituted"
    with pytest.raises(SemanticValidationError, match="must equal"):
        validate_contract(contract, now=NOW)


def test_empty_inverted_request_validity_fails():
    contract = make_contract()
    contract["action"]["request"]["expires_at"] = contract["action"]["request"]["created_at"]
    # Digest mismatch is detected before temporal validation if not recomputed.
    from eca_reference.canonical import request_digest
    contract["action"]["request_digest"] = request_digest(contract["action"]["request"])
    with pytest.raises(SemanticValidationError, match="expires_at must be later"):
        validate_contract(contract, now=NOW)


def test_expired_request_is_valid_data_but_not_current():
    contract = make_contract()
    result = validate_contract(contract, now=datetime(2026, 11, 19, tzinfo=timezone.utc))
    assert result["valid"] is True
    assert result["request_state"] == "EXPIRED"


def test_concurrent_obligation_requires_runtime_guard_in_schema():
    contract = make_contract()
    contract["obligations"].append({
        "id": "obligation:concurrent:1",
        "phase": "CONCURRENT",
        "owner_ref": "role:runtime",
        "status": "REGISTERED",
        "due_at": "2026-11-18T14:00:00Z",
    })
    with pytest.raises(SchemaValidationError, match="runtime_guard_ref"):
        validate_contract(contract, now=NOW)


def test_duplicate_obligation_ids_fail_semantic_validation():
    contract = make_contract()
    contract["obligations"].append(deepcopy(contract["obligations"][0]))
    with pytest.raises(SemanticValidationError, match=r"obligations\[\]\.id must not contain duplicate"):
        validate_contract(contract, now=NOW)


def test_discharged_obligation_requires_evidence_reference():
    contract = make_contract()
    contract["obligations"][0].pop("discharge_evidence_ref")
    with pytest.raises(SemanticValidationError, match="DISCHARGED but has no discharge_evidence_ref"):
        validate_contract(contract, now=NOW)


def test_obligation_due_timestamp_must_be_timezone_aware():
    contract = make_contract()
    contract["obligations"][0]["due_at"] = "2026-11-18T14:00:00"
    with pytest.raises(SchemaValidationError, match="is not a 'date-time'"):
        validate_contract(contract, now=NOW)
