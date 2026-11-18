from copy import deepcopy
from datetime import datetime, timezone

from eca_reference.canonical import request_digest
from eca_reference.contract import (
    evaluate_action_readiness,
    evaluate_trace_closure,
    evaluate_post_action_closure,
    evaluate_accountability_closure,
)
from tests.factories import NOW, make_contract, make_native_authorization, make_enforcement_assessment, make_dispatch_assessment, make_outcome, make_review_assessment


def test_pre_trace_closure_and_rrc_are_reported_separately():
    contract = make_contract()
    result = evaluate_trace_closure(contract, "PRE", now=NOW)
    assert result["trace_closed"] is True
    assert result["verified_required_count"] == 8
    assert result["denominator"] == 8
    assert result["rrc"] == 1.0


def test_low_rrc_is_not_used_as_a_substitute_for_critical_gate():
    contract = make_contract()
    for rel in contract["relations"]:
        if rel["type"] == "supported_by_evidence":
            rel["status"] = "STALE"
    result = evaluate_trace_closure(contract, "PRE", now=NOW)
    assert result["rrc"] == 7 / 8
    assert result["trace_closed"] is False


def test_noncritical_not_applicable_requires_valid_exception_and_is_not_counted_verified():
    contract = make_contract()
    rel = next(r for r in contract["relations"] if r["type"] == "built_as_release")
    rel["status"] = "NOT_APPLICABLE"
    rel["not_applicable_exception"] = {
        "reason": "the profile maps this action to an externally managed release record",
        "approved_by": "role:profile-owner",
        "approved_at": "2026-11-18T11:40:00Z",
        "valid_until": "2026-11-18T13:00:00Z",
    }
    result = evaluate_trace_closure(contract, "PRE", now=NOW)
    assert result["trace_closed"] is True
    assert result["approved_not_applicable_count"] == 1
    assert result["verified_required_count"] == 7
    assert result["rrc"] == 7 / 8


def test_critical_not_applicable_does_not_close_phase():
    contract = make_contract()
    rel = next(r for r in contract["relations"] if r["type"] == "supported_by_evidence")
    rel["status"] = "NOT_APPLICABLE"
    rel["not_applicable_exception"] = {
        "reason": "asserted exception",
        "approved_by": "role:profile-owner",
        "approved_at": "2026-11-18T11:40:00Z",
        "valid_until": "2026-11-18T13:00:00Z",
    }
    assert evaluate_trace_closure(contract, "PRE", now=NOW)["trace_closed"] is False


def test_disputed_parallel_edge_blocks_otherwise_verified_relation():
    contract = make_contract()
    disputed = deepcopy(next(r for r in contract["relations"] if r["type"] == "supported_by_evidence"))
    disputed["id"] = "relation:parallel-dispute"
    disputed["status"] = "DISPUTED"
    contract["relations"].append(disputed)
    result = evaluate_trace_closure(contract, "PRE", now=NOW)
    assert result["trace_closed"] is False


def test_stale_evidence_is_detected_from_freshness_rule_even_if_status_says_verified():
    contract = make_contract()
    rel = next(r for r in contract["relations"] if r["type"] == "supported_by_evidence")
    rel["observed_at"] = "2026-11-18T10:00:00Z"
    rel["validity"]["checked_at"] = "2026-11-18T11:59:00Z"
    result = evaluate_trace_closure(contract, "PRE", now=NOW)
    assert result["trace_closed"] is False
    assert "exceeds freshness limit" in result["relations"]["supported_by_evidence"]["instances"][0]["reason"]


