from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from eca_reference.canonical import request_digest

NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
NOW_TEXT = "2026-11-18T12:00:00Z"

RELATIONS = [
    ("governed_by_mission", "action", "mission"),
    ("delegated_through", "action", "delegation"),
    ("evaluated_under_policy", "action", "policy"),
    ("supported_by_evidence", "action", "evidence"),
    ("implemented_by_artifact", "action", "artifact"),
    ("built_as_release", "artifact", "release"),
    ("authorized_by_native_decision", "action", "native_authorization"),
    ("enforced_at_boundary", "action", "enforcement_point"),
    ("observed_as_target_effect", "action", "target_effect"),
    ("challenged_through_review", "action", "review_process"),
    ("remediated_by_action", "action", "remediation_action"),
    ("supersedes_version", "version_new", "version_old"),
]


def make_contract() -> dict:
    req = {
        "qid": "request:city-traffic:00042",
        "principal_ref": "principal:traffic-operator:17",
        "task": "bounded signal timing adjustment",
        "action": "traffic.signal.adjust",
        "target": "junction:munich-maxvorstadt:04",
        "arguments": {"phase": "north_south", "duration_delta_ms": 4000},
        "purpose": "reduce queue spillback without violating pedestrian minimums",
        "context": {"jurisdiction": "fictional-demo", "operating_mode": "normal"},
        "created_at": "2026-11-18T10:00:00Z",
        "expires_at": "2026-11-18T14:00:00Z",
        "artifact_ref": "artifact:controller:sha256:abc123",
        "policy_ref": "policy:traffic:2026-11-v3",
        "mission_ref": "mission:traffic-flow:2026-v2",
        "delegation_ref": "delegation:traffic-operator:17",
        "nonce": "nonce-0000000000000042",
    }
    digest = request_digest(req)
    kinds = [
        ("node:action", "action", "act-v1"),
        ("node:mission", "mission", "m-v2"),
        ("node:delegation", "delegation", "d-v3"),
        ("node:policy", "policy", "p-v3"),
        ("node:evidence", "evidence", "e-v5"),
        ("node:artifact", "artifact", "a-v7"),
        ("node:release", "release", "r-v7"),
        ("node:native-auth", "native_authorization", "na-42"),
        ("node:pep", "enforcement_point", "pep-v2"),
        ("node:effect", "target_effect", "effect-42"),
        ("node:review", "review_process", "review-route-v1"),
        ("node:remedy", "remediation_action", "remedy-plan-v1"),
        ("node:version-new", "version", "v2"),
        ("node:version-old", "version", "v1"),
    ]
    nodes = [
        {
            "id": node_id,
            "kind": kind,
            "native_ref": {
                "node:native-auth": "native-auth:permit:00042",
                "node:pep": "pep:controller-boundary:04",
            }.get(node_id, node_id.replace("node:", "native:")),
            "version": version,
            "owner_ref": "owner:demo-operator",
            "privacy_class": "operational-metadata",
            "retention_rule_ref": "retention:90d",
            "attributes": {},
        }
        for node_id, kind, version in kinds
    ]
    relation_endpoints = {
        "governed_by_mission": ("node:action", "node:mission"),
        "delegated_through": ("node:action", "node:delegation"),
        "evaluated_under_policy": ("node:action", "node:policy"),
        "supported_by_evidence": ("node:action", "node:evidence"),
        "implemented_by_artifact": ("node:action", "node:artifact"),
        "built_as_release": ("node:artifact", "node:release"),
        "authorized_by_native_decision": ("node:action", "node:native-auth"),
        "enforced_at_boundary": ("node:action", "node:pep"),
        "observed_as_target_effect": ("node:action", "node:effect"),
        "challenged_through_review": ("node:action", "node:review"),
        "remediated_by_action": ("node:action", "node:remedy"),
        "supersedes_version": ("node:version-new", "node:version-old"),
    }
    relations = []
    for index, (relation_type, _, _) in enumerate(RELATIONS, start=1):
        source, target = relation_endpoints[relation_type]
        relations.append({
            "id": f"relation:{index:02d}",
            "type": relation_type,
            "source": source,
            "target": target,
            "schema_version": "etc-relations-0.3-proposed",
            "asserting_issuer": "issuer:demo-registry",
            "asserted_at": "2026-11-18T11:50:00Z",
            "observed_at": "2026-11-18T11:50:00Z",
            "validity": {
                "checked_at": "2026-11-18T11:55:00Z",
                "valid_from": "2026-11-18T11:00:00Z",
                "valid_until": "2026-11-18T14:00:00Z",
            },
            "native_evidence_ref": f"native-evidence:{index:02d}",
            "verification_method": "demo-independent-check-v1",
            "verifier_ref": "verifier:demo-auditor",
            "trust_profile_ref": "trust:demo-lab-v1",
            "limitations": ["synthetic fixture; no external issuer was contacted"],
            "status": "VERIFIED",
            "owner_ref": "owner:demo-operator",
            "privacy_class": "operational-metadata",
            "retention_rule_ref": "retention:90d",
            "change_dependencies": [],
        })
    return {
        "contract_id": "etc:demo:city-traffic:00042",
        "profile_version": "0.3-proposed",
        "action": {
            "action_id": req["qid"],
            "request": req,
            "request_digest": digest,
            "request_binding_profile": "eca-canonical-json-v1",
            "action_class": req["action"],
            "target": req["target"],
            "validity": {"not_before": "2026-11-18T10:00:00Z", "expires_at": "2026-11-18T14:00:00Z"},
        },
        "risk_profile": {
            "id": "risk:medium-traffic-adjustment",
            "version": "1.0",
            "level": "medium",
            "action_class": req["action"],
            "jurisdictional_context": "fictional demonstration only",
            "pre_action_relation_types": [
                "governed_by_mission", "delegated_through", "evaluated_under_policy", "supported_by_evidence",
                "implemented_by_artifact", "built_as_release", "authorized_by_native_decision", "enforced_at_boundary",
            ],
            "post_action_relation_types": ["observed_as_target_effect"],
            "accountability_relation_types": ["challenged_through_review", "remediated_by_action", "supersedes_version"],
            "critical_relation_types": ["delegated_through", "supported_by_evidence", "authorized_by_native_decision", "enforced_at_boundary"],
            "freshness_seconds_by_relation_type": {"supported_by_evidence": 3600, "authorized_by_native_decision": 900, "delegated_through": 3600},
            "native_authorization_max_age_seconds": 60,
            "enforcement_assessment_max_age_seconds": 60,
            "independence_policy_ref": "independence:demo-profile",
            "obligation_policy_ref": "obligations:demo-profile",
        },
        "nodes": nodes,
        "relations": relations,
        "obligations": [
            {"id": "obligation:pre:1", "phase": "PRE", "owner_ref": "role:traffic-safety", "status": "DISCHARGED", "due_at": "2026-11-18T12:00:00Z", "discharge_evidence_ref": "evidence:pre-check:1"},
            {"id": "obligation:post:1", "phase": "POST", "owner_ref": "role:operations", "status": "REGISTERED", "due_at": "2026-11-18T15:00:00Z", "escalation_rule_ref": "escalation:post:1"},
            {"id": "obligation:accountability:1", "phase": "ACCOUNTABILITY", "owner_ref": "role:review", "status": "REGISTERED", "due_at": "2026-11-19T12:00:00Z"},
        ],
        "closure_policy": {
            "critical_relations_are_hard_gates": True,
            "coverage_is_diagnostic_only": True,
            "allow_not_applicable": True,
            "post_action_requirements_ref": "requirements:post:demo",
            "accountability_requirements_ref": "requirements:accountability:demo",
            "challenge_route_ref": "https://example.invalid/fictional-review-route",
        },
    }


