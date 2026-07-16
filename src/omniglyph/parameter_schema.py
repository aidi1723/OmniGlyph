import math
from typing import Any

Finding = dict[str, str]
ALLOWED_PARAMETER_TYPES = {"object", "string", "number", "integer", "boolean", "array"}


def validate_parameter_schema(schema: object, path: str = "$") -> list[Finding]:
    findings: list[Finding] = []
    ancestors: set[int] = set()
    stack: list[tuple[str, Any, str]] = [("enter", schema, path)]

    while stack:
        event, value, current_path = stack.pop()
        if event == "exit":
            ancestors.remove(id(value))
            continue

        if event == "property":
            field, field_schema = value
            if not isinstance(field, str) or not field.strip():
                findings.append(
                    _finding(
                        f"{current_path}.properties",
                        "type",
                        "Property name must be a non-empty string.",
                    )
                )
            else:
                stack.append(("enter", field_schema, f"{current_path}.properties.{field}"))
            continue

        if event == "after_properties":
            if "enum" in value and not isinstance(value.get("enum"), list):
                findings.append(_finding(f"{current_path}.enum", "type", "enum must be a list."))

            for keyword in ("minLength", "maxLength"):
                if keyword in value and not _is_non_negative_integer(value.get(keyword)):
                    findings.append(
                        _finding(
                            f"{current_path}.{keyword}",
                            "type",
                            f"{keyword} must be a non-negative integer.",
                        )
                    )

            for keyword in ("minimum", "maximum"):
                if keyword in value and not _is_finite_number(value.get(keyword)):
                    findings.append(
                        _finding(
                            f"{current_path}.{keyword}",
                            "type",
                            f"{keyword} must be a finite number.",
                        )
                    )

            if "items" in value:
                stack.append(("enter", value.get("items"), f"{current_path}.items"))
            continue

        if not isinstance(value, dict):
            findings.append(_finding(current_path, "type", "Parameter schema must be an object."))
            continue

        if id(value) in ancestors:
            findings.append(
                _finding(
                    current_path,
                    "cycle",
                    "Parameter schema must not contain cycles.",
                )
            )
            continue

        ancestors.add(id(value))
        expected_type = value.get("type")
        if "type" in value and (
            not isinstance(expected_type, str) or expected_type not in ALLOWED_PARAMETER_TYPES
        ):
            findings.append(
                _finding(
                    f"{current_path}.type",
                    "type",
                    "Schema type must be one of array, boolean, integer, number, object, string.",
                )
            )

        required = value.get("required")
        if "required" in value:
            if not isinstance(required, list):
                findings.append(
                    _finding(f"{current_path}.required", "type", "required must be a list.")
                )
            else:
                for index, field in enumerate(required):
                    if not isinstance(field, str) or not field.strip():
                        findings.append(
                            _finding(
                                f"{current_path}.required[{index}]",
                                "type",
                                "Required field name must be a non-empty string.",
                            )
                        )

        stack.append(("exit", value, current_path))
        stack.append(("after_properties", value, current_path))
        properties = value.get("properties")
        if "properties" in value:
            if not isinstance(properties, dict):
                findings.append(
                    _finding(
                        f"{current_path}.properties",
                        "type",
                        "properties must be an object.",
                    )
                )
            else:
                for field, field_schema in reversed(properties.items()):
                    stack.append(("property", (field, field_schema), current_path))

    return findings


def validate_parameters(parameters: object, schema: object) -> list[Finding]:
    schema_findings = validate_parameter_schema(schema, "$.schema")
    if schema_findings:
        return schema_findings
    assert isinstance(schema, dict)
    if not schema:
        return []
    return _validate_value(parameters, schema, "$")


def _validate_value(value: object, schema: dict[str, object], path: str) -> list[Finding]:
    findings: list[Finding] = []
    stack: list[tuple[object, dict[str, object], str]] = [(value, schema, path)]

    while stack:
        current_value, current_schema, current_path = stack.pop()
        expected_type = current_schema.get("type")
        if isinstance(expected_type, str) and not _matches_type(current_value, expected_type):
            findings.append(_finding(current_path, "type", f"Expected {expected_type}."))
            continue

        enum_values = current_schema.get("enum")
        if isinstance(enum_values, list) and not any(
            _json_values_equal(current_value, candidate) for candidate in enum_values
        ):
            findings.append(_finding(current_path, "enum", "Value is not in the allowed enum."))

        if isinstance(current_value, dict):
            required = current_schema.get("required")
            if isinstance(required, list):
                for field in required:
                    if isinstance(field, str) and field not in current_value:
                        findings.append(
                            _finding(
                                f"{current_path}.{field}",
                                "required",
                                "Required field is missing.",
                            )
                        )
            properties = current_schema.get("properties")
            if isinstance(properties, dict):
                # Reverse so insertion order is preserved when popping.
                for field, field_schema in reversed(list(properties.items())):
                    if (
                        not isinstance(field, str)
                        or not isinstance(field_schema, dict)
                        or field not in current_value
                    ):
                        continue
                    stack.append(
                        (current_value[field], field_schema, f"{current_path}.{field}")
                    )
        elif isinstance(current_value, str):
            findings.extend(_validate_string(current_value, current_schema, current_path))
        elif _is_number(current_value):
            findings.extend(_validate_number(current_value, current_schema, current_path))
        elif isinstance(current_value, list):
            items = current_schema.get("items")
            if isinstance(items, dict):
                for index in range(len(current_value) - 1, -1, -1):
                    stack.append(
                        (current_value[index], items, f"{current_path}[{index}]")
                    )
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


def _is_non_negative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    return not isinstance(value, float) or math.isfinite(value)


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _json_values_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if _is_number(left) or _is_number(right):
        return _is_number(left) and _is_number(right) and left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_values_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _json_values_equal(left[key], right[key]) for key in left
        )
    return left == right


def _format_number(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _finding(path: str, rule: str, message: str) -> Finding:
    return {"path": path, "rule": rule, "message": message}
