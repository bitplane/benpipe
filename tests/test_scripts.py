"""Exercise maintenance scripts in isolated directories with stubbed commands."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def script_workspace(tmp_path):
    bin_dir = tmp_path / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "activate").write_text('export PATH="$PWD/.venv/bin:$PATH"\n')
    return tmp_path


def command(workspace, name, body):
    path = workspace / ".venv" / "bin" / name
    path.write_text("#!/bin/bash\n" + body)
    path.chmod(0o755)


@pytest.mark.parametrize("status", [0, 1, 7])
def test_coverage_preserves_test_status_and_report(script_workspace, status):
    command(script_workspace, "pytest", f"echo 'Missing coverage summary'\nexit {status}\n")
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/coverage.sh"), "benpipe"],
        cwd=script_workspace,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == status
    assert "Missing coverage summary" in result.stdout
    assert (script_workspace / "htmlcov/missing_coverage.txt").read_text() == "Missing coverage summary\n"
