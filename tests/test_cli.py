"""Tests for the terminal CLI (pipe mode, --text, history subcommand).

The CLI is exercised as a subprocess with KEYLAYOUTFIXER_DATA_DIR and
KEYLAYOUTFIXER_CONFIG_DIR pointed at a temporary directory, so tests
never touch the user's real history or settings.
"""

import json
import os
import subprocess
import sys

import pytest

from keylayoutfixer.config import DATA_DIR_ENV, CONFIG_DIR_ENV

PYTHON = sys.executable


def run_cli(args, input_text=None, tmp_path=None):
    env = dict(os.environ)
    if tmp_path is not None:
        env[DATA_DIR_ENV] = str(tmp_path / "data")
        env[CONFIG_DIR_ENV] = str(tmp_path / "config")
    return subprocess.run(
        [PYTHON, "-m", "keylayoutfixer", *args],
        input=input_text,
        capture_output=True,
        text=True,
        # The harness always speaks UTF-8 to the child, whatever the
        # parent's locale is; the child itself must also handle a
        # non-UTF-8 console (see test_cli_works_when_console_encoding_is_not_utf8).
        encoding="utf-8",
        env=env,
        timeout=30,
    )


def test_one_shot_text_flag(tmp_path):
    result = run_cli(["--text", "sghl", "--no-history"], tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "سلام"


def test_one_shot_positional(tmp_path):
    result = run_cli(["سلام", "--no-history"], tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "sghl"


def test_reverse_flag(tmp_path):
    # Auto-detect would convert sghl -> سلام; --reverse keeps it as-is
    # (there is nothing to map back: s/g/h/l are not Persian keys).
    result = run_cli(["--text", "sghl", "--reverse", "--no-history"], tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "sghl"


def test_force_direction_to(tmp_path):
    result = run_cli(["--text", "sghl", "--to", "fa", "--no-history"], tmp_path=tmp_path)
    assert result.stdout.strip() == "سلام"
    result = run_cli(["--text", "sghl", "--to", "en", "--no-history"], tmp_path=tmp_path)
    assert result.stdout.strip() == "sghl"


def test_pipe_mode(tmp_path):
    result = run_cli([], input_text="sghl\nسلام\n", tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["سلام", "sghl"]


def test_pipe_mode_keeps_empty_lines(tmp_path):
    result = run_cli(["--no-history"], input_text="sghl\n\nسلام\n", tmp_path=tmp_path)
    assert result.stdout.splitlines() == ["سلام", "", "sghl"]


def test_empty_stdin_exits_cleanly(tmp_path):
    result = run_cli([], input_text="", tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout == ""


def test_history_records_and_lists(tmp_path):
    run_cli(["--text", "sghl"], tmp_path=tmp_path)
    run_cli(["--text", "سلام"], tmp_path=tmp_path)
    result = run_cli(["history"], tmp_path=tmp_path)
    assert result.returncode == 0
    assert "سلام" in result.stdout
    assert "sghl" in result.stdout
    history_file = tmp_path / "data" / "history.json"
    assert history_file.exists()
    stored = json.loads(history_file.read_text(encoding="utf-8"))
    assert len(stored) == 2
    assert stored[0]["original"] == "sghl"
    assert stored[0]["converted"] == "سلام"


def test_history_search_and_export(tmp_path):
    run_cli(["--text", "sghl"], tmp_path=tmp_path)
    run_cli(["--text", "hello"], tmp_path=tmp_path)
    result = run_cli(["history", "--search", "سلام"], tmp_path=tmp_path)
    assert "سلام" in result.stdout
    assert "hello" not in result.stdout
    export = tmp_path / "out.csv"
    result = run_cli(["history", "--export", str(export)], tmp_path=tmp_path)
    assert result.returncode == 0
    assert export.exists()
    content = export.read_text(encoding="utf-8-sig")
    assert "Original,Converted" in content
    assert "سلام" in content


def test_history_clear(tmp_path):
    run_cli(["--text", "sghl"], tmp_path=tmp_path)
    result = run_cli(["history", "--clear", "--yes"], tmp_path=tmp_path)
    assert result.returncode == 0
    result = run_cli(["history"], tmp_path=tmp_path)
    assert "No history yet" in result.stdout


def test_pipe_mode_multiple_lines(tmp_path):
    result = run_cli([], input_text="sghl\nhello\n", tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["سلام", "اثممخ"]


def test_cli_works_when_console_encoding_is_not_utf8(monkeypatch, tmp_path):
    # Regression test for the Windows CI failures: on Windows the console
    # code page is cp1252, which cannot encode Persian characters. The CLI
    # must reconfigure its own streams to UTF-8 instead of crashing with
    # UnicodeEncodeError when printing سلام (or reading it from a pipe).
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    result = run_cli(["--text", "sghl", "--no-history"], tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == "سلام"
    result = run_cli([], input_text="sghl\nسلام\n", tmp_path=tmp_path)
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["سلام", "sghl"]


def test_version_flag(tmp_path):
    result = run_cli(["--version"], tmp_path=tmp_path)
    assert result.returncode == 0
    assert "1.0.0" in result.stdout
