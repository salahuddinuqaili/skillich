"""Input validation for skill parameters against JSON Schema definitions.

Uses only stdlib -- no jsonschema dependency required for basic validation.
"""

from typing import Any, Dict, List


_JSON_TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def validate_parameters(schema: Dict[str, Any], kwargs: Dict[str, Any]) -> List[str]:
    """Validate kwargs against a JSON Schema. Returns a list of error strings.

    An empty list means validation passed. Supports: type checking, required
    fields, enum values, and nested object validation.
    """
    errors: List[str] = []

    if schema.get("type") != "object":
        return errors

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    for field_name in required:
        if field_name not in kwargs:
            errors.append(f"Missing required parameter: '{field_name}'")

    for field_name, value in kwargs.items():
        if field_name not in properties:
            continue

        field_schema = properties[field_name]
        expected_type_name = field_schema.get("type")

        if expected_type_name and value is not None:
            expected_type = _JSON_TYPE_MAP.get(expected_type_name)
            if expected_type and not isinstance(value, expected_type):
                errors.append(
                    f"Parameter '{field_name}' expected type '{expected_type_name}', "
                    f"got '{type(value).__name__}'"
                )

        if "enum" in field_schema and value not in field_schema["enum"]:
            errors.append(
                f"Parameter '{field_name}' must be one of {field_schema['enum']}, "
                f"got '{value}'"
            )

        if expected_type_name == "object" and isinstance(value, dict):
            nested_errors = validate_parameters(field_schema, value)
            errors.extend(nested_errors)

    return errors
