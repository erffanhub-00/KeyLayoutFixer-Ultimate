"""Conversion between Persian and English keyboard layouts.

The conversion is positional and direction-aware: text typed with the
wrong layout active is mapped key by key to what the user meant to type.
Converting twice returns the original text for text that contains
letters (the direction is detected from the letters). One exception: a
lone ``]`` or ``[`` is genuinely ambiguous — it is a key in both layouts
(English ``]`` types چ, Persian Shift+O types ``]``) — so a single
bracket on its own needs an explicit direction (``to_persian`` /
``to_english``); inside real text the letter majority decides correctly.
"""

from .mapping import EN_TO_FA, FA_TO_EN, is_latin_char, is_persian_char

EN = "en"
FA = "fa"


def detect_source(text):
    """Guess the layout the text was typed with.

    Returns "fa" if the text contains more Persian than Latin letters,
    otherwise "en". Text with no letters at all defaults to "en" (so
    digits convert to Persian digits, matching the old behaviour).
    """
    persian = sum(1 for ch in text if is_persian_char(ch))
    latin = sum(1 for ch in text if is_latin_char(ch))
    return FA if persian > latin else EN


def to_persian(text):
    """Convert text typed in the English layout to Persian. ``sghl`` -> ``سلام``."""
    return "".join(EN_TO_FA.get(ch, ch) for ch in text)


def to_english(text):
    """Convert text typed in the Persian layout to English. ``سلام`` -> ``sghl``."""
    return "".join(FA_TO_EN.get(ch, ch) for ch in text)


def convert_text(text, source="auto", reverse=False):
    """Convert text typed in the wrong layout.

    :param text: the text to convert.
    :param source: the layout the text was typed with: "en", "fa", or
        "auto" (default) to detect it from the text itself.
    :param reverse: if True, convert in the opposite direction of what
        ``source`` says (only meaningful with "auto").
    :returns: the converted text. Characters with no mapping (spaces,
        identical punctuation, ZWNJ/ZWJ) pass through unchanged.
    """
    if source == "auto":
        source = detect_source(text)
    if reverse:
        source = FA if source == EN else EN
    if source == EN:
        return to_persian(text)
    return to_english(text)
