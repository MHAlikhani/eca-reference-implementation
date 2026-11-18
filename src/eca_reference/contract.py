"""Public ETC evaluation API.

This module deliberately consumes native authorization/enforcement assessments
from their owning systems. It does not issue or verify native grants itself.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .canonical import request_digest
from .constants import TERMINAL_OUTCOMES
from .errors import ReadinessError, SemanticValidationError
from .schema import validate_contract_structure
from .semantics import (
    parse_time,
    phase_report,
    validate_contract_semantics,
    validate_outcome,
)


def _utc_now(now: datetime | None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise SemanticValidationError("evaluation time must be timezone-aware")
    return current.astimezone(timezone.utc)


def validate_contract(contract: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Run structural and local semantic checks; does not validate external trust roots."""
    current = _utc_now(now)
    validate_contract_structure(contract)
    validate_contract_semantics(contract)
    computed = request_digest(contract["action"]["request"])
    declared = contract["action"]["request_digest"]
    if computed != declared:
        raise SemanticValidationError(f"request digest mismatch: declared {declared}, computed {computed}")
    req = contract["action"]["request"]
    action_validity = contract["action"]["validity"]
    not_before = parse_time(action_validity["not_before"], "action.validity.not_before")
    expires = parse_time(action_validity["expires_at"], "action.validity.expires_at")
    if expires <= not_before:
        raise SemanticValidationError("action validity interval is empty or inverted")
    if parse_time(req["expires_at"], "request.expires_at") <= current:
        # Expiry is a time-sensitive semantic finding, not a malformed document.
        request_state = "EXPIRED"
    elif parse_time(req["created_at"], "request.created_at") > current:
        request_state = "NOT_YET_VALID"
    else:
        request_state = "CURRENT"
    if expires <= current:
        action_validity_state = "EXPIRED"
    elif not_before > current:
        action_validity_state = "NOT_YET_VALID"
    else:
        action_validity_state = "CURRENT"
    return {
        "valid": True,
        "profile_version": contract["profile_version"],
        "request_digest": computed,
        "request_state": request_state,
        "action_validity_state": action_validity_state,
        "node_count": len(contract["nodes"]),
        "relation_count": len(contract["relations"]),
        "checked_at": current.isoformat().replace("+00:00", "Z"),
    }


def evaluate_trace_closure(contract: dict[str, Any], phase: str, *, now: datetime | None = None) -> dict[str, Any]:
    current = _utc_now(now)
    validate_contract(contract, now=current)
    return phase_report(contract, phase, current)


