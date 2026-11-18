"""Standalone-binary entry point for PyInstaller (build only).

``keylayoutfixer/__main__.py`` cannot be used directly: it uses a
relative import, which fails when PyInstaller treats it as a top-level
script. This file imports the package properly, so:

    pyinstaller --onefile --name klf --collect-all pystray \
        --collect-all pynput klf.py

produces a single-file ``klf`` binary (tray mode included).
"""

import sys

from keylayoutfixer.cli import main

if __name__ == "__main__":
    sys.exit(main())
