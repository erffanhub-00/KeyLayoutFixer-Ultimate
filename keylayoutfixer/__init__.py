"""KeyLayoutFixer: Persian <-> English keyboard layout converter.

Cross-platform terminal tool (``klf``) with an optional tray mode
(``klf tray``). The mapping table is verified against ISIRI 9147.
"""

__version__ = "1.0.0"

from .convert import convert_text, detect_source, to_english, to_persian

__all__ = ["__version__", "convert_text", "detect_source", "to_english", "to_persian"]
