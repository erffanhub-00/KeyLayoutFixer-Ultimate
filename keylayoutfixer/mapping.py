"""Persian <-> English keyboard layout mapping.

Verified against ISIRI 9147 (Iranian national standard for the Persian
keyboard layout) using two independent sources that agree:

* the ISIRI 9147 table (Wikipedia, "ISIRI 9147")
* the Emacs quail input method ``farsi-isiri-9147`` (explicit per-key rules)

The map is positional: each key is the character that key produces in the
*other* layout. It is a bijection, so converting twice with a known
direction returns the original text (see tests/test_mapping.py). With
auto-detection, text containing letters round-trips; a lone ``]`` or
``[`` is ambiguous because it is a key in both layouts.

Deliberate exclusions (not bugs):

* Backtick (`` ` ``) produces ZWJ (U+200D) in the Persian layout and
  Shift+B / Shift+Space produce ZWNJ (U+200C). Both are invisible
  formatting characters that also occur legitimately inside Persian
  text, so they are left untouched instead of being mapped to a visible
  key. Mapping them would corrupt real Persian text.
* Characters that are identical in both layouts (``. / - = ! * + : |``
  backslash, space) need no entry: they pass through unchanged.
* AltGr (third-level) characters are out of scope: they are almost
  never part of text typed in the wrong layout.
"""

# English key -> Persian character (what that physical key types when the
# Persian layout is active).
EN_TO_FA = {
    # Letters, unshifted.
    "q": "ض", "w": "ص", "e": "ث", "r": "ق", "t": "ف",
    "y": "غ", "u": "ع", "i": "ه", "o": "خ", "p": "ح",
    "a": "ش", "s": "س", "d": "ی", "f": "ب", "g": "ل",
    "h": "ا", "j": "ت", "k": "ن", "l": "م",
    "z": "ظ", "x": "ط", "c": "ز", "v": "ر", "b": "ذ",
    "n": "د", "m": "پ",
    # Punctuation, unshifted.
    "[": "ج", "]": "چ", ";": "ک", "'": "گ", ",": "و",
    # Digits.
    "1": "۱", "2": "۲", "3": "۳", "4": "۴", "5": "۵",
    "6": "۶", "7": "۷", "8": "۸", "9": "۹", "0": "۰",
    # Letters, shifted (diacritics and extra letters).
    "Q": "ْ", "W": "ٌ", "E": "ٍ", "R": "ً", "T": "ُ",
    "Y": "ِ", "U": "َ", "I": "ّ",
    "O": "]", "P": "[",
    "A": "ؤ", "S": "ئ", "D": "ي", "F": "إ", "G": "أ",
    "H": "آ", "J": "ة", "K": "»", "L": "«",
    "Z": "ك", "X": "ٓ", "C": "ژ", "V": "ٰ", "N": "ٔ", "M": "ء",
    # Digits and punctuation, shifted.
    "@": "٬", "#": "٫", "$": "﷼", "%": "٪", "^": "×",
    "&": "،", "(": ")", ")": "(", "_": "ـ", "~": "÷",
    "{": "}", "}": "{", '"': "؛", "<": ">", ">": "<", "?": "؟",
}

# Persian character -> English key. Built by inverting EN_TO_FA, which is
# a bijection: every value appears exactly once, so no mapping is lost.
# In particular, "]" maps back to "O" and "[" back to "P" (those keys
# produce brackets when shifted in the Persian layout), while "چ" maps
# back to "]" and "ج" back to "[".
FA_TO_EN = {value: key for key, value in EN_TO_FA.items()}

# Sanity check at import time: the table must stay a bijection, otherwise
# a mapping would silently disappear from the reverse direction.
assert len(FA_TO_EN) == len(EN_TO_FA), "EN_TO_FA has duplicate values"

# Characters that identify text as Persian (Arabic script blocks plus the
# joiners that only occur in Persian/Arabic text). Used for auto-detect.
_PERSIAN_RANGES = (
    (0x0600, 0x06FF),  # Arabic
    (0x0750, 0x077F),  # Arabic Supplement
    (0x08A0, 0x08FF),  # Arabic Extended-A
    (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    (0x200C, 0x200D),  # ZWNJ, ZWJ
)


# Punctuation that only the Persian layout produces: a lone one of these
# (or text made only of them) must still detect as Persian, otherwise
# auto-detect defaults to English and they never convert back. They cannot
# come from the English layout — there is no key for them there.
_PERSIAN_ONLY_PUNCT = frozenset("»«×÷")


def is_persian_char(ch):
    """Return True if a single character belongs to Persian/Arabic script
    or is punctuation only the Persian layout produces."""
    if ch in _PERSIAN_ONLY_PUNCT:
        return True
    code = ord(ch)
    return any(start <= code <= end for start, end in _PERSIAN_RANGES)


def is_latin_char(ch):
    """Return True for ASCII letters."""
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z")
