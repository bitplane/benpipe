"""Verify freshly built artifacts before publishing them."""

import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path


def check_artifacts(directory, name, version):
    artifacts = list(Path(directory).iterdir())
    wheels = [path for path in artifacts if path.suffix == ".whl"]
    sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
    if len(artifacts) != 2 or len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("Expected exactly one wheel and one source distribution")
    with zipfile.ZipFile(wheels[0]) as archive:
        members = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(members) != 1:
            raise ValueError("Expected one wheel metadata file")
        wheel_metadata = archive.read(members[0])
    with tarfile.open(sdists[0]) as archive:
        members = [
            member
            for member in archive.getmembers()
            if member.name.count("/") == 1 and member.name.endswith("/PKG-INFO") and member.isfile()
        ]
        if len(members) != 1:
            raise ValueError("Expected one source distribution metadata file")
        with archive.extractfile(members[0]) as metadata_file:
            sdist_metadata = metadata_file.read()
    for artifact, raw_metadata in [(wheels[0], wheel_metadata), (sdists[0], sdist_metadata)]:
        metadata = BytesParser().parsebytes(raw_metadata)
        if metadata["Name"] != name or metadata["Version"] != version:
            raise ValueError(f"Artifact metadata does not match {name} {version}: {artifact.name}")


if __name__ == "__main__":
    check_artifacts(*sys.argv[1:])
