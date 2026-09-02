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
