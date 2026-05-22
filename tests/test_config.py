import importlib

import omniglyph.config as config


def test_settings_can_be_overridden_with_data_dir_environment(monkeypatch, tmp_path):
    data_dir = tmp_path / "omniglyph-data"
    monkeypatch.setenv("OMNIGLYPH_DATA_DIR", str(data_dir))

    reloaded = importlib.reload(config)

    assert reloaded.settings.data_dir == data_dir
    assert reloaded.settings.raw_dir == data_dir / "raw"
    assert reloaded.settings.sqlite_path == data_dir / "omniglyph.sqlite3"
    assert reloaded.settings.lexicon_pack_root is None

    monkeypatch.delenv("OMNIGLYPH_DATA_DIR")
    importlib.reload(config)


def test_settings_can_limit_lexicon_pack_root(monkeypatch, tmp_path):
    pack_root = tmp_path / "packs"
    monkeypatch.setenv("OMNIGLYPH_LEXICON_PACK_ROOT", str(pack_root))

    reloaded = importlib.reload(config)

    assert reloaded.settings.lexicon_pack_root == pack_root

    monkeypatch.delenv("OMNIGLYPH_LEXICON_PACK_ROOT")
    importlib.reload(config)
