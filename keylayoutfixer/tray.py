"""Tray mode: a small tray icon plus a global hotkey.

Select text anywhere, press the convert hotkey (default Ctrl+Shift+K)
and the selection is replaced with the converted text. Ctrl+Shift+Z
undoes the last conversion. All heavy dependencies (pystray, pynput,
pyperclip, Pillow) are imported lazily, so the terminal tool works
without them.

Honest limits (also in the README):

* The tray only handles text. If the clipboard holds an image or files
  when you convert, that non-text content is replaced by the converted
  text and cannot be restored by undo (undo restores the previous
  *text* only).
* On Linux the tray icon needs a system tray (AppIndicator); in
  environments without one the icon may not appear, and pyperclip
  needs xclip, xsel or wl-copy installed. The hotkeys still work
  without a visible icon.
* This module is not covered by the automated tests: it needs a real
  desktop. It must be tested by hand on Windows/macOS/Linux.
"""

import time

from .config import load_config
from .convert import convert_text
from .history import History


def create_icon_image():
    """Build a 64x64 tray icon with Pillow (no asset file needed)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise ImportError("Pillow is required for tray mode") from exc
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([2, 2, size - 2, size - 2], radius=14, fill=(13, 148, 136, 255))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((size / 2, size / 2 - 2), "K", font=font, fill=(255, 255, 255, 255),
              anchor="mm")
    return image


class TrayApp:
    """Tray icon + global hotkeys. Keeps the last conversion for undo."""

    def __init__(self, config=None):
        self.config = config or load_config()
        self.paused = False
        self.last = None  # (original, converted) of the last conversion
        self.history = (
            History(max_items=self.config["max_history"])
            if self.config["keep_history"]
            else None
        )

    def _paste(self):
        """Simulate Ctrl+V with pynput (imported lazily)."""
        from pynput.keyboard import Controller, Key

        keyboard = Controller()
        keyboard.press(Key.ctrl)
        keyboard.press("v")
        keyboard.release("v")
        keyboard.release(Key.ctrl)

    def convert_clipboard(self):
        """Convert the clipboard text and paste it over the selection."""
        if self.paused:
            return
        import pyperclip

        try:
            text = pyperclip.paste()
        except Exception:
            return
        if not text or not text.strip():
            return
        converted = convert_text(text)
        if converted == text:
            return
        self.last = (text, converted)
        try:
            pyperclip.copy(converted)
        except Exception:
            self.last = None
            return
        time.sleep(0.08)
        self._paste()
        if self.history is not None:
            from .convert import detect_source

            source = detect_source(text)
            self.history.add(text, converted, "enToFa" if source == "en" else "faToEn")

    def undo_last(self):
        """Restore the original text, but only if the clipboard still
        holds the converted text (so we never clobber new content)."""
        if self.last is None:
            return
        import pyperclip

        try:
            current = pyperclip.paste()
        except Exception:
            return
        if current != self.last[1]:
            return
        original = self.last[0]
        try:
            pyperclip.copy(original)
        except Exception:
            return
        time.sleep(0.08)
        self._paste()
        self.last = None

    def toggle_paused(self):
        self.paused = not self.paused


def run_tray(config=None):
    """Start the tray icon and global hotkeys. Blocks until Quit."""
    try:
        import pyperclip
        import pystray
        from pynput import keyboard as pynput_keyboard
    except ImportError as exc:
        raise RuntimeError(
            "tray mode needs pystray, pynput and pyperclip: "
            'pip install "keylayoutfixer[tray]"'
        ) from exc

    app = TrayApp(config)

    convert_hotkey = app.config["convert_hotkey"]
    undo_hotkey = app.config["undo_hotkey"]
    if convert_hotkey == undo_hotkey:
        raise RuntimeError("convert and undo hotkeys must be different")

    # Fail fast if the clipboard does not work here (on Linux pyperclip
    # needs xclip, xsel or wl-copy). Better a clear error now than a
    # silent tray icon later.
    try:
        pyperclip.paste()
    except Exception as exc:
        raise RuntimeError(
            "clipboard is not available: on Linux install xclip, xsel "
            f"or wl-copy ({exc})"
        ) from exc

    menu = pystray.Menu(
        pystray.MenuItem("Convert clipboard", lambda: app.convert_clipboard()),
        pystray.MenuItem("Undo", lambda: app.undo_last()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Paused", lambda: app.toggle_paused(), checked=lambda item: app.paused
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", lambda icon: icon.stop()),
    )
    icon = pystray.Icon(
        "KeyLayoutFixer", create_icon_image(), "KeyLayout Fixer", menu
    )

    hotkeys = pynput_keyboard.GlobalHotKeys(
        {
            convert_hotkey: app.convert_clipboard,
            undo_hotkey: app.undo_last,
        }
    )
    hotkeys.start()
    try:
        icon.run()
    finally:
        hotkeys.stop()
