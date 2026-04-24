import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlretrieve


@dataclass(frozen=True)
class SourceArtifact:
    path: Path
    source_url: str
    source_version: str
    sha256: str
    license: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_local_source(path: Path, source_url: str, source_version: str, license: str) -> SourceArtifact:
    return SourceArtifact(
        path=path,
        source_url=source_url,
        source_version=source_version,
        sha256=sha256_file(path),
        license=license,
    )


def download_source(url: str, destination: Path, source_version: str, license: str) -> SourceArtifact:
    destination.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(url, destination)
    return register_local_source(destination, url, source_version, license)
