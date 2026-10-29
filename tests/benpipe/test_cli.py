import subprocess
import sys


def run_benpipe(input_data: bytes, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-m", "benpipe", *arguments],
        input=input_data,
        capture_output=True,
        check=False,
    )


def test_automatic_json_conversion_does_not_mix_diagnostics_into_output():
    result = run_benpipe(b'{"x":"y"}')

    assert result.returncode == 0
    assert result.stdout == b"d1:x1:ye"
    assert result.stderr == b""


def test_failed_automatic_conversion_returns_failure():
    result = run_benpipe(b"invalid")

    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr.startswith(b"Conversion failed:")


def test_explicit_conversion_modes_are_mutually_exclusive():
    result = run_benpipe(b"", "--to-json", "--to-bencode")

    assert result.returncode == 2
    assert result.stdout == b""
    assert b"not allowed with argument" in result.stderr


def test_explicit_json_conversion():
    result = run_benpipe(b"d1:ai1ee", "--to-json")

    assert result.returncode == 0
    assert result.stdout == b'{\n    "a": 1\n}'
    assert result.stderr == b""


def test_explicit_bencode_conversion():
    result = run_benpipe(b'{"a":1}', "--to-bencode")

    assert result.returncode == 0
    assert result.stdout == b"d1:ai1ee"
    assert result.stderr == b""


def test_failed_explicit_conversion_has_no_traceback():
    result = run_benpipe(b"invalid", "--to-json")

    assert result.returncode == 1
    assert result.stdout == b""
    assert result.stderr.startswith(b"Conversion failed:")
    assert b"Traceback" not in result.stderr


def test_json_input_is_utf8_regardless_of_stdin_encoding(monkeypatch):
    monkeypatch.setenv("PYTHONIOENCODING", "latin-1")
    for arguments in [(), ("--to-bencode",)]:
        result = run_benpipe('"é"'.encode(), *arguments)
        assert result.returncode == 0
        assert result.stdout == b"2:\xc3\xa9"
        assert result.stderr == b""


def test_excessive_nesting_is_a_controlled_conversion_error():
    for depth in (101, 600, 2000):
        for data, flag in [
            (b"l" * depth + b"i1e" + b"e" * depth, "--to-json"),
            (b"[" * depth + b"1" + b"]" * depth, "--to-bencode"),
        ]:
            for arguments in [(), (flag,)]:
                result = run_benpipe(data, *arguments)
                assert result.returncode == 1
                assert result.stdout == b""
                assert b"Maximum nesting depth of 100 exceeded" in result.stderr
                assert b"Traceback" not in result.stderr
