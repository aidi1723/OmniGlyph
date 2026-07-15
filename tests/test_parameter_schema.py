import pytest

from omniglyph.parameter_schema import validate_parameter_schema, validate_parameters


@pytest.mark.parametrize(
    ("schema", "expected_path"),
    [
        ([], "$"),
        ({"type": []}, "$.type"),
        ({"type": "date"}, "$.type"),
        ({"required": "service"}, "$.required"),
        ({"required": [" "]}, "$.required[0]"),
        ({"properties": []}, "$.properties"),
        ({"properties": {"": {}}}, "$.properties"),
        ({"properties": {"service": []}}, "$.properties.service"),
        ({"enum": "safe"}, "$.enum"),
        ({"minLength": True}, "$.minLength"),
        ({"minLength": -1}, "$.minLength"),
        ({"maxLength": "8"}, "$.maxLength"),
        ({"minimum": True}, "$.minimum"),
        ({"minimum": float("nan")}, "$.minimum"),
        ({"maximum": "10"}, "$.maximum"),
        ({"items": []}, "$.items"),
    ],
)
def test_validate_parameter_schema_reports_invalid_definitions(schema, expected_path):
    findings = validate_parameter_schema(schema)

    assert expected_path in [finding["path"] for finding in findings]


def test_validate_parameter_schema_accepts_valid_nested_definition():
    schema = {
        "type": "object",
        "required": ["service", "retries", "tags"],
        "properties": {
            "service": {
                "type": "string",
                "enum": ["network", "dns"],
                "pattern": "^[a-z]+$",
            },
            "retries": {"type": "integer", "minimum": 1, "maximum": 3},
            "tags": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
            },
        },
        "format": "unknown-format",
    }

    assert validate_parameter_schema(schema) == []


def test_validate_parameters_rejects_invalid_schema_before_validating_values():
    assert validate_parameters({}, {"required": "service"}) == [
        {
            "path": "$.schema.required",
            "rule": "type",
            "message": "required must be a list.",
        }
    ]


def test_validate_parameters_accepts_matching_object_parameters():
    schema = {
        "type": "object",
        "required": ["service"],
        "properties": {
            "service": {"type": "string", "enum": ["network", "dns"]},
            "force": {"type": "boolean"},
        },
    }

    findings = validate_parameters({"service": "network", "force": False}, schema)

    assert findings == []


def test_validate_parameters_reports_missing_required_field():
    schema = {"type": "object", "required": ["service"], "properties": {"service": {"type": "string"}}}

    findings = validate_parameters({}, schema)

    assert findings == [{"path": "$.service", "rule": "required", "message": "Required field is missing."}]


def test_validate_parameters_reports_string_length_and_enum_failures():
    schema = {"type": "object", "properties": {"mode": {"type": "string", "enum": ["safe"], "minLength": 4, "maxLength": 8}}}

    findings = validate_parameters({"mode": "x"}, schema)

    assert {"path": "$.mode", "rule": "enum", "message": "Value is not in the allowed enum."} in findings
    assert {"path": "$.mode", "rule": "minLength", "message": "String is shorter than 4 characters."} in findings


def test_validate_parameters_reports_numeric_bounds():
    schema = {"type": "object", "properties": {"retries": {"type": "integer", "minimum": 1, "maximum": 3}}}

    findings = validate_parameters({"retries": 5}, schema)

    assert findings == [{"path": "$.retries", "rule": "maximum", "message": "Number is greater than 3."}]


def test_validate_parameters_reports_array_item_failures():
    schema = {"type": "object", "properties": {"ports": {"type": "array", "items": {"type": "integer", "minimum": 1}}}}

    findings = validate_parameters({"ports": [80, "443", 0]}, schema)

    assert {"path": "$.ports[1]", "rule": "type", "message": "Expected integer."} in findings
    assert {"path": "$.ports[2]", "rule": "minimum", "message": "Number is less than 1."} in findings


def test_validate_parameters_ignores_unknown_schema_keywords():
    schema = {"type": "object", "properties": {"service": {"type": "string", "pattern": "^[a-z]+$"}}}

    findings = validate_parameters({"service": "NETWORK"}, schema)

    assert findings == []


def test_validate_parameters_distinguishes_boolean_and_numeric_enum_values():
    schema = {"type": "object", "properties": {"level": {"enum": [1]}}}

    assert validate_parameters({"level": True}, schema) == [
        {"path": "$.level", "rule": "enum", "message": "Value is not in the allowed enum."}
    ]
    assert validate_parameters({"level": 1.0}, schema) == []
