from copy import deepcopy

import pytest

from eca_reference.delegation import sign_delegation, verify_delegation_chain
from eca_reference.errors import SemanticValidationError
from tests.factories import NOW

ROOT_KEY = b"root-secret-for-test-only"
OPS_KEY = b"ops-secret-for-test-only"


def base_chain():
    root = {
        "delegation_id": "delegation:root",
        "issuer_ref": "issuer:city-authority",
        "subject_ref": "principal:operations-unit",
        "parent_ref": None,
        "actions": ["traffic.signal.adjust", "traffic.signal.inspect"],
        "resources": ["junction:04", "junction:05"],
        "risk_ceiling": "high",
        "not_before": "2026-11-18T09:00:00Z",
        "expires_at": "2026-11-18T18:00:00Z",
    }
    root = sign_delegation(root, ROOT_KEY)
    child = {
        "delegation_id": "delegation:child",
        "issuer_ref": "principal:operations-unit",
        "subject_ref": "principal:controller-04",
        "parent_ref": "delegation:root",
        "actions": ["traffic.signal.adjust"],
        "resources": ["junction:04"],
        "risk_ceiling": "medium",
        "not_before": "2026-11-18T10:00:00Z",
        "expires_at": "2026-11-18T14:00:00Z",
    }
    child = sign_delegation(child, OPS_KEY)
    return [root, child]


def test_valid_chain_enforces_attenuation_and_expiry_containment():
    result = verify_delegation_chain(base_chain(), {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY}, now=NOW)
    assert result["valid"] is True
    assert result["chain_length"] == 2
    assert result["effective_actions"] == ["traffic.signal.adjust"]
    assert result["risk_ceiling"] == "medium"


def test_parent_revocation_blocks_child():
    with pytest.raises(SemanticValidationError, match="durably revoked"):
        verify_delegation_chain(base_chain(), {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY}, {"delegation:root"}, now=NOW)


def test_child_action_scope_expansion_is_rejected_even_if_signed():
    chain = base_chain()
    child = deepcopy(chain[1])
    child["actions"].append("financial.transfer")
    chain[1] = sign_delegation({k: v for k, v in child.items() if k != "signature"}, OPS_KEY)
    with pytest.raises(SemanticValidationError, match="expands its parent's action scope"):
        verify_delegation_chain(chain, {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY}, now=NOW)


def test_child_resource_scope_expansion_is_rejected():
    chain = base_chain()
    child = deepcopy(chain[1])
    child["resources"].append("junction:06")
    chain[1] = sign_delegation({k: v for k, v in child.items() if k != "signature"}, OPS_KEY)
    with pytest.raises(SemanticValidationError, match="expands its parent's resource scope"):
        verify_delegation_chain(chain, {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY}, now=NOW)


def test_child_risk_ceiling_expansion_is_rejected():
    chain = base_chain()
    child = deepcopy(chain[1])
    child["risk_ceiling"] = "critical"
    chain[1] = sign_delegation({k: v for k, v in child.items() if k != "signature"}, OPS_KEY)
    with pytest.raises(SemanticValidationError, match="risk ceiling"):
        verify_delegation_chain(chain, {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY}, now=NOW)


def test_parent_issuer_continuity_is_required():
    chain = base_chain()
    child = deepcopy(chain[1])
    child["issuer_ref"] = "principal:other"
    chain[1] = sign_delegation({k: v for k, v in child.items() if k != "signature"}, b"other-key")
    with pytest.raises(SemanticValidationError, match="issuer is not the parent delegate"):
        verify_delegation_chain(chain, {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY, "principal:other": b"other-key"}, now=NOW)


def test_missing_trust_key_fails_closed():
    with pytest.raises(SemanticValidationError, match="no trusted verification key"):
        verify_delegation_chain(base_chain(), {}, now=NOW)


def test_signature_tampering_is_detected():
    chain = base_chain()
    chain[1]["subject_ref"] = "principal:attacker"
    with pytest.raises(SemanticValidationError, match="signature is invalid"):
        verify_delegation_chain(chain, {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY}, now=NOW)


def test_chain_order_and_parent_reference_are_enforced():
    chain = base_chain()
    chain[1]["parent_ref"] = "delegation:other"
    chain[1] = sign_delegation({k: v for k, v in chain[1].items() if k != "signature"}, OPS_KEY)
    with pytest.raises(SemanticValidationError, match="immediately preceding parent"):
        verify_delegation_chain(chain, {"issuer:city-authority": ROOT_KEY, "principal:operations-unit": OPS_KEY}, now=NOW)
