"""Validate taxonomy YAML files against JSON Schema definitions."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None  # type: ignore[assignment]


_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "taxonomy" / "schemas"


@dataclass
class ValidationReport:
    """Result of validating taxonomy files."""
    files_checked: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _load_schema(name: str) -> dict:
    schema_path = _SCHEMA_DIR / name
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def validate_taxonomy(taxonomy_dir: str = "taxonomy") -> ValidationReport:
    """Validate all YAML files in the taxonomy directory against their schemas.

    Requires the jsonschema package (install with pip install skillich[dev]).
    """
    if jsonschema is None:
        raise ImportError("jsonschema is required for validation: pip install jsonschema")

    report = ValidationReport()
    taxonomy_path = Path(taxonomy_dir)

    if not taxonomy_path.exists():
        report.errors.append(f"Taxonomy directory not found: {taxonomy_dir}")
        return report

    function_schema = _load_schema("function.schema.json")
    role_schema = _load_schema("role.schema.json")

    for func_dir in sorted(taxonomy_path.iterdir()):
        if not func_dir.is_dir() or func_dir.name == "schemas":
            continue

        # Validate _function.yaml
        func_file = func_dir / "_function.yaml"
        if func_file.exists():
            report.files_checked += 1
            _validate_file(func_file, function_schema, report)
        else:
            report.errors.append(f"{func_dir.name}: missing _function.yaml")

        # Validate role files
        for role_file in sorted(func_dir.glob("*.yaml")):
            if role_file.name == "_function.yaml":
                continue
            report.files_checked += 1
            _validate_file(role_file, role_schema, report)

    return report


def _validate_file(file_path: Path, schema: dict, report: ValidationReport) -> None:
    """Validate a single YAML file against a JSON Schema."""
    relative = file_path.as_posix()
    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        report.errors.append(f"{relative}: YAML parse error: {e}")
        return

    if data is None:
        report.errors.append(f"{relative}: file is empty")
        return

    validator = jsonschema.Draft202012Validator(schema)
    for error in validator.iter_errors(data):
        path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
        report.errors.append(f"{relative}: {path}: {error.message}")
