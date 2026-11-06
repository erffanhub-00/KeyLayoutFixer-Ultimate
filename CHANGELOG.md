# Changelog

## 1.0.0 — 2026-11-06

Cross-platform Python rewrite. This version replaces the old AutoHotkey
v3.1 release, which was Windows-only (the old script stays in its
original repository under `terminal88project`).

### Added

- Terminal tool `klf` (also available as `keylayoutfixer`):
  interactive mode, pipe/stdin mode, one-shot `--text`, `--to` and
  `--reverse` to force the direction.
- Tray mode (`klf tray`): small tray icon plus the global hotkeys
  Ctrl+Shift+K (convert selection) and Ctrl+Shift+Z (undo), using
  pystray, pynput and pyperclip.
- Conversion history as JSON, with search and CSV export
  (`klf history`), atomic writes, and safe recovery from a corrupt
  history file.
- Settings file (`config.json`) with sensible defaults; the old
  AHK hotkey format (`^+k`) is accepted and normalized.
- pytest suite: mapping round-trip for every mappable character,
  direction detection, CLI pipe mode, history storage, settings.

### Fixed (mapping table, verified against ISIRI 9147)

The old AHK table was missing 32 mappings and had one wrong entry,
so text with shifted characters converted only partially:

- `A` mapped to ژ; ISIRI 9147 says Shift+A is ؤ and ژ is Shift+C.
- Added all missing shifted letters: I (ّ), O (]), P ([), S (ئ),
  D (ي), F (إ), G (أ), H (آ), J (ة), K (»), L («), Z (ك), X (ٓ),
  C (ژ), V (ٰ), N (ٔ), M (ء).
- Added all missing shifted digits and punctuation: @ (٬), # (٫),
  $ (﷼), % (٪), ^ (×), & (،), ( ), ) (, _ (ـ), ~ (÷), { }, } {,
  " (؛), < >, > <, ? (؟).
- The reverse map now handles the bracket keys: `]` converts back to
  O and `[` back to P (they are Shift+O / Shift+P in the Persian
  layout), while چ and ج still map back to `]` and `[`.
- Corrected the documented example: سلام converts to `sghl`
  (positional), not `salam` as the old README claimed.
- ZWNJ/ZWJ are deliberately left unconverted: they occur
  legitimately inside Persian text, and mapping them would corrupt
  real words.
- Auto-detect counts » « × ÷ as Persian (they only exist on the
  Persian layout), so they round-trip in auto mode. A lone `]` or
  `[` stays ambiguous — it is a key in both layouts — and needs an
  explicit direction; inside real text the letter majority decides.

### Notes

- The old version's bugs that do not carry over: the tray sound
  toggle called a nonexistent function, the hotkey display was
  garbled (`CtrlShift+Shift+k`), the hand-rolled JSON history
  corrupted entries containing backslashes, braces or `},{`, and a
  corrupt settings file could crash startup. All are fixed by
  construction in this rewrite (real JSON, no dead code paths).
- Not tested here: the global hotkey and tray icon need a real
  desktop (Windows/macOS/Linux). The terminal tool and the mapping
  table are fully tested on this machine.
