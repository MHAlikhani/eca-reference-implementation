"""Canonical vocabulary for the ECA/ETC proposed profile."""

PROFILE_VERSION = "0.3-proposed"
IMPLEMENTATION_VERSION = "2.0.0"
CANONICALIZATION_PROFILE = "eca-canonical-json-v1"

RELATION_TYPES = (
    "governed_by_mission",
    "delegated_through",
    "evaluated_under_policy",
    "supported_by_evidence",
    "implemented_by_artifact",
    "built_as_release",
    "authorized_by_native_decision",
    "enforced_at_boundary",
    "observed_as_target_effect",
    "challenged_through_review",
    "remediated_by_action",
    "supersedes_version",
)

RELATION_STATUSES = (
    "VERIFIED",
    "PRESENT_UNVERIFIED",
    "STALE",
    "UNAVAILABLE",
    "DISPUTED",
    "CONTRADICTED",
    "NOT_APPLICABLE",
)

PHASES = ("PRE", "POST", "ACCOUNTABILITY")  # trace-closure report phases
OBLIGATION_PHASES = ("PRE", "CONCURRENT", "POST", "ACCOUNTABILITY")
RISK_LEVELS = ("low", "medium", "high", "critical")
RISK_RANK = {name: index for index, name in enumerate(RISK_LEVELS)}

TERMINAL_OUTCOMES = ("COMMITTED", "REJECTED", "RECONCILED")