def make_native_authorization(contract: dict | None = None) -> dict:
    c = contract or make_contract()
    request = c["action"]["request"]
    return {
        "native_ref": "native-auth:permit:00042",
        "verdict": "PERMIT",
        "verified_by_native_verifier": True,
        "verifier_ref": "native-verifier:opa-adapter-demo",
        "verification_ref": "native-auth-verification:00042",
        "verification_method": "native-pdp-attestation-check-v1",
        "verified_at": NOW_TEXT,
        "request_digest": c["action"]["request_digest"],
        "principal_ref": request["principal_ref"],
        "action": request["action"],
        "target": request["target"],
        "policy_ref": request["policy_ref"],
        "valid_from": "2026-11-18T10:00:00Z",
        "valid_until": "2026-11-18T14:00:00Z",
        "revocation_state": "ACTIVE",
        "replay_state": "AVAILABLE",
        "required_approval_roles": ["traffic-operator", "safety-reviewer"],
        "verified_approval_roles": ["traffic-operator", "safety-reviewer"],
        "trust_profile_ref": "trust:native-pdp-v1",
    }


def make_enforcement_assessment(contract: dict | None = None) -> dict:
    c = contract or make_contract()
    request = c["action"]["request"]
    return {
        "active": True,
        "verification_status": "VERIFIED",
        "verification_ref": "pep-verification:00042",
        "verifier_ref": "verifier:pep-health-check",
        "verification_method": "native-enforcement-assessment-v1",
        "assessed_at": NOW_TEXT,
        "trust_profile_ref": "trust:pep-test",
        "request_digest": c["action"]["request_digest"],
        "action": request["action"],
        "target": request["target"],
        "policy_ref": request["policy_ref"],
        "adapter_version": "demo-pep-adapter-1.0",
        "bypass_controlled": True,
        "enforcement_point_ref": "pep:controller-boundary:04",
        "active_guard_refs": [],
    }


