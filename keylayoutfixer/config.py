"""Settings for KeyLayoutFixer.

Settings live in a JSON file (``config.json`` in the config directory).
A corrupt or missing file falls back to the defaults instead of
crashing; a corrupt file is backed up next to the original.
"""

import json
import os
import re
from pathlib import Path

APP_NAME = "keylayoutfixer"

DEFAULT_CONFIG = {
    # pynput format: <ctrl>, <shift>, <alt>, <cmd> joined with "+".
    # The old AHK hotkeys (Ctrl+Shift+K / Ctrl+Shift+Z) are kept.
    "convert_hotkey": "<ctrl>+<shift>+k",
    "undo_hotkey": "<ctrl>+<shift>+z",
    "keep_history": True,
    "max_history": 200,
}

# Env overrides (used by tests and by users who want a custom location).
CONFIG_DIR_ENV = "KEYLAYOUTFIXER_CONFIG_DIR"
DATA_DIR_ENV = "KEYLAYOUTFIXER_DATA_DIR"

# Old AHK-style hotkey prefixes, accepted for users migrating from the
# Windows-only version ("^+k" -> "<ctrl>+<shift>+k").
_AHK_PREFIXES = {"^": "<ctrl>", "+": "<shift>", "!": "<alt>", "#": "<cmd>"}


def get_config_dir():
    """Platform config directory (overridable with KEYLAYOUTFIXER_CONFIG_DIR)."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        return Path(override)
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", home))
        return base / "KeyLayoutFixer"
    if __import__("sys").platform == "darwin":
        return home / "Library" / "Application Support" / "KeyLayoutFixer"
    base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    return base / APP_NAME


def get_data_dir():
    """Platform data directory (overridable with KEYLAYOUTFIXER_DATA_DIR)."""
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override)
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", home))
        return base / "KeyLayoutFixer"
    if __import__("sys").platform == "darwin":
        return home / "Library" / "Application Support" / "KeyLayoutFixer"
    base = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return base / APP_NAME


def normalize_hotkey(hotkey):
    """Normalize a hotkey string to pynput ``<ctrl>+<shift>+k`` format.

    Accepts pynput format as-is and the old AHK format (``^+k``,
    ``^!z``, ``#+k``). Returns the normalized string, lowercased.
    """
    hotkey = (hotkey or "").strip().lower()
    if not hotkey:
        return ""
    if "<" in hotkey:
        # Already pynput format; just tidy the separators.
        parts = [p.strip() for p in hotkey.split("+") if p.strip()]
        return "+".join(parts)
    modifiers = []
    key = ""
    for ch in hotkey:
        if ch in _AHK_PREFIXES:
            modifiers.append(_AHK_PREFIXES[ch])
        else:
            key += ch
    if not key:
        return ""
    return "+".join(modifiers + [key])


def config_path():
    return get_config_dir() / "config.json"


def load_config():
    """Load settings, falling back to defaults on any problem."""
    path = config_path()
    config = dict(DEFAULT_CONFIG)
    if not path.exists():
        return config
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        backup = path.with_suffix(".json.corrupt")
        try:
            path.replace(backup)
        except OSError:
            pass
        return config
    if isinstance(stored, dict):
        for key, value in stored.items():
            if key in config:
                config[key] = value
    config["convert_hotkey"] = normalize_hotkey(config["convert_hotkey"])
    config["undo_hotkey"] = normalize_hotkey(config["undo_hotkey"])
    if not config["convert_hotkey"]:
        config["convert_hotkey"] = DEFAULT_CONFIG["convert_hotkey"]
    if not config["undo_hotkey"]:
        config["undo_hotkey"] = DEFAULT_CONFIG["undo_hotkey"]
    try:
        config["max_history"] = max(0, int(config["max_history"]))
    except (TypeError, ValueError):
        config["max_history"] = DEFAULT_CONFIG["max_history"]
    config["keep_history"] = bool(config["keep_history"])
    return config


def save_config(config):
    """Save settings atomically (temp file + rename)."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path
