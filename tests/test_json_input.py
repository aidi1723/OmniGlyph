import math

import pytest

from omniglyph.json_input import ensure_finite_json, parse_strict_json


@pytest.mark.parametrize("text", ['NaN', 'Infinity', '-Infinity', '{"amount": 1e999}'])
def test_parse_strict_json_rejects_nonfinite_numbers(text):
    with pytest.raises(ValueError):
        parse_strict_json(text)


def test_ensure_finite_json_rejects_nested_nonfinite_value():
    with pytest.raises(ValueError, match=r"\$\.items\[1\]"):
        ensure_finite_json({"items": [1, math.nan]})
