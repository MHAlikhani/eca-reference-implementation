"""ECA bounded reference implementation, version 2.0.0."""
from .constants import IMPLEMENTATION_VERSION, PROFILE_VERSION
from .contract import (
    evaluate_accountability_closure,
    evaluate_action_readiness,
    evaluate_post_action_closure,
    evaluate_trace_closure,
    validate_contract,
)

__version__ = IMPLEMENTATION_VERSION
__all__ = [
    "IMPLEMENTATION_VERSION", "PROFILE_VERSION", "validate_contract",
    "evaluate_trace_closure", "evaluate_action_readiness",
    "evaluate_post_action_closure", "evaluate_accountability_closure",
]
