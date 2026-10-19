import json

import pytest

from prompt_binding_check.core import InputError, compare, parse_bindings, parse_template


@pytest.mark.parametrize(("source", "names"), [
    ("", ()), ("plain {text}\n", ()), ("${A}-${B}-${A}", ("A", "B")),
    ("$${A}", ()), ("$$${A}", ("A",)), ("$$$$${A}", ("A",)),
    ("${a}${A}${a}", ("a", "A")), ("${_x}${x9}", ("_x", "x9")),
])
def test_template_grammar_and_order(source, names):
    assert parse_template(source).names == names


@pytest.mark.parametrize("source", ["$", "$name", "${}", "${1A}", "${a-b}", "${A", "${A${B}}", "${A}x$"])
def test_invalid_dollar_sequences(source):
    with pytest.raises(InputError):
        parse_template(source)


def test_bindings_schema_order_unicode_and_empty_values():
    assert parse_bindings('{"Z":"","A":"🧪","B":"x"}').names == ("Z", "A", "B")
    assert parse_bindings("{}").names == ()


@pytest.mark.parametrize("source", [
    '[]', 'null', '"x"', '{"A":1}', '{"bad-key":"x"}',
    '{"A":"x","A":"y"}', '{"A":NaN}', '{"A":Infinity}',
    '{bad}', '{"A":"x",}',
])
def test_invalid_bindings(source):
    with pytest.raises(InputError):
        parse_bindings(source)


def test_indices_are_first_appearance_and_insertion_order():
    result = compare(parse_template("${A}${B}${A}${C}"), parse_bindings('{"B":"","X":"","C":""}'))
    assert result == {
        "status": "binding_issues", "variable_count": 3, "binding_count": 3,
        "missing_variable_indices": [1], "unused_binding_indices": [2],
    }
