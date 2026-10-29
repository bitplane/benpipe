"""Exercise maintenance scripts in isolated directories with stubbed commands."""

import os
import subprocess
import sys
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


@pytest.mark.parametrize("failure", ["", "wheel-version", "sdist-version", "build", "check"])
def test_release_builds_and_validates_only_fresh_artifacts(script_workspace, failure):
    (script_workspace / "pyproject.toml").write_text('version = "0.1.1"\n')
    (script_workspace / "dist").mkdir()
    stale = script_workspace / "dist/stale.whl"
    stale.write_text("must not upload")
    command(script_workspace, "git", "echo 0.1.1\n")
    command(script_workspace, "python3", 'exec "$REVIEW_PYTHON" "$PWD/fake_python.py" "$@"\n')
    (script_workspace / "fake_python.py").write_text(r"""import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

args = sys.argv[1:]
failure = os.environ["REVIEW_FAILURE"]
if args[:2] == ["-m", "build"]:
    if failure == "build":
        sys.exit(7)
    directory = Path(args[args.index("--outdir") + 1])
    for kind in ("wheel", "sdist"):
        version = "0.1.0" if failure == kind + "-version" else "0.1.1"
        metadata = f"Name: benpipe\nVersion: {version}\n".encode()
        if kind == "wheel":
            with zipfile.ZipFile(directory / "benpipe-0.1.1-py3-none-any.whl", "w") as archive:
                archive.writestr("benpipe-0.1.1.dist-info/METADATA", metadata)
        else:
            with tarfile.open(directory / "benpipe-0.1.1.tar.gz", "w:gz") as archive:
                member = tarfile.TarInfo("benpipe-0.1.1/PKG-INFO")
                member.size = len(metadata)
                archive.addfile(member, io.BytesIO(metadata))
elif args[:3] == ["-m", "twine", "check"]:
    sys.exit(8 if failure == "check" else 0)
elif args[:3] == ["-m", "twine", "upload"]:
    Path("upload.json").write_text(json.dumps(args[3:]))
else:
    sys.exit(subprocess.run([sys.executable, *args], check=False).returncode)
""")
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/release.sh"), "benpipe"],
        cwd=script_workspace,
        env={**os.environ, "REVIEW_PYTHON": sys.executable, "REVIEW_FAILURE": failure, "PYPI_TOKEN": "fake-test-token"},
        capture_output=True,
        text=True,
        check=False,
    )
    upload = script_workspace / "upload.json"
    if failure:
        assert result.returncode != 0
        assert not upload.exists()
    else:
        assert result.returncode == 0, result.stderr
        assert "stale.whl" not in upload.read_text()
        assert "benpipe-0.1.1-py3-none-any.whl" in upload.read_text()
        assert "benpipe-0.1.1.tar.gz" in upload.read_text()
    assert stale.exists()
    assert list((script_workspace / "dist").iterdir()) == [stale]
