"""Typed errors emitted by the reference implementation."""

class ECAError(Exception):
    """Base class for expected ECA validation and lifecycle errors."""


class CanonicalizationError(ECAError):
    pass


class SchemaValidationError(ECAError):
    pass


class SemanticValidationError(ECAError):
    pass


class ReadinessError(ECAError):
    pass


class ReplayError(ECAError):
    pass


class StateTransitionError(ECAError):
    pass
