"""Terminal interface for KeyLayoutFixer.

Usage:

    klf                    interactive mode (type, Enter, get the conversion)
    echo sghl | klf        pipe mode: convert stdin, print to stdout
    klf --text sghl        one-shot conversion
    klf sghl               same, as a positional argument
    klf --text sghl --reverse
                           convert in the opposite direction of auto-detect
    klf --text سلام --to en
                           force the direction (convert to English)
    klf tray               tray icon + global hotkey (Ctrl+Shift+K)
    klf history            show recent conversions
    klf history --search x
    klf history --export history.csv
"""

import argparse
import sys

from . import __version__
from .config import load_config
from .convert import convert_text, detect_source
from .history import History

DIRECTION_LABEL = {"en": "enToFa", "fa": "faToEn"}


def _ensure_utf8_stdio():
    """Force stdin/stdout/stderr to UTF-8.

    On Windows the console code page is usually cp1252 (or similar), which
    cannot encode Persian characters at all: printing a conversion result
    like سلام crashes with UnicodeEncodeError, and reading Persian input
    from a pipe fails the same way. Reconfiguring the streams up front
    makes the CLI work on any console, whatever its code page is.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _convert_and_record(text, source="auto", reverse=False, record=True, history=None):
    """Convert one text, optionally recording it. Returns (result, source)."""
    if source == "auto":
        used_source = detect_source(text)
    else:
        used_source = source
    if reverse and source == "auto":
        used_source = "fa" if used_source == "en" else "en"
    result = convert_text(text, source=used_source)
    if record and history is not None and text.strip():
        history.add(text, result, DIRECTION_LABEL[used_source])
    return result, used_source


def _print(text):
    try:
        print(text)
    except BrokenPipeError:
        # User piped to `head` or closed stdout: exit quietly.
        try:
            sys.stdout.close()
        except Exception:
            pass
        raise SystemExit(0)


def _convert_parser():
    parser = argparse.ArgumentParser(
        prog="klf",
        description="Convert text typed in the wrong keyboard layout "
        "(Persian <-> English).",
    )
    parser.add_argument("text", nargs="?", help="text to convert (one-shot)")
    parser.add_argument("--text", dest="text_opt", help="text to convert (one-shot)")
    parser.add_argument(
        "--to",
        choices=["fa", "en"],
        help="force the target language (fa = to Persian, en = to English)",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="convert in the opposite direction of auto-detect",
    )
    parser.add_argument(
        "--no-history", action="store_true", help="do not record this conversion"
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    return parser


def _history_parser():
    parser = argparse.ArgumentParser(
        prog="klf history", description="Show, search, export or clear history."
    )
    parser.add_argument("--search", help="show only entries containing this text")
    parser.add_argument("--export", metavar="FILE", help="export history to a CSV file")
    parser.add_argument("--clear", action="store_true", help="delete all history")
    parser.add_argument("--yes", action="store_true", help="skip the clear confirmation")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="how many entries to show (default: 20, 0 = all)",
    )
    return parser


def _run_history(argv):
    args = _history_parser().parse_args(argv)
    config = load_config()
    history = History(max_items=config["max_history"])
    if args.clear:
        if not args.yes:
            answer = input("Clear all history? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Cancelled.")
                return 0
        history.clear()
        print("History cleared.")
        return 0
    if args.export:
        path = history.export_csv(args.export)
        print(f"Exported {len(history.items)} entries to {path}")
        return 0
    entries = history.search(args.search) if args.search else history.list()
    if args.limit:
        entries = entries[: args.limit]
    if not entries:
        print("No history yet. Convert some text first.")
        return 0
    for index, entry in enumerate(entries, start=1):
        arrow = "EN->FA" if entry["dir"] == "enToFa" else "FA->EN"
        original = entry["original"]
        converted = entry["converted"]
        if len(original) > 60:
            original = original[:57] + "..."
        if len(converted) > 60:
            converted = converted[:57] + "..."
        print(f"{index}. [{entry['time']}] {arrow}: {original} => {converted}")
    return 0


def _run_tray():
    try:
        from .tray import run_tray
    except ImportError as exc:
        print(f"klf tray needs the tray dependencies: {exc}", file=sys.stderr)
        print("Install them with: pip install \"keylayoutfixer[tray]\"", file=sys.stderr)
        return 1
    config = load_config()
    try:
        run_tray(config)
    except RuntimeError as exc:
        print(f"klf tray: {exc}", file=sys.stderr)
        return 1
    return 0


def _run_convert(argv):
    args = _convert_parser().parse_args(argv)
    config = load_config()
    history = (
        History(max_items=config["max_history"]) if config["keep_history"] else None
    )
    record = not args.no_history and history is not None

    if args.to == "fa":
        source = "en"
    elif args.to == "en":
        source = "fa"
    else:
        source = "auto"

    one_shot = args.text_opt if args.text_opt is not None else args.text
    if one_shot is not None:
        result, _ = _convert_and_record(
            one_shot, source=source, reverse=args.reverse, record=record,
            history=history,
        )
        _print(result)
        return 0

    if not sys.stdin.isatty():
        # Pipe mode: convert stdin line by line, keep empty lines.
        data = sys.stdin.read()
        if data == "":
            return 0
        lines = data.split("\n")
        converted_lines = []
        for line in lines:
            if line == "":
                converted_lines.append("")
                continue
            result, _ = _convert_and_record(
                line, source=source, reverse=args.reverse, record=False,
                history=None,
            )
            converted_lines.append(result)
        if record and history is not None and data.strip():
            whole, used = _convert_and_record(
                data, source=source, reverse=args.reverse, record=False,
                history=None,
            )
            history.add(data, whole, DIRECTION_LABEL[used])
        # Write raw (no extra newline): split/join round-trips the exact
        # line structure, including a trailing newline.
        try:
            sys.stdout.write("\n".join(converted_lines))
            sys.stdout.flush()
        except BrokenPipeError:
            try:
                sys.stdout.close()
            except Exception:
                pass
            return 0
        return 0

    # Interactive mode.
    print(f"KeyLayoutFixer {__version__} — type text, Enter converts it.",
          file=sys.stderr)
    print("Type 'exit' or press Ctrl+C to quit.", file=sys.stderr)
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            print(file=sys.stderr)
            return 0
        if line.strip().lower() in ("exit", "quit"):
            return 0
        if line.strip() == "":
            continue
        result, _ = _convert_and_record(
            line, source=source, reverse=args.reverse, record=record,
            history=history,
        )
        _print(result)


def main(argv=None):
    """Entry point for the `klf` / `keylayoutfixer` commands."""
    _ensure_utf8_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "tray":
        return _run_tray()
    if argv and argv[0] == "history":
        return _run_history(argv[1:])
    return _run_convert(argv)


if __name__ == "__main__":
    raise SystemExit(main())