def _native_authorization_errors(contract: dict[str, Any], assessment: dict[str, Any], now: datetime) -> list[str]:
    if not isinstance(assessment, dict):
        return ["native authorization assessment must be an object"]
    errors: list[str] = []
    request = contract["action"]["request"]
    digest = contract["action"]["request_digest"]
    if assessment.get("verdict") != "PERMIT": errors.append("native PDP verdict is not PERMIT")
    if assessment.get("verified_by_native_verifier") is not True: errors.append("native authorization was not affirmatively verified by its native verifier")
    if not assessment.get("native_ref"): errors.append("native authorization reference is missing")
    if not assessment.get("verifier_ref"): errors.append("native verifier reference is missing")
    if not assessment.get("verification_ref"): errors.append("native authorization verification reference is missing")
    if not assessment.get("verification_method"): errors.append("native authorization verification method is missing")
    if assessment.get("request_digest") != digest: errors.append("native authorization is not bound to this request digest")
    for field, expected in (("principal_ref", request["principal_ref"]), ("action", request["action"]), ("target", request["target"]), ("policy_ref", request["policy_ref"])):
        if assessment.get(field) != expected: errors.append(f"native authorization {field} does not match the request")
    try:
        start = parse_time(assessment["valid_from"], "native_authorization.valid_from")
        end = parse_time(assessment["valid_until"], "native_authorization.valid_until")
        if end <= start or not (start <= now < end): errors.append("native authorization is outside its validity interval")
    except (KeyError, SemanticValidationError):
        errors.append("native authorization validity interval is missing or invalid")
    if assessment.get("revocation_state") != "ACTIVE": errors.append("native authorization is revoked or its revocation state is unknown")
    if assessment.get("replay_state") not in {"AVAILABLE", "RESERVED_FOR_THIS_ACTION"}: errors.append("native authorization replay state is not available for this action")
    roles_required_raw = assessment.get("required_approval_roles", [])
    roles_verified_raw = assessment.get("verified_approval_roles", [])
    if (not isinstance(roles_required_raw, list) or not isinstance(roles_verified_raw, list)
            or any(not isinstance(role, str) or not role for role in roles_required_raw + roles_verified_raw)):
        errors.append("approval role lists must contain non-empty strings")
        roles_required, roles_verified = set(), set()
    else:
        roles_required, roles_verified = set(roles_required_raw), set(roles_verified_raw)
    if not roles_required.issubset(roles_verified):
        errors.append(f"required approvals are missing: {sorted(roles_required - roles_verified)}")
    if not assessment.get("trust_profile_ref"): errors.append("native authorization trust profile is missing")
    try:
        verified_at = parse_time(assessment["verified_at"], "native_authorization.verified_at")
        max_age = contract["risk_profile"]["native_authorization_max_age_seconds"]
        age = (now - verified_at).total_seconds()
        if age < 0 or age > max_age:
            errors.append(f"native authorization assessment age {age:.0f}s is outside the allowed 0..{max_age}s window")
    except (KeyError, SemanticValidationError):
        errors.append("native authorization verified_at timestamp is missing or invalid")
    node_map = {node["id"]: node for node in contract["nodes"]}
    mapped = [r for r in contract["relations"] if r["type"] == "authorized_by_native_decision"]
    expected_refs = {node_map[r["target"]]["native_ref"] for r in mapped}
    if not expected_refs or assessment.get("native_ref") not in expected_refs:
        errors.append("native authorization reference does not match the ETC authorized_by_native_decision relation")
    return errors


def _pre_obligation_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for obligation in contract["obligations"]:
        if obligation["phase"] == "PRE":
            if obligation["status"] != "DISCHARGED" or not obligation.get("discharge_evidence_ref"):
                errors.append(f"PRE obligation {obligation['id']} is not discharged with evidence")
    return errors


