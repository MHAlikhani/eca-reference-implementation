"""Draft 2020-12 structural validation for ETC contracts."""
from __future__ import annotations

import json
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
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(contract), key=lambda e: (list(e.absolute_path), e.message))
    if errors:
        details = "; ".join(
            f"/{'/'.join(str(p) for p in error.absolute_path)}: {error.message}" for error in errors
        )
        raise SchemaValidationError(details)
