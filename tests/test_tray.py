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
    #
    # Simulate the missing dependencies even when they ARE installed
    # (CI installs `.[dev,tray]`, so the old version of this test saw
    # the real pystray/pynput and went past the import guard: on
    # headless Linux it died with an Xlib DisplayNameError, and on
    # Windows/macOS it started the tray event loop and hung until the
    # 6h job timeout). Setting the sys.modules entries to None makes
    # the lazy imports inside run_tray() raise ImportError.
    for name in ("pystray", "pynput", "pyperclip"):
        monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.setenv("KEYLAYOUTFIXER_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("KEYLAYOUTFIXER_DATA_DIR", str(tmp_path / "data"))
    from keylayoutfixer.tray import run_tray

    with pytest.raises(RuntimeError, match="keylayoutfixer\\[tray\\]"):
        run_tray()


def _fake_clipboard(monkeypatch, selection):
    """Fake pyperclip + pynput.keyboard for TrayApp tests (no desktop).

    The fake clipboard starts with stale text. Pressing Ctrl+C through
    the fake Controller copies ``selection`` into it, the way a real
    app copies the user's selected text; with no selection the
    clipboard stays as cleared.
    """
    import types

    store = {"text": "stale clipboard"}
    selection_box = {"text": selection}

    pyperclip = types.ModuleType("pyperclip")
    pyperclip.paste = lambda: store["text"]
    pyperclip.copy = lambda text: store.__setitem__("text", text)
    monkeypatch.setitem(sys.modules, "pyperclip", pyperclip)

    keys_pressed = []

    class Key:
        ctrl = "ctrl"
        cmd = "cmd"

    class Controller:
        def __init__(self):
            self.held = set()

        def press(self, key):
            keys_pressed.append(("press", key))
            self.held.add(key)
            if key == "c" and ("ctrl" in self.held or "cmd" in self.held):
                store["text"] = selection_box["text"]

        def release(self, key):
            keys_pressed.append(("release", key))
            self.held.discard(key)

    keyboard = types.ModuleType("pynput.keyboard")
    keyboard.Controller = Controller
    keyboard.Key = Key
    pynput = types.ModuleType("pynput")
    pynput.keyboard = keyboard
    monkeypatch.setitem(sys.modules, "pynput", pynput)
    monkeypatch.setitem(sys.modules, "pynput.keyboard", keyboard)
    return store, keys_pressed


def test_convert_copies_selection_first(monkeypatch):
    """Regression test: the hotkey must copy the current selection.

    The original code converted whatever stale text was already in the
    clipboard, so pressing the hotkey on a fresh selection did nothing
    useful (or converted the wrong text).
    """
    from keylayoutfixer.tray import TrayApp

    store, keys = _fake_clipboard(monkeypatch, selection="sghl")
    app = TrayApp({"keep_history": False, "max_history": 200})
    app.convert_clipboard()

    assert store["text"] == "سلام"  # converted selection, pasted back
    assert app.last == ("sghl", "سلام")
    assert ("press", "ctrl") in keys  # Ctrl+C copied, Ctrl+V pasted
    assert keys.count(("press", "c")) == 1
    assert keys.count(("press", "v")) == 1


def test_convert_with_no_selection_restores_clipboard(monkeypatch):
    from keylayoutfixer.tray import TrayApp

    store, _keys = _fake_clipboard(monkeypatch, selection="")
    app = TrayApp({"keep_history": False, "max_history": 200})
    app.convert_clipboard()

    assert store["text"] == "stale clipboard"
    assert app.last is None


def test_copy_paste_use_cmd_on_macos(monkeypatch):
    from keylayoutfixer.tray import TrayApp

    store, keys = _fake_clipboard(monkeypatch, selection="sghl")
    monkeypatch.setattr(sys, "platform", "darwin")
    app = TrayApp({"keep_history": False, "max_history": 200})
    app.convert_clipboard()

    assert ("press", "cmd") in keys
    assert ("press", "ctrl") not in keys
    assert store["text"] == "سلام"