def deep_contract() -> dict:
    return deepcopy(make_contract())


def make_dispatch_assessment(contract):
    return {
        "assessment_ref": "dispatch-assessment:00042",
        "dispatch_ref": "dispatch:00042",
        "verification_ref": "verification:dispatch:00042",
        "action_ready": True,
        "request_digest": contract["action"]["request_digest"],
        "action": contract["action"]["action_class"],
        "target": contract["action"]["target"],
        "dispatched_at": "2026-11-18T11:59:55Z",
        "verification_status": "VERIFIED",
        "verifier_ref": "verifier:dispatch-audit",
        "verification_method": "native-attestation-verification-v1",
        "trust_profile_ref": "trust:dispatch-assessment:test",
        "limitations": [],
    }


def make_outcome(contract, state="COMMITTED", receipt_verified=True):
    outcome = {
        "state": state,
        "request_digest": contract["action"]["request_digest"],
        "target": contract["action"]["target"],
        "receipt_verified": receipt_verified,
    }
    if state in {"COMMITTED", "REJECTED", "RECONCILED"}:
        outcome.update({
            "target_result": state if state in {"COMMITTED", "REJECTED"} else "COMMITTED",
            "receipt_ref": "target-receipt:00042",
            "receipt_verifier_ref": "verifier:target-receipt",
            "receipt_verification_method": "target-receipt-hmac-test-profile",
            "receipt_trust_profile_ref": "trust:target-test",
        })
    return outcome


def make_review_assessment(contract, open_cases=None):
    return {
        "review_ref": "review:case-bundle:00042",
        "verification_ref": "verification:review:00042",
        "verifier_ref": "verifier:review-audit",
        "verification_method": "review-record-attestation-v1",
        "trust_profile_ref": "trust:review-test",
        "verification_status": "VERIFIED",
        "action_id": contract["action"]["action_id"],
        "request_digest": contract["action"]["request_digest"],
        "challenge_route_ref": contract["closure_policy"]["challenge_route_ref"],
        "challenge_route_tested": True,
        "open_cases": open_cases or [],
    }
