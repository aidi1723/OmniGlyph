from typing import Any

Finding = dict[str, str]


def validate_parameters(parameters: object, schema: dict[str, object]) -> list[Finding]:
    if not schema:
        return []
    return _validate_value(parameters, schema, "$")


def _validate_value(value: object, schema: dict[str, object], path: str) -> list[Finding]:
    findings: list[Finding] = []
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _matches_type(value, expected_type):
        return [_finding(path, "type", f"Expected {expected_type}.")]

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        findings.append(_finding(path, "enum", "Value is not in the allowed enum."))

    if isinstance(value, dict):
        findings.extend(_validate_object(value, schema, path))
    elif isinstance(value, str):
        findings.extend(_validate_string(value, schema, path))
    elif _is_number(value):
        findings.extend(_validate_number(value, schema, path))
    elif isinstance(value, list):
        findings.extend(_validate_array(value, schema, path))
    return findings


def _validate_object(value: dict[Any, Any], schema: dict[str, object], path: str) -> list[Finding]:
    findings: list[Finding] = []
    required = schema.get("required")
    if isinstance(required, list):
        for field in required:
            if isinstance(field, str) and field not in value:
                findings.append(_finding(f"{path}.{field}", "required", "Required field is missing."))
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for field, field_schema in properties.items():
            if not isinstance(field, str) or not isinstance(field_schema, dict) or field not in value:
                continue
            findings.extend(_validate_value(value[field], field_schema, f"{path}.{field}"))
    return findings


def _validate_string(value: str, schema: dict[str, object], path: str) -> list[Finding]:
    findings = []
    min_length = schema.get("minLength")
    if isinstance(min_length, int) and len(value) < min_length:
        findings.append(_finding(path, "minLength", f"String is shorter than {min_length} characters."))
    max_length = schema.get("maxLength")
    if isinstance(max_length, int) and len(value) > max_length:
        findings.append(_finding(path, "maxLength", f"String is longer than {max_length} characters."))
    return findings


def _validate_number(value: object, schema: dict[str, object], path: str) -> list[Finding]:
    findings = []
    minimum = schema.get("minimum")
    if _is_number(minimum) and value < minimum:  # type: ignore[operator]
        findings.append(_finding(path, "minimum", f"Number is less than {_format_number(minimum)}."))
    maximum = schema.get("maximum")
    if _is_number(maximum) and value > maximum:  # type: ignore[operator]
        findings.append(_finding(path, "maximum", f"Number is greater than {_format_number(maximum)}."))
    return findings


def _validate_array(value: list[Any], schema: dict[str, object], path: str) -> list[Finding]:
    items = schema.get("items")
    if not isinstance(items, dict):
        return []
    findings = []
    for index, item in enumerate(value):
        findings.extend(_validate_value(item, items, f"{path}[{index}]"))
    return findings


def _matches_type(value: object, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return _is_number(value)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    return True


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _format_number(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _finding(path: str, rule: str, message: str) -> Finding:
    return {"path": path, "rule": rule, "message": message}
