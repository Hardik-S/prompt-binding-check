# prompt-binding-check

An offline Python CLI that checks whether a UTF-8 template's variable references and a UTF-8 JSON bindings object cover one another. It reports counts and opaque positions only. It never renders the template, prints names or values, or calls a model or network service.

## Install and run

Requires Python 3.10 or newer. From a source checkout:

```console
python -m pip install .
prompt-binding-check TEMPLATE.txt BINDINGS.json
```

The installed command is registered through Python package metadata and resolves into the environment's scripts directory. For example, check the synthetic sample (which intentionally has one unused binding):

```console
prompt-binding-check examples/template.txt examples/bindings.json
```

## Input grammar

The only dollar forms are `${NAME}` and `$$`. Names are ASCII identifiers matching `[A-Za-z_][A-Za-z0-9_]*`. `$$` consumes a literal dollar and is never rescanned. Thus `$${X}` has no reference, while `$$${X}` contains a literal dollar followed by a reference. A bare `$`, `$NAME`, or malformed `${...}` is invalid. Other characters, including braces, newlines, Unicode text, and empty strings, are unrestricted.

The bindings file must be a strict UTF-8 JSON object whose keys follow the same name rule and whose values are strings. Duplicate keys, invalid names, non-string values, non-finite JSON numbers, malformed JSON, and invalid UTF-8 are rejected. Empty objects and empty string values are valid. Matching is case-sensitive; there is no normalization.

Distinct template variables are numbered from one in first-appearance order. Bindings are numbered from one in JSON insertion order. Repeated references share an index. A missing index identifies a referenced variable position; an unused index identifies a binding position. No names or source content are included in output.

## Result and exit status

For valid inputs, stdout contains exactly one compact JSON object and newline:

```json
{"status":"matched","variable_count":2,"binding_count":2,"missing_variable_indices":[],"unused_binding_indices":[]}
```

`matched` exits 0. Any missing or unused binding yields `binding_issues` and exit 1. Invalid files or argument lists yield only `{"status":"invalid_input"}` and exit 2, with empty stderr. `-h` and `--help` exit 0 with usage text. Both input files are read and parsed before a result is emitted, so invalid input never produces a partial report. OS errors and parser exceptions are intentionally not displayed.

## Scope

This is a local coverage check. It does not interpolate values, implement Python `Template` or Jinja, provide defaults, inspect secrets, or establish prompt safety or quality. It accepts no model or network configuration. Memory use grows with input size. The package has no runtime dependencies.

Run the tests with `python -m pytest`.
