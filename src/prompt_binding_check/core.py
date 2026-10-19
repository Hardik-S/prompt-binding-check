"""Strict template and JSON binding parsers; this module never renders values."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z", re.ASCII)


class InputError(ValueError):
    """An input file violates the frozen input grammar or schema."""


@dataclass(frozen=True)
class Template:
    names: tuple[str, ...]


@dataclass(frozen=True)
class Bindings:
    names: tuple[str, ...]


def parse_template(text: str) -> Template:
    """Parse references left-to-right, consuming escapes without rescanning."""
    order: list[str] = []
    seen: set[str] = set()
    i = 0
    while i < len(text):
        if text[i] != "$":
            i += 1
            continue
        if i + 1 < len(text) and text[i + 1] == "$":
            i += 2
            continue
        if i + 1 < len(text) and text[i + 1] == "{":
            end = text.find("}", i + 2)
            if end < 0:
                raise InputError
            name = text[i + 2 : end]
            if not _NAME.fullmatch(name):
                raise InputError
            if name not in seen:
                seen.add(name)
                order.append(name)
            i = end + 1
            continue
        raise InputError
    return Template(tuple(order))


def _reject_constant(_: str) -> Any:
    raise InputError


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError
        result[key] = value
    return result


def parse_bindings(text: str) -> Bindings:
    try:
        data = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (json.JSONDecodeError, UnicodeError, InputError, TypeError, ValueError) as exc:
        raise InputError from exc
    if not isinstance(data, dict):
        raise InputError
    for key, value in data.items():
        if not isinstance(key, str) or not _NAME.fullmatch(key) or not isinstance(value, str):
            raise InputError
    return Bindings(tuple(data.keys()))


def compare(template: Template, bindings: Bindings) -> dict[str, object]:
    binding_positions = {name: i for i, name in enumerate(bindings.names, 1)}
    template_positions = {name: i for i, name in enumerate(template.names, 1)}
    missing = [template_positions[n] for n in template.names if n not in binding_positions]
    unused = [i for i, name in enumerate(bindings.names, 1) if name not in template_positions]
    return {
        "status": "binding_issues" if missing or unused else "matched",
        "variable_count": len(template.names),
        "binding_count": len(bindings.names),
        "missing_variable_indices": missing,
        "unused_binding_indices": unused,
    }
