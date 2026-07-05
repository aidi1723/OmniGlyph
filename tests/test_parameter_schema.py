from omniglyph.parameter_schema import validate_parameters


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
