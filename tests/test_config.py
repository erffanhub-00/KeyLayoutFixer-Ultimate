"""Tests for settings: defaults, corrupt files, hotkey normalization."""

from keylayoutfixer.config import (
    DEFAULT_CONFIG,
    get_config_dir,
    get_data_dir,
    load_config,
    normalize_hotkey,
    save_config,
)


def test_defaults_when_no_file(monkeypatch, tmp_path):
    monkeypatch.setenv("KEYLAYOUTFIXER_CONFIG_DIR", str(tmp_path / "config"))
    config = load_config()
    assert config == DEFAULT_CONFIG


def test_save_and_load_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("KEYLAYOUTFIXER_CONFIG_DIR", str(tmp_path / "config"))
    config = load_config()
    config["convert_hotkey"] = "<ctrl>+<alt>+k"
    config["keep_history"] = False
    save_config(config)
    assert load_config() == config


def test_corrupt_config_falls_back_to_defaults(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.json").write_text("{broken", encoding="utf-8")
    monkeypatch.setenv("KEYLAYOUTFIXER_CONFIG_DIR", str(config_dir))
    assert load_config() == DEFAULT_CONFIG
    assert (config_dir / "config.json.corrupt").exists()


def test_unknown_keys_are_ignored(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        '{"convert_hotkey": "<ctrl>+<shift>+j", "bogus": 1}', encoding="utf-8"
    )
    monkeypatch.setenv("KEYLAYOUTFIXER_CONFIG_DIR", str(config_dir))
    config = load_config()
    assert config["convert_hotkey"] == "<ctrl>+<shift>+j"
    assert "bogus" not in config


def test_normalize_hotkey_pynput_format():
    assert normalize_hotkey("<ctrl>+<shift>+k") == "<ctrl>+<shift>+k"
    assert normalize_hotkey("<Ctrl>+<Shift>+K") == "<ctrl>+<shift>+k"


def test_normalize_hotkey_old_ahk_format():
    # Users migrating from the AHK version know ^+k / ^+z.
    assert normalize_hotkey("^+k") == "<ctrl>+<shift>+k"
    assert normalize_hotkey("^+z") == "<ctrl>+<shift>+z"
    assert normalize_hotkey("^!z") == "<ctrl>+<alt>+z"
    assert normalize_hotkey("#+k") == "<cmd>+<shift>+k"
    assert normalize_hotkey("") == ""


def test_env_overrides_for_dirs(monkeypatch, tmp_path):
    monkeypatch.setenv("KEYLAYOUTFIXER_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("KEYLAYOUTFIXER_DATA_DIR", str(tmp_path / "data"))
    assert get_config_dir() == tmp_path / "cfg"
    assert get_data_dir() == tmp_path / "data"
