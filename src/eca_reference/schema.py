"""Draft 2020-12 structural validation for ETC contracts."""
from __future__ import annotations

import json
import re
from datetime import datetime
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .errors import SchemaValidationError


def schema_document() -> dict[str, Any]:
    path = files("eca_reference").joinpath("schemas/etc-profile-0.3-proposed.schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema_definition() -> None:
    Draft202012Validator.check_schema(schema_document())


def validate_contract_structure(contract: dict[str, Any]) -> None:
    schema = schema_document()
    format_checker = FormatChecker()

    # jsonschema delegates RFC 3339 validation to optional dependencies in
    # some environments. Register a deterministic checker so naive timestamps
    # are rejected identically across the supported Python matrix.
    @format_checker.checks("date-time")
    def _is_timezone_aware_rfc3339(value: Any) -> bool:
        if not isinstance(value, str):
            return True  # The schema's "type" constraint reports non-strings.
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
            r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
            value,
        ):
            return False
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return parsed.tzinfo is not None and parsed.utcoffset() is not None

    validator = Draft202012Validator(schema, format_checker=format_checker)
    errors = sorted(validator.iter_errors(contract), key=lambda e: (list(e.absolute_path), e.message))
    if errors:
        details = "; ".join(
            f"/{'/'.join(str(p) for p in error.absolute_path)}: {error.message}" for error in errors
        )
        raise SchemaValidationError(details)
