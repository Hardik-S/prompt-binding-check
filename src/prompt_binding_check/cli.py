"""Command-line interface for prompt-binding-check."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import InputError, compare, parse_bindings, parse_template


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError


def _read_utf8(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="strict")


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(
        prog="prompt-binding-check",
        description="Check template and binding coverage without rendering content.",
    )
    parser.add_argument("template", help="UTF-8 template text file")
    parser.add_argument("bindings", help="UTF-8 JSON bindings file")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code == 0:
            return 0
        sys.stdout.buffer.write(b'{"status":"invalid_input"}\n')
        return 2
    except ValueError:
        sys.stdout.buffer.write(b'{"status":"invalid_input"}\n')
        return 2

    errors = False
    template = bindings = None
    try:
        template_text = _read_utf8(args.template)
    except (OSError, UnicodeError, ValueError):
        errors = True
    else:
        try:
            template = parse_template(template_text)
        except InputError:
            errors = True
    try:
        binding_text = _read_utf8(args.bindings)
    except (OSError, UnicodeError, ValueError):
        errors = True
    else:
        try:
            bindings = parse_bindings(binding_text)
        except InputError:
            errors = True
    if errors or template is None or bindings is None:
        sys.stdout.buffer.write(b'{"status":"invalid_input"}\n')
        return 2
    result = compare(template, bindings)
    sys.stdout.buffer.write((json.dumps(result, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii"))
    return 1 if result["status"] == "binding_issues" else 0


if __name__ == "__main__":
    raise SystemExit(main())
