"""Tests for tray mode that do not need a real desktop.

The global hotkey and the tray icon itself cannot be tested here
(no desktop session); they must be tested by hand on Windows/macOS/
Linux. What is tested here: the tray icon image builds, the hotkey
settings are sane, and importing the tray module never pulls in
pystray/pynput at import time (so `klf` works without tray deps).
"""

import sys

import pytest

from keylayoutfixer.config import load_config


def test_tray_module_imports_without_tray_dependencies():
    # pystray/pynput/pyperclip are NOT installed in this environment.
    for name in ("pystray", "pynput", "pyperclip"):
        assert name not in sys.modules
    import keylayoutfixer.tray  # noqa: F401

    assert "pystray" not in sys.modules
    assert "pynput" not in sys.modules


def test_icon_image_builds():
    pil = pytest.importorskip("PIL")
    from keylayoutfixer.tray import create_icon_image

    image = create_icon_image()
    assert image.size == (64, 64)
    assert image.mode == "RGBA"


def test_default_hotkeys_differ():
    config = load_config()
    assert config["convert_hotkey"] != config["undo_hotkey"]
    assert config["convert_hotkey"] == "<ctrl>+<shift>+k"
    assert config["undo_hotkey"] == "<ctrl>+<shift>+z"


def test_tray_run_fails_clearly_without_dependencies(monkeypatch, tmp_path):
    # run_tray must explain what to install instead of crashing with an
    # ImportError traceback when the tray extras are missing.
    monkeypatch.setenv("KEYLAYOUTFIXER_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("KEYLAYOUTFIXER_DATA_DIR", str(tmp_path / "data"))
    from keylayoutfixer.tray import run_tray

    with pytest.raises(RuntimeError, match="keylayoutfixer\\[tray\\]"):
        run_tray()
