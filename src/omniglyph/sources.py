import hashlib
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


@dataclass(frozen=True)
class SourceArtifact:
    path: Path
    source_url: str
    source_version: str
    sha256: str
    license: str


@dataclass(frozen=True)
class SourceManifest:
    source_url: str
    source_version: str
    license: str
    expected_sha256: str


class SourceIntegrityError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_sha256(path: Path, expected_sha256: str | None) -> str:
    actual_sha256 = sha256_file(path)
    if expected_sha256 is not None and actual_sha256.casefold() != expected_sha256.casefold():
        raise SourceIntegrityError(
            f"SHA-256 mismatch for {path}: expected {expected_sha256}, got {actual_sha256}"
        )
    return actual_sha256


def register_local_source(
    path: Path,
    source_url: str,
    source_version: str,
    license: str,
    expected_sha256: str | None = None,
) -> SourceArtifact:
    actual_sha256 = validate_sha256(path, expected_sha256)
    return SourceArtifact(
        path=path,
        source_url=source_url,
        source_version=source_version,
        sha256=actual_sha256,
        license=license,
    )


def download_source(
    url: str,
    destination: Path,
    source_version: str,
    license: str,
    expected_sha256: str | None = None,
) -> SourceArtifact:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            with urlopen(url, timeout=30) as response:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    file.write(chunk)
        actual_sha256 = validate_sha256(temporary_path, expected_sha256)
        temporary_path.replace(destination)
        return SourceArtifact(
            path=destination,
            source_url=url,
            source_version=source_version,
            sha256=actual_sha256,
            license=license,
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
