# KeyLayoutFixer

A cross-platform Persian/English keyboard layout converter — a terminal tool first, with a small tray app for converting text anywhere.

[![CI](https://github.com/erffanhub-00/KeyLayoutFixer-Ultimate/actions/workflows/ci.yml/badge.svg)](https://github.com/erffanhub-00/KeyLayoutFixer-Ultimate/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Typed `sghl` while the English layout was active? That was `سلام`. Select text anywhere, press `Ctrl+Shift+K`, and it is fixed. Works on Windows, macOS and Linux.

## Features

- **Two-way conversion** — English layout to Persian and back, with automatic direction detection (whichever script dominates wins)
- **Terminal tool** — interactive mode, pipe/stdin mode (`echo sghl | klf`), and one-shot `--text`
- **Tray mode** — `klf tray` puts a small icon in the taskbar/menu bar; the global hotkey converts the current selection in any app, and `Ctrl+Shift+Z` undoes it
- **History** — every conversion is saved as JSON, with search and CSV export (`klf history`)
- **Verified mapping** — the Persian/English key table is checked against ISIRI 9147 (the Iranian national standard), and converting twice returns the original text
- **No dependencies for the terminal tool** — the tray mode needs `pystray`, `pynput` and `pyperclip` (`pip install "keylayoutfixer[tray]"`)

## Quickstart

Requires Python 3.10 or later.

```bash
git clone https://github.com/erffanhub-00/KeyLayoutFixer-Ultimate.git
cd KeyLayoutFixer-Ultimate
pip install -e .

klf --text sghl
# سلام

klf --text سلام
# sghl
```

Tray mode (global hotkey in any app):

```bash
pip install -e ".[tray]"
klf tray
```

## Usage

### Terminal

```bash
klf                          # interactive: type text, Enter converts it
echo sghl | klf              # pipe mode: سلام
cat notes.txt | klf > fixed.txt
klf --text sghl              # one-shot: سلام
klf sghl                     # same, as a positional argument
klf --text سلام --to en      # force the direction: sghl
klf --text sghl --reverse    # convert in the opposite direction of auto-detect
klf --text sghl --no-history # do not record this conversion
```

### History

```bash
klf history                  # last 20 conversions, newest first
klf history --limit 0        # all of them
klf history --search سلام    # search original and converted text
klf history --export history.csv
klf history --clear          # asks for confirmation; --yes skips it
```

History lives in the platform data directory (`~/.local/share/keylayoutfixer/history.json` on Linux, `%APPDATA%/KeyLayoutFixer` on Windows, `~/Library/Application Support/KeyLayoutFixer` on macOS). Settings (`config.json`: hotkeys, history on/off, history size) live in the matching config directory. Both can be overridden with `KEYLAYOUTFIXER_DATA_DIR` and `KEYLAYOUTFIXER_CONFIG_DIR`.

### Tray

```bash
klf tray
```

Select text in any app and press `Ctrl+Shift+K` (configurable in `config.json`; the old AHK format `^+k` is accepted too). Press `Ctrl+Shift+Z` to undo. Right-click the tray icon for Convert, Undo, Pause and Quit.

### Requirements and honest limits

- Python 3.10+ on Windows, macOS or Linux.
- Tray mode needs `pystray`, `pynput`, `pyperclip` and Pillow. On Linux, `pyperclip` needs `xclip`, `xsel` or `wl-copy`, and the tray icon needs a system tray (AppIndicator); in environments without one the icon may not appear, but the hotkeys still work.
- The tray only handles text. If the clipboard holds an image or files when you convert, that non-text content is replaced and undo restores the previous *text* only.
- The global hotkey and tray icon were not tested here (no desktop session in this environment) — they need a real Windows/macOS/Linux desktop to verify. The terminal tool and the mapping table are fully tested (see Development).

## Project structure

```text
KeyLayoutFixer-Ultimate/
├── keylayoutfixer/
│   ├── __init__.py      # version, public API
│   ├── __main__.py      # python -m keylayoutfixer
│   ├── mapping.py       # ISIRI 9147 key table, both directions
│   ├── convert.py       # direction detection + conversion
│   ├── cli.py           # terminal: interactive, pipe, --text, history
│   ├── tray.py          # tray icon + global hotkey (lazy deps)
│   ├── config.py        # settings file, hotkey normalization
│   └── history.py       # JSON history, search, CSV export
├── tests/
│   ├── test_mapping.py  # round-trip for every mappable character
│   ├── test_convert.py  # detection + conversion
│   ├── test_cli.py      # pipe mode, --text, history commands
│   ├── test_config.py   # settings + hotkey normalization
│   ├── test_history.py  # storage, search, export, corruption
│   └── test_tray.py     # tray import safety + icon (no desktop needed)
├── pyproject.toml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q
```

The mapping table is the core asset: `tests/test_mapping.py` checks that converting twice returns the original text for every mappable character. Any change to `mapping.py` must cite ISIRI 9147 and keep those tests green. Tray tests skip gracefully without a desktop; the hotkey and tray icon need manual testing on a real machine.

## فارسی | Persian

ابزار تبدیل چیدمان کیبورد فارسی و انگلیسی — ترمینال‌محور و کراس‌پلتفرم (ویندوز، مک، لینوکس). اگر با چیدمان اشتباه تایپ کردی، متن را برمی‌گرداند: `sghl` می‌شود `سلام` و برعکس.

- ترمینال: `klf` (تعاملی)، `echo sghl | klf` (پایپ)، `klf --text sghl`
- تری: `klf tray` — آیکون کوچک در نوار وظیفه/منو + هات‌کی سراسری `Ctrl+Shift+K` برای تبدیل متن انتخاب‌شده در هر برنامه، و `Ctrl+Shift+Z` برای برگرداندن
- تاریخچه: `klf history` با جستجو و خروجی CSV
- جدول نگاشت کلیدها بر اساس استاندارد ISIRI 9147 بررسی شده و تبدیل دوطرفه دقیق است


## License

MIT — see [LICENSE](LICENSE).

---

## Me
[![Telegram](https://img.shields.io/badge/Telegram-erffan__hub-blue?style=for-the-badge&logo=telegram)](https://t.me/erffan_hub)
[![Twitter](https://img.shields.io/badge/Twitter-@Erffanhub__00-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/Erffanhub_00)
[![Gist](https://img.shields.io/badge/Gist-Profile-000000?style=for-the-badge&logo=github)](https://gist.github.com/erffanhub-00)
[![Github](https://img.shields.io/badge/Github-Profile-000000?style=for-the-badge&logo=github)](https://github.com/erffanhub-00)
