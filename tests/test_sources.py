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
