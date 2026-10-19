import json
import subprocess
import sys
import sysconfig
from pathlib import Path
from importlib.metadata import version


def run_cli(tmp_path, template=b"${A}", bindings=b'{"A":"value"}', *args):
    t = tmp_path / "template.txt"
    b = tmp_path / "bindings.json"
    t.write_bytes(template)
    b.write_bytes(bindings)
    p = subprocess.run([sys.executable, "-m", "prompt_binding_check.cli", str(t), str(b), *args], capture_output=True)
    return p.returncode, p.stdout, p.stderr


def test_matched_success_has_only_contract_output(tmp_path):
    code, out, err = run_cli(tmp_path, "hi ${A} 🧪".encode(), '{"A":"TOP SECRET"}'.encode())
    assert code == 0 and err == b""
    assert json.loads(out) == {"status":"matched", "variable_count":1, "binding_count":1,
                              "missing_variable_indices":[], "unused_binding_indices":[]}
    assert b"SECRET" not in out


def test_issues_exit_one(tmp_path):
    code, out, err = run_cli(tmp_path, b"${A}${B}", b'{"X":"secret"}')
    assert code == 1 and err == b""
    assert json.loads(out)["missing_variable_indices"] == [1, 2]
    assert json.loads(out)["unused_binding_indices"] == [1]
    assert b"A" not in out and b"secret" not in out


def test_both_files_are_observed_even_when_template_invalid(tmp_path, monkeypatch):
    t, b = tmp_path / "t", tmp_path / "b"
    t.write_text("$", encoding="utf-8")
    b.write_text('{"A":1}', encoding="utf-8")
    observed = []
    from prompt_binding_check import cli
    original = cli._read_utf8
    def watch(path):
        observed.append(path)
        return original(path)
    monkeypatch.setattr(cli, "_read_utf8", watch)
    assert cli.main([str(t), str(b)]) == 2
    assert observed == [str(t), str(b)]


def test_invalid_files_are_opaque_and_no_partial_output(tmp_path):
    code, out, err = run_cli(tmp_path, b"valid ${A}", b'{"A":1}')
    assert (code, out, err) == (2, b'{"status":"invalid_input"}\n', b"")
    code, out, err = run_cli(tmp_path, b"${PRIVATE}", b'{"PRIVATE":"sensitive"}', "unexpected")
    assert (code, out, err) == (2, b'{"status":"invalid_input"}\n', b"")


def test_bad_utf8_and_missing_file_are_opaque(tmp_path):
    code, out, err = run_cli(tmp_path, b"\xff", b"{}")
    assert (code, out, err) == (2, b'{"status":"invalid_input"}\n', b"")
    code, out, err = run_cli(tmp_path, b"${A}", b"{}")
    assert code == 1
    (tmp_path / "template.txt").unlink()
    p = subprocess.run([sys.executable, "-m", "prompt_binding_check.cli", str(tmp_path / "template.txt"), str(tmp_path / "bindings.json")], capture_output=True)
    assert (p.returncode, p.stdout, p.stderr) == (2, b'{"status":"invalid_input"}\n', b"")


def test_help_and_missing_argv():
    help_run = subprocess.run([sys.executable, "-m", "prompt_binding_check.cli", "--help"], capture_output=True)
    assert help_run.returncode == 0 and b"without rendering" in help_run.stdout and help_run.stderr == b""
    bad = subprocess.run([sys.executable, "-m", "prompt_binding_check.cli"], capture_output=True)
    assert (bad.returncode, bad.stdout, bad.stderr) == (2, b'{"status":"invalid_input"}\n', b"")


def test_installed_console_entrypoint_exists_in_scripts_dir():
    command = "prompt-binding-check.exe" if sys.platform == "win32" else "prompt-binding-check"
    script_dirs = [Path(sysconfig.get_path("scripts"))]
    if sys.platform == "win32" and sys.prefix == sys.base_prefix:
        script_dirs.append(Path(sysconfig.get_path("scripts", scheme="nt_user")))
    executable = next((directory / command for directory in script_dirs if (directory / command).is_file()), None)
    assert executable is not None
    help_run = subprocess.run([str(executable), "--help"], capture_output=True)
    assert help_run.returncode == 0 and help_run.stderr == b""
    assert version("prompt-binding-check") == "0.1.0"


def test_installed_console_entrypoint_exit_contract(tmp_path):
    command = "prompt-binding-check.exe" if sys.platform == "win32" else "prompt-binding-check"
    script_dirs = [Path(sysconfig.get_path("scripts"))]
    if sys.platform == "win32" and sys.prefix == sys.base_prefix:
        script_dirs.append(Path(sysconfig.get_path("scripts", scheme="nt_user")))
    executable = next(directory / command for directory in script_dirs if (directory / command).is_file())
    template, bindings = tmp_path / "template.txt", tmp_path / "bindings.json"
    template.write_text("${A}", encoding="utf-8")
    bindings.write_text('{"A":"synthetic"}', encoding="utf-8")
    matched = subprocess.run([str(executable), str(template), str(bindings)], capture_output=True)
    assert matched.returncode == 0 and matched.stderr == b""
    bindings.write_text("{}", encoding="utf-8")
    issue = subprocess.run([str(executable), str(template), str(bindings)], capture_output=True)
    assert issue.returncode == 1 and issue.stderr == b""
    invalid = subprocess.run([str(executable), str(template)], capture_output=True)
    assert (invalid.returncode, invalid.stdout, invalid.stderr) == (2, b'{"status":"invalid_input"}\n', b"")
