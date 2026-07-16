import pytest

from omniglyph.parameter_schema import validate_parameter_schema, validate_parameters


@pytest.mark.parametrize(
    ("schema", "expected"),
    [
        ([], {"path": "$", "rule": "type", "message": "Parameter schema must be an object."}),
        (
            {"type": []},
            {
                "path": "$.type",
                "rule": "type",
                "message": "Schema type must be one of array, boolean, integer, number, object, string.",
            },
        ),
        (
            {"type": "date"},
            {
                "path": "$.type",
                "rule": "type",
                "message": "Schema type must be one of array, boolean, integer, number, object, string.",
            },
        ),
        (
            {"required": "service"},
            {"path": "$.required", "rule": "type", "message": "required must be a list."},
        ),
        (
            {"required": [" "]},
            {
                "path": "$.required[0]",
                "rule": "type",
                "message": "Required field name must be a non-empty string.",
            },
        ),
        (
            {"properties": []},
            {"path": "$.properties", "rule": "type", "message": "properties must be an object."},
        ),
        (
            {"properties": {"": {}}},
            {
                "path": "$.properties",
                "rule": "type",
                "message": "Property name must be a non-empty string.",
            },
        ),
        (
            {"properties": {"service": []}},
            {
                "path": "$.properties.service",
                "rule": "type",
                "message": "Parameter schema must be an object.",
            },
        ),
        (
            {"enum": "safe"},
            {"path": "$.enum", "rule": "type", "message": "enum must be a list."},
        ),
        (
            {"minLength": True},
            {
                "path": "$.minLength",
                "rule": "type",
                "message": "minLength must be a non-negative integer.",
            },
        ),
        (
            {"minLength": -1},
            {
                "path": "$.minLength",
                "rule": "type",
                "message": "minLength must be a non-negative integer.",
            },
        ),
        (
            {"maxLength": "8"},
            {
                "path": "$.maxLength",
                "rule": "type",
                "message": "maxLength must be a non-negative integer.",
            },
        ),
        (
            {"minimum": True},
            {"path": "$.minimum", "rule": "type", "message": "minimum must be a finite number."},
        ),
        (
            {"minimum": float("nan")},
            {"path": "$.minimum", "rule": "type", "message": "minimum must be a finite number."},
        ),
        (
            {"minimum": float("-inf")},
            {"path": "$.minimum", "rule": "type", "message": "minimum must be a finite number."},
        ),
        (
            {"maximum": "10"},
            {"path": "$.maximum", "rule": "type", "message": "maximum must be a finite number."},
        ),
        (
            {"maximum": float("inf")},
            {"path": "$.maximum", "rule": "type", "message": "maximum must be a finite number."},
        ),
        (
            {"items": []},
            {"path": "$.items", "rule": "type", "message": "Parameter schema must be an object."},
        ),
    ],
)
def test_validate_parameter_schema_reports_invalid_definitions(schema, expected):
    findings = validate_parameter_schema(schema)

    assert findings == [expected]


def test_validate_parameter_schema_reports_properties_cycle():
    schema = {}
    schema["properties"] = {"loop": schema}

    assert validate_parameter_schema(schema) == [
        {
            "path": "$.properties.loop",
            "rule": "cycle",
            "message": "Parameter schema must not contain cycles.",
        }
    ]


def test_validate_parameter_schema_reports_items_cycle():
    schema = {}
    schema["items"] = schema

    assert validate_parameter_schema(schema) == [
        {
            "path": "$.items",
            "rule": "cycle",
            "message": "Parameter schema must not contain cycles.",
        }
    ]


def test_validate_parameter_schema_accepts_deep_acyclic_definition():
    schema = {}
    current = schema
    for _ in range(1500):
        nested = {}
        current["items"] = nested
        current = nested

    assert validate_parameter_schema(schema) == []


def test_validate_parameter_schema_allows_shared_child_schema_on_siblings():
    shared = {"type": "string", "minLength": 1}
    schema = {
        "type": "object",
        "properties": {
            "left": shared,
            "right": shared,
            "tags": {"type": "array", "items": shared},
        },
    }

    assert validate_parameter_schema(schema) == []


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


def _deep_object_schema(depth: int) -> dict:
    schema: dict = {"type": "string"}
    for _ in range(depth):
        schema = {"type": "object", "properties": {"x": schema}}
    return schema


def _deep_object_value(depth: int, leaf: object) -> object:
    value: object = leaf
    for _ in range(depth):
        value = {"x": value}
    return value


def test_validate_parameters_accepts_deep_nested_matching_values():
    depth = 1500
    schema = _deep_object_schema(depth)
    parameters = _deep_object_value(depth, "ok")

    assert validate_parameters(parameters, schema) == []


def test_validate_parameters_reports_deep_nested_type_failures():
    depth = 1500
    schema = _deep_object_schema(depth)
    parameters = _deep_object_value(depth, 1)

    findings = validate_parameters(parameters, schema)

    assert findings == [
        {
            "path": "$" + (".x" * depth),
            "rule": "type",
            "message": "Expected string.",
        }
    ]


def test_validate_parameters_accepts_deep_array_item_chain():
    schema: dict = {"type": "string"}
    for _ in range(1500):
        schema = {"type": "array", "items": schema}
    parameters: object = "ok"
    for _ in range(1500):
        parameters = [parameters]

    assert validate_parameters(parameters, schema) == []
