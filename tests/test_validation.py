"""Tests for core.validation module."""

from core.validation import validate_parameters


SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "role": {"type": "string", "enum": ["admin", "user"]},
    },
    "required": ["name", "age"],
}


class TestValidation:
    def test_valid_input(self):
        errors = validate_parameters(SCHEMA, {"name": "Alice", "age": 30, "role": "admin"})
        assert errors == []

    def test_missing_required(self):
        errors = validate_parameters(SCHEMA, {"name": "Alice"})
        assert len(errors) == 1
        assert "age" in errors[0]

    def test_wrong_type(self):
        errors = validate_parameters(SCHEMA, {"name": 123, "age": 30})
        assert len(errors) == 1
        assert "string" in errors[0]

    def test_invalid_enum(self):
        errors = validate_parameters(SCHEMA, {"name": "Alice", "age": 30, "role": "superadmin"})
        assert len(errors) == 1
        assert "enum" in errors[0].lower() or "must be one of" in errors[0]

    def test_extra_fields_ignored(self):
        errors = validate_parameters(SCHEMA, {"name": "Alice", "age": 30, "extra": True})
        assert errors == []

    def test_empty_schema(self):
        errors = validate_parameters({}, {"anything": "goes"})
        assert errors == []

    def test_number_accepts_int_and_float(self):
        schema = {
            "type": "object",
            "properties": {"val": {"type": "number"}},
            "required": ["val"],
        }
        assert validate_parameters(schema, {"val": 3}) == []
        assert validate_parameters(schema, {"val": 3.14}) == []