def test_action_ready_requires_native_permit_and_effect_boundary():
    contract = make_contract()
    result = evaluate_action_readiness(contract, make_native_authorization(contract), make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is True
    assert result["failures"] == []


def test_action_ready_rejects_native_deny():
    contract = make_contract()
    auth = make_native_authorization(contract)
    auth["verdict"] = "DENY"
    result = evaluate_action_readiness(contract, auth, make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("not PERMIT" in f for f in result["failures"])


def test_action_ready_rejects_request_substitution_in_native_decision():
    contract = make_contract()
    auth = make_native_authorization(contract)
    auth["target"] = "junction:other"
    result = evaluate_action_readiness(contract, auth, make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("target does not match" in f for f in result["failures"])


def test_action_ready_rejects_missing_approval_role():
    contract = make_contract()
    auth = make_native_authorization(contract)
    auth["verified_approval_roles"] = ["traffic-operator"]
    result = evaluate_action_readiness(contract, auth, make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("approvals are missing" in f for f in result["failures"])


def test_action_ready_rejects_revoked_or_unknown_authority():
    contract = make_contract()
    auth = make_native_authorization(contract)
    auth["revocation_state"] = "UNKNOWN"
    result = evaluate_action_readiness(contract, auth, make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("revoked or" in f for f in result["failures"])


def test_action_ready_rejects_uncontrolled_bypass():
    contract = make_contract()
    enforcement = make_enforcement_assessment(contract)
    enforcement["bypass_controlled"] = False
    result = evaluate_action_readiness(contract, make_native_authorization(contract), enforcement, now=NOW)
    assert result["action_ready"] is False
    assert any("bypass paths" in f for f in result["failures"])


def test_action_ready_rejects_pending_pre_obligation():
    contract = make_contract()
    contract["obligations"][0]["status"] = "PENDING"
    result = evaluate_action_readiness(contract, make_native_authorization(contract), make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("PRE obligation" in f for f in result["failures"])


def test_action_ready_rejects_expired_request():
    contract = make_contract()
    req = contract["action"]["request"]
    req["expires_at"] = "2026-11-18T11:00:00Z"
    contract["action"]["request_digest"] = request_digest(req)
    auth = make_native_authorization(contract)
    auth["request_digest"] = contract["action"]["request_digest"]
    auth["valid_until"] = "2026-11-18T13:00:00Z"
    result = evaluate_action_readiness(contract, auth, make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("request is EXPIRED" in f for f in result["failures"])


def test_post_action_closure_rejects_unknown_outcome():
    contract = make_contract()
    outcome = make_outcome(contract, state="UNKNOWN", receipt_verified=False)
    result = evaluate_post_action_closure(contract, outcome, make_dispatch_assessment(contract), now=NOW)
    assert result["post_action_closed"] is False


def test_post_action_closure_requires_verified_target_receipt():
    contract = make_contract()
    outcome = make_outcome(contract, state="COMMITTED", receipt_verified=False)
    result = evaluate_post_action_closure(contract, outcome, make_dispatch_assessment(contract), now=NOW)
    assert result["post_action_closed"] is False
    assert any("verified target-linked receipt" in f for f in result["failures"])


def test_post_action_closure_passes_with_terminal_verified_outcome():
    contract = make_contract()
    result = evaluate_post_action_closure(contract, make_outcome(contract), make_dispatch_assessment(contract), now=NOW)
    assert result["post_action_closed"] is True


def test_post_action_closure_does_not_recheck_expired_native_permission_after_dispatch():
    contract = make_contract()
    # The current native authorization is deliberately not an input here.
    # A verified historical dispatch assessment is the evidence used.
    dispatch = make_dispatch_assessment(contract)
    dispatch["dispatched_at"] = "2026-11-18T11:59:59Z"
    result = evaluate_post_action_closure(contract, make_outcome(contract), dispatch, now=NOW)
    assert result["post_action_closed"] is True


def test_post_action_closure_requires_verified_dispatch_assessment():
    contract = make_contract()
    dispatch = make_dispatch_assessment(contract)
    dispatch["verification_status"] = "PRESENT_UNVERIFIED"
    result = evaluate_post_action_closure(contract, make_outcome(contract), dispatch, now=NOW)
    assert result["post_action_closed"] is False
    assert any("not VERIFIED" in failure for failure in result["failures"])


def test_post_action_closure_rejects_dispatch_request_substitution():
    contract = make_contract()
    dispatch = make_dispatch_assessment(contract)
    dispatch["request_digest"] = "sha256:" + "0" * 64
    result = evaluate_post_action_closure(contract, make_outcome(contract), dispatch, now=NOW)
    assert result["post_action_closed"] is False
    assert any("not bound to this request digest" in failure for failure in result["failures"])


def test_post_action_closure_rejects_future_dispatch_time():
    contract = make_contract()
    dispatch = make_dispatch_assessment(contract)
    dispatch["dispatched_at"] = "2026-11-18T12:05:00Z"
    result = evaluate_post_action_closure(contract, make_outcome(contract), dispatch, now=NOW)
    assert result["post_action_closed"] is False
    assert any("in the future" in failure for failure in result["failures"])


def test_post_action_closure_rejects_due_undischarged_post_obligation():
    contract = make_contract()
    contract["obligations"][1]["due_at"] = "2026-11-18T11:00:00Z"
    result = evaluate_post_action_closure(contract, make_outcome(contract), make_dispatch_assessment(contract), now=NOW)
    assert result["post_action_closed"] is False
    assert any("is due but not discharged" in f for f in result["failures"])

def test_accountability_closure_requires_challenge_route_test_and_dispositions():
    contract = make_contract()
    outcome = make_outcome(contract)
    post = evaluate_post_action_closure(contract, outcome, make_dispatch_assessment(contract), now=NOW)
    review = make_review_assessment(contract, [{"case_id": "case-1", "owner_ref": "role:reviewer", "disposition": "RESOLVED"}])
    result = evaluate_accountability_closure(contract, post, review, now=NOW)
    assert result["accountability_closed"] is True


def test_accountability_closure_rejects_unresolved_case():
    contract = make_contract()
    outcome = make_outcome(contract)
    post = evaluate_post_action_closure(contract, outcome, make_dispatch_assessment(contract), now=NOW)
    review = make_review_assessment(contract, [{"case_id": "case-1", "owner_ref": "role:reviewer", "disposition": "OPEN"}])
    assert evaluate_accountability_closure(contract, post, review, now=NOW)["accountability_closed"] is False


def test_action_ready_rejects_native_reference_not_mapped_by_etc():
    contract = make_contract()
    auth = make_native_authorization(contract)
    auth["native_ref"] = "native-auth:other"
    result = evaluate_action_readiness(contract, auth, make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("does not match the ETC authorized_by_native_decision" in failure for failure in result["failures"])


def test_action_ready_rejects_enforcement_reference_not_mapped_by_etc():
    contract = make_contract()
    enforcement = make_enforcement_assessment(contract)
    enforcement["enforcement_point_ref"] = "pep:other"
    result = evaluate_action_readiness(contract, make_native_authorization(contract), enforcement, now=NOW)
    assert result["action_ready"] is False
    assert any("does not match the ETC enforced_at_boundary" in failure for failure in result["failures"])


def test_accountability_closure_rejects_post_report_transplant():
    contract = make_contract()
    outcome = make_outcome(contract)
    post = evaluate_post_action_closure(contract, outcome, make_dispatch_assessment(contract), now=NOW)
    post["request_digest"] = "sha256:" + "0" * 64
    result = evaluate_accountability_closure(contract, post, make_review_assessment(contract), now=NOW)
    assert result["accountability_closed"] is False
    assert any("post-action report is not bound" in failure for failure in result["failures"])


def test_accountability_closure_requires_verified_action_bound_review():
    contract = make_contract()
    outcome = make_outcome(contract)
    post = evaluate_post_action_closure(contract, outcome, make_dispatch_assessment(contract), now=NOW)
    review = make_review_assessment(contract)
    review["verification_status"] = "PRESENT_UNVERIFIED"
    result = evaluate_accountability_closure(contract, post, review, now=NOW)
    assert result["accountability_closed"] is False
    assert any("review assessment is not VERIFIED" in failure for failure in result["failures"])


def test_not_applicable_exception_with_inverted_interval_is_rejected():
    contract = make_contract()
    rel = next(r for r in contract["relations"] if r["type"] == "built_as_release")
    rel["status"] = "NOT_APPLICABLE"
    rel["not_applicable_exception"] = {
        "reason": "demonstration exception",
        "approved_by": "role:profile-owner",
        "approved_at": "2026-11-18T13:00:00Z",
        "valid_until": "2026-11-18T12:30:00Z",
    }
    from eca_reference.errors import SemanticValidationError
    import pytest
    with pytest.raises(SemanticValidationError, match="expiry must be later"):
        evaluate_trace_closure(contract, "PRE", now=NOW)


def test_concurrent_obligation_requires_registered_active_runtime_guard():
    contract = make_contract()
    contract["obligations"].append({
        "id": "obligation:concurrent:pedestrian-minimum",
        "phase": "CONCURRENT",
        "owner_ref": "role:runtime-safety",
        "status": "REGISTERED",
        "due_at": "2026-11-18T14:00:00Z",
        "runtime_guard_ref": "guard:pedestrian-minimum",
    })
    enforcement = make_enforcement_assessment(contract)
    enforcement["active_guard_refs"] = ["guard:pedestrian-minimum"]
    result = evaluate_action_readiness(contract, make_native_authorization(contract), enforcement, now=NOW)
    assert result["action_ready"] is True


def test_concurrent_obligation_without_active_guard_blocks_action_ready():
    contract = make_contract()
    contract["obligations"].append({
        "id": "obligation:concurrent:pedestrian-minimum",
        "phase": "CONCURRENT",
        "owner_ref": "role:runtime-safety",
        "status": "REGISTERED",
        "due_at": "2026-11-18T14:00:00Z",
        "runtime_guard_ref": "guard:pedestrian-minimum",
    })
    result = evaluate_action_readiness(contract, make_native_authorization(contract), make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert any("not bound to an active runtime guard" in failure for failure in result["failures"])


def test_post_closure_requires_concurrent_guard_discharge_evidence():
    contract = make_contract()
    contract["obligations"].append({
        "id": "obligation:concurrent:pedestrian-minimum",
        "phase": "CONCURRENT",
        "owner_ref": "role:runtime-safety",
        "status": "REGISTERED",
        "due_at": "2026-11-18T14:00:00Z",
        "runtime_guard_ref": "guard:pedestrian-minimum",
    })
    result = evaluate_post_action_closure(contract, make_outcome(contract), make_dispatch_assessment(contract), now=NOW)
    assert result["post_action_closed"] is False
    assert any("was not closed with discharge evidence" in failure for failure in result["failures"])


def test_accountability_closure_checks_due_accountability_obligations():
    contract = make_contract()
    contract["obligations"][2]["due_at"] = "2026-11-18T11:00:00Z"
    outcome = make_outcome(contract)
    post = evaluate_post_action_closure(contract, outcome, make_dispatch_assessment(contract), now=NOW)
    result = evaluate_accountability_closure(contract, post, make_review_assessment(contract), now=NOW)
    assert result["accountability_closed"] is False
    assert any("ACCOUNTABILITY obligation" in failure for failure in result["failures"])


def test_malformed_external_assessment_types_fail_closed():
    contract = make_contract()
    result = evaluate_action_readiness(contract, None, make_enforcement_assessment(contract), now=NOW)
    assert result["action_ready"] is False
    assert "native authorization assessment must be an object" in result["failures"]


def test_non_string_active_guard_reference_fails_closed():
    contract = make_contract()
    contract["obligations"].append({
        "id": "obligation:concurrent:bad-guard",
        "phase": "CONCURRENT",
        "owner_ref": "role:runtime-safety",
        "status": "REGISTERED",
        "due_at": "2026-11-18T14:00:00Z",
        "runtime_guard_ref": "guard:pedestrian-minimum",
    })
    enforcement = make_enforcement_assessment(contract)
    enforcement["active_guard_refs"] = [{"unexpected": "object"}]
    result = evaluate_action_readiness(contract, make_native_authorization(contract), enforcement, now=NOW)
    assert result["action_ready"] is False
    assert any("list of non-empty strings" in failure for failure in result["failures"])


def test_stale_native_authorization_assessment_blocks_action_ready():
    native = make_native_authorization(make_contract())
    native["verified_at"] = "2026-11-18T11:57:00Z"
    result = evaluate_action_readiness(make_contract(), native, make_enforcement_assessment(), now=NOW)
    assert result["action_ready"] is False
    assert any("native authorization assessment age" in failure for failure in result["failures"])


def test_future_enforcement_assessment_blocks_action_ready():
    enforcement = make_enforcement_assessment(make_contract())
    enforcement["assessed_at"] = "2026-11-18T12:00:01Z"
    result = evaluate_action_readiness(make_contract(), make_native_authorization(), enforcement, now=NOW)
    assert result["action_ready"] is False
    assert any("effect-boundary assessment age" in failure for failure in result["failures"])


def test_missing_assessment_timestamp_blocks_action_ready():
    native = make_native_authorization(make_contract())
    native.pop("verified_at")
    result = evaluate_action_readiness(make_contract(), native, make_enforcement_assessment(), now=NOW)
    assert result["action_ready"] is False
    assert "native authorization verified_at timestamp is missing or invalid" in result["failures"]


def test_malformed_dispatch_assessment_fails_closed_without_exception():
    result = evaluate_post_action_closure(make_contract(), make_outcome(make_contract()), None, now=NOW)
    assert result["post_action_closed"] is False
    assert "dispatch assessment must be an object" in result["failures"]


def test_non_object_outcome_fails_closed_without_exception():
    result = evaluate_post_action_closure(make_contract(), None, make_dispatch_assessment(make_contract()), now=NOW)
    assert result["post_action_closed"] is False
    assert "outcome must be an object" in result["failures"]


def test_unhashable_review_case_identifier_fails_closed():
    contract = make_contract()
    post = evaluate_post_action_closure(contract, make_outcome(contract), make_dispatch_assessment(contract), now=NOW)
    review = make_review_assessment(contract, open_cases=[{"case_id": ["bad"], "owner_ref": "owner:1", "disposition": "RESOLVED"}])
    result = evaluate_accountability_closure(contract, post, review, now=NOW)
    assert result["accountability_closed"] is False
    assert any("non-empty string case_id" in failure for failure in result["failures"])