def _concurrent_obligation_errors(contract: dict[str, Any], enforcement_assessment: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(enforcement_assessment, dict):
        return ["effect-boundary assessment must be an object"]
    active_guards = enforcement_assessment.get("active_guard_refs", [])
    if (not isinstance(active_guards, list)
            or any(not isinstance(ref, str) or not ref for ref in active_guards)):
        errors.append("effect-boundary active_guard_refs must be a list of non-empty strings")
        active_guards = []
    if len(active_guards) != len(set(active_guards)):
        errors.append("effect-boundary active_guard_refs must not contain duplicates")
    active = set(active_guards)
    for obligation in contract["obligations"]:
        if obligation["phase"] == "CONCURRENT":
            guard_ref = obligation.get("runtime_guard_ref")
            if obligation["status"] != "REGISTERED":
                errors.append(f"CONCURRENT obligation {obligation['id']} must be REGISTERED while action is running")
            if not guard_ref:
                errors.append(f"CONCURRENT obligation {obligation['id']} has no runtime_guard_ref")
            elif guard_ref not in active:
                errors.append(f"CONCURRENT obligation {obligation['id']} is not bound to an active runtime guard")
    return errors


def _enforcement_errors(contract: dict[str, Any], assessment: dict[str, Any], now: datetime) -> list[str]:
    if not isinstance(assessment, dict):
        return ["effect-boundary assessment must be an object"]
    request = contract["action"]["request"]
    errors: list[str] = []
    if assessment.get("active") is not True: errors.append("effect boundary is not active")
    if assessment.get("verification_status") != "VERIFIED": errors.append("effect-boundary assessment is not VERIFIED by its declared verifier")
    for field in ("verification_ref", "verifier_ref", "verification_method", "trust_profile_ref"):
        if not assessment.get(field): errors.append(f"effect-boundary assessment {field} is missing")
    if assessment.get("request_digest") != contract["action"]["request_digest"]: errors.append("effect boundary is not pinned to the exact request digest")
    if assessment.get("target") != request["target"]: errors.append("effect boundary target does not match the request")
    if assessment.get("action") != request["action"]: errors.append("effect boundary action does not match the request")
    if assessment.get("policy_ref") != request["policy_ref"]: errors.append("effect boundary policy pin does not match the request")
    if not assessment.get("adapter_version"): errors.append("effect-boundary adapter version is not recorded")
    if assessment.get("bypass_controlled") is not True: errors.append("direct or alternate bypass paths are not declared controlled")
    if not assessment.get("enforcement_point_ref"): errors.append("enforcement point reference is missing")
    try:
        assessed_at = parse_time(assessment["assessed_at"], "enforcement_assessment.assessed_at")
        max_age = contract["risk_profile"]["enforcement_assessment_max_age_seconds"]
        age = (now - assessed_at).total_seconds()
        if age < 0 or age > max_age:
            errors.append(f"effect-boundary assessment age {age:.0f}s is outside the allowed 0..{max_age}s window")
    except (KeyError, SemanticValidationError):
        errors.append("effect-boundary assessed_at timestamp is missing or invalid")
    guards = assessment.get("active_guard_refs", [])
    if (not isinstance(guards, list)
            or any(not isinstance(ref, str) or not ref for ref in guards)):
        errors.append("effect-boundary active_guard_refs must be a list of non-empty strings")
    node_map = {node["id"]: node for node in contract["nodes"]}
    mapped = [r for r in contract["relations"] if r["type"] == "enforced_at_boundary"]
    expected_refs = {node_map[r["target"]]["native_ref"] for r in mapped}
    if not expected_refs or assessment.get("enforcement_point_ref") not in expected_refs:
        errors.append("enforcement point reference does not match the ETC enforced_at_boundary relation")
    return errors


def evaluate_action_readiness(
    contract: dict[str, Any],
    native_authorization: dict[str, Any],
    enforcement_assessment: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate ACTION_READY without issuing permission or invoking a target."""
    current = _utc_now(now)
    validate_contract(contract, now=current)
    pre = phase_report(contract, "PRE", current)
    state_report = validate_contract(contract, now=current)
    failures: list[str] = []
    if state_report["request_state"] != "CURRENT":
        failures.append(f"request is {state_report['request_state']}")
    if state_report["action_validity_state"] != "CURRENT":
        failures.append(f"action validity is {state_report['action_validity_state']}")
    if pre["trace_closed"] is not True:
        failures.append("TRACE_CLOSED_PRE is false")
    pre_obligation_failures = _pre_obligation_errors(contract)
    if pre_obligation_failures:
        failures.extend(pre_obligation_failures)
    failures.extend(_native_authorization_errors(contract, native_authorization, current))
    failures.extend(_enforcement_errors(contract, enforcement_assessment, current))
    failures.extend(_concurrent_obligation_errors(contract, enforcement_assessment))
    return {
        "action_ready": not failures,
        "request_digest": contract["action"]["request_digest"],
        "pre_trace_closure": pre,
        "failures": failures,
        "evaluated_at": current.isoformat().replace("+00:00", "Z"),
        "authority_source": "native authorization system; ETC is not the grant",
    }


def _dispatch_assessment_errors(contract: dict[str, Any], assessment: dict[str, Any], now: datetime) -> list[str]:
    """Check an externally verified, immutable dispatch-time readiness attestation.

    This function validates the assessment envelope and its bindings. It does
    not authenticate the verifier's signature or trust root; that verification
    must be performed by the native attestation verifier before this object is
    passed to the ETC evaluator.
    """
    if not isinstance(assessment, dict):
        return ["dispatch assessment must be an object"]
    request = contract["action"]["request"]
    digest = contract["action"]["request_digest"]
    failures: list[str] = []
    required_text = ("assessment_ref", "dispatch_ref", "verification_ref", "verifier_ref", "verification_method", "trust_profile_ref")
    for field in required_text:
        if not assessment.get(field):
            failures.append(f"dispatch assessment {field} is missing")
    if assessment.get("verification_status") != "VERIFIED":
        failures.append("dispatch readiness attestation is not VERIFIED by its declared verifier")
    if assessment.get("action_ready") is not True:
        failures.append("ACTION_READY was not established at dispatch")
    if assessment.get("request_digest") != digest:
        failures.append("dispatch assessment is not bound to this request digest")
    if assessment.get("action") != request["action"]:
        failures.append("dispatch assessment action does not match the request")
    if assessment.get("target") != request["target"]:
        failures.append("dispatch assessment target does not match the request")
    try:
        dispatched_at = parse_time(assessment["dispatched_at"], "dispatch_assessment.dispatched_at")
        created_at = parse_time(request["created_at"], "request.created_at")
        expires_at = parse_time(request["expires_at"], "request.expires_at")
        if not (created_at <= dispatched_at < expires_at):
            failures.append("dispatch timestamp is outside the request validity interval")
        if dispatched_at > now:
            failures.append("dispatch timestamp is in the future")
    except (KeyError, SemanticValidationError):
        failures.append("dispatch timestamp is missing or invalid")
    if "limitations" not in assessment or not isinstance(assessment.get("limitations"), list):
        failures.append("dispatch assessment limitations must be explicitly recorded as a list (empty is permitted)")
    return failures


def evaluate_post_action_closure(
    contract: dict[str, Any],
    outcome: dict[str, Any],
    dispatch_assessment: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate post-action closure using an externally verified dispatch record.

    It intentionally does not re-evaluate current authorization: expiry or
    revocation after a correctly recorded dispatch cannot rewrite history.
    """
    current = _utc_now(now)
    validate_contract(contract, now=current)
    failures = _dispatch_assessment_errors(contract, dispatch_assessment, current)
    failures.extend(validate_outcome(outcome, contract["action"]["request_digest"], contract["action"]["target"]))
    if not isinstance(dispatch_assessment, dict):
        dispatch_assessment = {}
    if not isinstance(outcome, dict):
        outcome = {}
    post = phase_report(contract, "POST", current)
    if not post["trace_closed"]:
        failures.append("TRACE_CLOSED_POST relation obligations are not satisfied")
    for obligation in contract["obligations"]:
        if obligation["phase"] == "POST":
            due = parse_time(obligation["due_at"], f"obligation.{obligation['id']}.due_at")
            if due <= current and (obligation["status"] != "DISCHARGED" or not obligation.get("discharge_evidence_ref")):
                failures.append(f"POST obligation {obligation['id']} is due but not discharged")
            elif obligation["status"] not in {"REGISTERED", "DISCHARGED"}:
                failures.append(f"POST obligation {obligation['id']} is neither registered nor discharged")
    for obligation in contract["obligations"]:
        if obligation["phase"] == "CONCURRENT":
            if obligation["status"] != "DISCHARGED" or not obligation.get("discharge_evidence_ref"):
                failures.append(f"CONCURRENT obligation {obligation['id']} was not closed with discharge evidence")
    if not contract["closure_policy"].get("challenge_route_ref"):
        failures.append("usable challenge/recovery route is not recorded")
    if outcome.get("state") not in TERMINAL_OUTCOMES:
        failures.append("UNKNOWN or non-terminal outcome prevents post-action closure")
    return {
        "post_action_closed": not failures,
        "outcome_state": outcome.get("state"),
        "request_digest": contract["action"]["request_digest"],
        "action_id": contract["action"]["action_id"],
        "dispatch_assessment_ref": dispatch_assessment.get("assessment_ref"),
        "post_trace_closure": post,
        "failures": failures,
        "dispatch_readiness_source": "externally verified immutable dispatch assessment",
        "current_authorization_rechecked": False,
        "note": "current authorization expiry or revocation does not retroactively change a verified historical dispatch assessment",
    }


def evaluate_accountability_closure(
    contract: dict[str, Any],
    post_action_report: dict[str, Any],
    review_assessment: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = _utc_now(now)
    validate_contract(contract, now=current)
    failures: list[str] = []
    digest = contract["action"]["request_digest"]
    action_id = contract["action"]["action_id"]
    if not isinstance(post_action_report, dict):
        failures.append("post-action report must be an object")
        post_action_report = {}
    if not isinstance(review_assessment, dict):
        failures.append("review assessment must be an object")
        review_assessment = {}
    if post_action_report.get("post_action_closed") is not True:
        failures.append("POST_ACTION_CLOSED is false")
    if post_action_report.get("request_digest") != digest or post_action_report.get("action_id") != action_id:
        failures.append("post-action report is not bound to this contract action and request digest")
    accountability = phase_report(contract, "ACCOUNTABILITY", current)
    if not accountability["trace_closed"]:
        failures.append("accountability relation obligations are not satisfied")
    for field in ("review_ref", "verification_ref", "verifier_ref", "verification_method", "trust_profile_ref"):
        if not review_assessment.get(field):
            failures.append(f"review assessment {field} is missing")
    if review_assessment.get("verification_status") != "VERIFIED":
        failures.append("review assessment is not VERIFIED by its declared verifier")
    if review_assessment.get("request_digest") != digest or review_assessment.get("action_id") != action_id:
        failures.append("review assessment is not bound to this contract action and request digest")
    if review_assessment.get("challenge_route_ref") != contract["closure_policy"].get("challenge_route_ref"):
        failures.append("review assessment challenge route does not match the contract route")
    if review_assessment.get("challenge_route_tested") is not True:
        failures.append("challenge route has not been tested or accessibly demonstrated")
    open_cases = review_assessment.get("open_cases")
    if not isinstance(open_cases, list):
        failures.append("review assessment open_cases must be a list")
        open_cases = []
    case_ids = [case.get("case_id") for case in open_cases if isinstance(case, dict)]
    valid_case_ids = [case_id for case_id in case_ids if isinstance(case_id, str) and case_id]
    if len(valid_case_ids) != len(case_ids):
        failures.append("each review case must have a non-empty string case_id")
    if len(valid_case_ids) != len(set(valid_case_ids)):
        failures.append("review case identifiers must be unique")
    unresolved = [case.get("case_id", "<unknown>") for case in open_cases if isinstance(case, dict) and case.get("disposition") not in {"RESOLVED", "NO_REMEDY_REQUIRED", "REFERRED_WITH_OWNER"}]
    if unresolved:
        failures.append(f"unresolved review cases remain: {unresolved}")
    for case in open_cases:
        if not isinstance(case, dict) or not case.get("owner_ref") or not case.get("disposition") or not case.get("case_id"):
            failures.append("each review case must have case_id, owner_ref and disposition")
    for obligation in contract["obligations"]:
        if obligation["phase"] == "ACCOUNTABILITY":
            due = parse_time(obligation["due_at"], f"obligation.{obligation['id']}.due_at")
            if due <= current and (obligation["status"] != "DISCHARGED" or not obligation.get("discharge_evidence_ref")):
                failures.append(f"ACCOUNTABILITY obligation {obligation['id']} is due but not discharged")
            elif obligation["status"] not in {"REGISTERED", "DISCHARGED"}:
                failures.append(f"ACCOUNTABILITY obligation {obligation['id']} is neither registered nor discharged")
    return {
        "accountability_closed": not failures,
        "accountability_trace_closure": accountability,
        "failures": failures,
        "evaluated_at": current.isoformat().replace("+00:00", "Z"),
    }
