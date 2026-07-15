import hashlib

import pytest

import omniglyph.sources as sources


def test_register_local_source_accepts_matching_sha256(tmp_path):
    path = tmp_path / "UnicodeData.txt"
    path.write_text("0041;LATIN CAPITAL LETTER A\n", encoding="utf-8")
    expected_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

    artifact = sources.register_local_source(
        path,
        source_url="file://UnicodeData.txt",
        source_version="fixture",
        license="Unicode Terms of Use",
        expected_sha256=expected_sha256,
    )

    assert artifact.sha256 == expected_sha256


def test_register_local_source_rejects_mismatched_sha256(tmp_path):
    path = tmp_path / "UnicodeData.txt"
    path.write_text("0041;LATIN CAPITAL LETTER A\n", encoding="utf-8")

    source_integrity_error = getattr(sources, "SourceIntegrityError", AssertionError)

    with pytest.raises(source_integrity_error, match="SHA-256 mismatch"):
        sources.register_local_source(
            path,
            source_url="file://UnicodeData.txt",
            source_version="fixture",
            license="Unicode Terms of Use",
            expected_sha256="0" * 64,
        )


def test_download_source_validates_expected_sha256(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("U+94DD\tkMandarin\tlǚ\n", encoding="utf-8")
    expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    destination = tmp_path / "downloaded.txt"

    artifact = sources.download_source(
        source.as_uri(),
        destination,
        source_version="fixture",
        license="Unicode Terms of Use",
        expected_sha256=expected_sha256,
    )

    assert artifact.path == destination
    assert artifact.sha256 == expected_sha256


def test_download_source_hash_mismatch_preserves_existing_destination(tmp_path):
    source = tmp_path / "source.txt"
    source.write_bytes(b"untrusted")
    destination = tmp_path / "UnicodeData.txt"
    destination.write_bytes(b"known-good")

    with pytest.raises(sources.SourceIntegrityError, match="SHA-256 mismatch"):
        sources.download_source(
            source.as_uri(),
            destination,
            source_version="fixture",
            license="Unicode Terms of Use",
            expected_sha256="0" * 64,
        )

    assert destination.read_bytes() == b"known-good"
    assert sorted(tmp_path.glob(".UnicodeData.txt.*.tmp")) == []


def test_download_source_interruption_preserves_existing_destination(tmp_path, monkeypatch):
    destination = tmp_path / "UnicodeData.txt"
    destination.write_bytes(b"known-good")

    class FailingResponse:
        def __init__(self):
            self.read_count = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self, _size):
            self.read_count += 1
            if self.read_count == 1:
                return b"partial"
            raise OSError("download interrupted")

    monkeypatch.setattr(sources, "urlopen", lambda *_args, **_kwargs: FailingResponse())

    with pytest.raises(OSError, match="download interrupted"):
        sources.download_source(
            "https://example.invalid/UnicodeData.txt",
            destination,
            source_version="fixture",
            license="Unicode Terms of Use",
        )

    assert destination.read_bytes() == b"known-good"
    assert sorted(tmp_path.glob(".UnicodeData.txt.*.tmp")) == []
