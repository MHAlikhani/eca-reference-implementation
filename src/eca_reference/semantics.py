"""Contract semantics, relation validation, and phase-indexed closure."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from .constants import OBLIGATION_PHASES, PHASES, RELATION_STATUSES, RELATION_TYPES, TERMINAL_OUTCOMES
from .errors import SemanticValidationError


def parse_time(value: str, field: str) -> datetime:
    if not isinstance(value, str):
        raise SemanticValidationError(f"{field} must be an RFC 3339 date-time string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SemanticValidationError(f"{field} is not a valid date-time: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SemanticValidationError(f"{field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def _unique(values: Iterable[str], label: str) -> set[str]:
    sequence = list(values)
    if len(sequence) != len(set(sequence)):
        raise SemanticValidationError(f"{label} must not contain duplicate values")
    return set(sequence)


def validate_contract_semantics(contract: dict[str, Any]) -> None:
    action = contract["action"]
    request = action["request"]
    required_request_fields = {
        "qid", "principal_ref", "task", "action", "target", "arguments", "purpose",
        "context", "created_at", "expires_at", "artifact_ref", "policy_ref", "mission_ref",
        "delegation_ref", "nonce",
    }
    missing = required_request_fields - set(request)
    if missing:
        raise SemanticValidationError(f"canonical request is missing fields: {sorted(missing)}")
    created = parse_time(request["created_at"], "action.request.created_at")
    expires = parse_time(request["expires_at"], "action.request.expires_at")
    if expires <= created:
        raise SemanticValidationError("action request expires_at must be later than created_at")
    if action["action_id"] != request["qid"]:
        raise SemanticValidationError("action.action_id must equal action.request.qid")
    if action["action_class"] != request["action"]:
        raise SemanticValidationError("action.action_class must equal action.request.action")
    if action["target"] != request["target"]:
        raise SemanticValidationError("action.target must equal action.request.target")
    if action["request_digest"] == "":
        raise SemanticValidationError("action.request_digest must not be empty")

    risk = contract["risk_profile"]
    phase_fields = {
        "PRE": "pre_action_relation_types",
        "POST": "post_action_relation_types",
        "ACCOUNTABILITY": "accountability_relation_types",
    }
    for phase, field in phase_fields.items():
        _unique(risk[field], f"risk_profile.{field}")
        unknown = set(risk[field]) - set(RELATION_TYPES)
        if unknown:
            raise SemanticValidationError(f"unknown relation types in {field}: {sorted(unknown)}")
    required = set().union(*(set(risk[field]) for field in phase_fields.values()))
    if not required:
        raise SemanticValidationError("at least one phase-specific relation obligation is required")
    if not risk["pre_action_relation_types"]:
        raise SemanticValidationError("PRE relation obligations must be non-empty")
    _unique(risk["critical_relation_types"], "risk_profile.critical_relation_types")
    critical = set(risk["critical_relation_types"])
    if not critical.issubset(required):
        raise SemanticValidationError("critical_relation_types must be a subset of phase-specific required relations")

    node_ids = [node["id"] for node in contract["nodes"]]
    _unique(node_ids, "nodes[].id")
    node_map = {node["id"]: node for node in contract["nodes"]}
    relation_ids = [relation["id"] for relation in contract["relations"]]
    _unique(relation_ids, "relations[].id")
    endpoint_kinds = {
        "governed_by_mission": ("action", "mission"),
        "delegated_through": ("action", "delegation"),
        "evaluated_under_policy": ("action", "policy"),
        "supported_by_evidence": ("action", "evidence"),
        "implemented_by_artifact": ("action", "artifact"),
        "built_as_release": ("artifact", "release"),
        "authorized_by_native_decision": ("action", "native_authorization"),
        "enforced_at_boundary": ("action", "enforcement_point"),
        "observed_as_target_effect": ("action", "target_effect"),
        "challenged_through_review": ("action", "review_process"),
        "remediated_by_action": ("action", "remediation_action"),
    }
    for index, relation in enumerate(contract["relations"]):
        if relation["type"] not in RELATION_TYPES:
            raise SemanticValidationError(f"relations[{index}].type is not canonical")
        if relation["status"] not in RELATION_STATUSES:
            raise SemanticValidationError(f"relations[{index}].status is not canonical")
        for endpoint in ("source", "target"):
            if relation[endpoint] not in node_map:
                raise SemanticValidationError(f"relations[{index}].{endpoint} references an unknown node")
        if relation["type"] in endpoint_kinds:
            expected_source, expected_target = endpoint_kinds[relation["type"]]
            actual_source = node_map[relation["source"]]["kind"]
            actual_target = node_map[relation["target"]]["kind"]
            if (actual_source, actual_target) != (expected_source, expected_target):
                raise SemanticValidationError(
                    f"relations[{index}] {relation['type']} requires {expected_source}->{expected_target}, "
                    f"got {actual_source}->{actual_target}"
                )
        elif relation["type"] == "supersedes_version":
            source_kind = node_map[relation["source"]]["kind"]
            target_kind = node_map[relation["target"]]["kind"]
            if source_kind != target_kind:
                raise SemanticValidationError("supersedes_version must connect two nodes of the same kind")
            if node_map[relation["source"]]["version"] == node_map[relation["target"]]["version"]:
                raise SemanticValidationError("supersedes_version must connect different versions")
        validity = relation["validity"]
        checked = parse_time(validity["checked_at"], f"relations[{index}].validity.checked_at")
        if "valid_from" in validity:
            start = parse_time(validity["valid_from"], f"relations[{index}].validity.valid_from")
            if "valid_until" in validity:
                end = parse_time(validity["valid_until"], f"relations[{index}].validity.valid_until")
                if end <= start:
                    raise SemanticValidationError(f"relations[{index}] has an empty or inverted validity interval")
        elif "valid_until" in validity:
            parse_time(validity["valid_until"], f"relations[{index}].validity.valid_until")
        if relation["status"] == "NOT_APPLICABLE":
            exception = relation.get("not_applicable_exception")
            if not exception or not all(exception.get(k) for k in ("reason", "approved_by", "approved_at", "valid_until")):
                raise SemanticValidationError(f"relations[{index}] NOT_APPLICABLE requires a reason, approver, approval time, and expiry")
            approved_at = parse_time(exception["approved_at"], f"relations[{index}].not_applicable_exception.approved_at")
            valid_until = parse_time(exception["valid_until"], f"relations[{index}].not_applicable_exception.valid_until")
            if valid_until <= approved_at:
                raise SemanticValidationError(f"relations[{index}] NOT_APPLICABLE approval expiry must be later than approval time")

    # A relation type may be required in more than one phase, but it must have at
    # least one relation instance in the graph. The evaluator below treats any
    # unresolved contradiction/dispute for that obligation as a hard failure.
    present_types = {r["type"] for r in contract["relations"]}
    absent_types = required - present_types
    if absent_types:
        raise SemanticValidationError(f"required relation types have no graph instance: {sorted(absent_types)}")

    for age_field in ("native_authorization_max_age_seconds", "enforcement_assessment_max_age_seconds"):
        age_value = risk[age_field]
        if isinstance(age_value, bool) or not isinstance(age_value, int) or age_value < 0:
            raise SemanticValidationError(f"risk_profile.{age_field} must be a non-negative integer")

    freshness = risk.get("freshness_seconds_by_relation_type", {})
    for relation_type, seconds in freshness.items():
        if relation_type not in RELATION_TYPES or not isinstance(seconds, int) or seconds < 0:
            raise SemanticValidationError(f"invalid freshness rule for relation type {relation_type!r}")

    # Obligations are distinct from relation-closure reports. CONCURRENT
    # obligations are checked against runtime guard references at readiness and
    # must later carry discharge evidence before POST closure.
    obligations = contract["obligations"]
    _unique((item["id"] for item in obligations), "obligations[].id")
    for index, obligation in enumerate(obligations):
        if obligation["phase"] not in OBLIGATION_PHASES:
            raise SemanticValidationError(f"obligations[{index}].phase is not canonical")
        parse_time(obligation["due_at"], f"obligations[{index}].due_at")
        if obligation["status"] == "DISCHARGED" and not obligation.get("discharge_evidence_ref"):
            raise SemanticValidationError(f"obligations[{index}] is DISCHARGED but has no discharge_evidence_ref")
        if obligation["phase"] == "CONCURRENT" and not obligation.get("runtime_guard_ref"):
            raise SemanticValidationError(f"obligations[{index}] CONCURRENT phase requires runtime_guard_ref")

    # The profile's canonical hard-gate switches cannot be weakened by an instance.
    closure = contract["closure_policy"]
    if closure["critical_relations_are_hard_gates"] is not True:
        raise SemanticValidationError("critical relations must remain hard gates")
    if closure["coverage_is_diagnostic_only"] is not True:
        raise SemanticValidationError("RRC/coverage must remain diagnostic only")


def evaluate_relation(relation: dict[str, Any], *, now: datetime, risk: dict[str, Any], critical: bool, allow_na: bool) -> dict[str, Any]:
    status = relation["status"]
    typ = relation["type"]
    validity = relation["validity"]
    if status == "NOT_APPLICABLE":
        exception = relation.get("not_applicable_exception", {})
        approved_at = parse_time(exception["approved_at"], "not_applicable_exception.approved_at")
        valid_until = parse_time(exception["valid_until"], "not_applicable_exception.valid_until")
        if not allow_na or critical or not exception.get("reason") or not exception.get("approved_by") or approved_at > now or valid_until <= approved_at or valid_until <= now:
            return {"satisfied": False, "reason": "NOT_APPLICABLE exception is not valid or is not permitted", "status": status}
        return {"satisfied": True, "reason": "approved profile exception; excluded from VERIFIED coverage", "status": status, "excluded": True}
    if status != "VERIFIED":
        return {"satisfied": False, "reason": f"relation status is {status}, not VERIFIED", "status": status}
    checked = parse_time(validity["checked_at"], "relation.validity.checked_at")
    if checked > now:
        return {"satisfied": False, "reason": "verification time is in the future", "status": status}
    valid_from = parse_time(validity.get("valid_from", relation["observed_at"]), "relation.validity.valid_from")
    if valid_from > now:
        return {"satisfied": False, "reason": "relation is not yet valid", "status": status}
    if "valid_until" in validity and parse_time(validity["valid_until"], "relation.validity.valid_until") <= now:
        return {"satisfied": False, "reason": "relation validity interval has expired", "status": status}
    max_age = risk.get("freshness_seconds_by_relation_type", {}).get(typ)
    if max_age is not None:
        observed = parse_time(relation["observed_at"], "relation.observed_at")
        age = (now - observed).total_seconds()
        if age < 0 or age > max_age:
            return {"satisfied": False, "reason": f"evidence age {age:.0f}s exceeds freshness limit {max_age}s", "status": "STALE"}
    return {"satisfied": True, "reason": "VERIFIED under the declared verifier/trust profile", "status": status, "excluded": False}


def phase_report(contract: dict[str, Any], phase: str, now: datetime) -> dict[str, Any]:
    if phase not in PHASES:
        raise SemanticValidationError(f"unknown lifecycle phase: {phase}")
    risk = contract["risk_profile"]
    phase_field = {
        "PRE": "pre_action_relation_types",
        "POST": "post_action_relation_types",
        "ACCOUNTABILITY": "accountability_relation_types",
    }[phase]
    required = list(risk[phase_field])
    critical = set(risk["critical_relation_types"])
    rels_by_type: dict[str, list[dict[str, Any]]] = {}
    for relation in contract["relations"]:
        rels_by_type.setdefault(relation["type"], []).append(relation)

    results: dict[str, dict[str, Any]] = {}
    verified_count = 0
    excluded_count = 0
    closed = True
    for typ in required:
        instances = rels_by_type.get(typ, [])
        if not instances:
            results[typ] = {"satisfied": False, "reason": "missing required relation", "status": "MISSING"}
            closed = False
            continue
        # A valid verified relation is required; an unresolved dispute or
        # contradiction on a parallel edge blocks closure rather than being
        # hidden by a second, convenient assertion.
        evaluated = [evaluate_relation(r, now=now, risk=risk, critical=typ in critical, allow_na=contract["closure_policy"]["allow_not_applicable"]) for r in instances]
        blocking = [x for x in evaluated if x.get("status") in {"DISPUTED", "CONTRADICTED"}]
        satisfied = any(x["satisfied"] for x in evaluated) and not blocking
        if not satisfied:
            closed = False
        if satisfied and any(x.get("status") == "VERIFIED" and x["satisfied"] for x in evaluated):
            verified_count += 1
        elif satisfied and all(x.get("excluded") for x in evaluated):
            excluded_count += 1
        results[typ] = {
            "satisfied": satisfied,
            "instances": evaluated,
            "reason": "all active assertions are compatible and at least one satisfies the obligation" if satisfied else "no satisfying relation or an unresolved contradiction/dispute exists",
        }
    denominator = len(required)
    return {
        "phase": phase,
        "required_relation_types": required,
        "verified_required_count": verified_count,
        "approved_not_applicable_count": excluded_count,
        "denominator": denominator,
        "rrc": (verified_count / denominator) if denominator else None,
        "trace_closed": closed,
        "relations": results,
    }


def validate_outcome(outcome: dict[str, Any], request_digest: str, target: str) -> list[str]:
    if not isinstance(outcome, dict):
        return ["outcome must be an object"]
    errors: list[str] = []
    state = outcome.get("state")
    if state not in (*TERMINAL_OUTCOMES, "UNKNOWN"):
        errors.append("outcome.state must be COMMITTED, REJECTED, RECONCILED, or UNKNOWN")
    if outcome.get("request_digest") != request_digest:
        errors.append("outcome request_digest does not match the canonical request")
    if outcome.get("target") != target:
        errors.append("outcome target does not match the action target")
    if state in {"COMMITTED", "REJECTED", "RECONCILED"}:
        if outcome.get("receipt_verified") is not True:
            errors.append("terminal outcome requires a verified target-linked receipt")
        for field in ("receipt_ref", "receipt_verifier_ref", "receipt_verification_method", "receipt_trust_profile_ref"):
            if not outcome.get(field):
                errors.append(f"terminal outcome requires {field}")
        target_result = outcome.get("target_result")
        if state in {"COMMITTED", "REJECTED"} and target_result != state:
            errors.append("terminal outcome state must match target_result")
        if state == "RECONCILED" and target_result not in {"COMMITTED", "REJECTED"}:
            errors.append("RECONCILED requires a resolved COMMITTED or REJECTED target_result")
    if state == "UNKNOWN" and outcome.get("receipt_verified"):
        errors.append("UNKNOWN outcome must not claim a verified terminal receipt")
    return errors
