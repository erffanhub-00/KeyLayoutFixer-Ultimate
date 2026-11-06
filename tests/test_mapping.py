"""Mapping table tests.

The table is the core asset of this project: it was verified key by key
against ISIRI 9147 (the Iranian national standard for the Persian
keyboard layout), cross-checked with the Emacs quail input method
``farsi-isiri-9147``. If you change a mapping, you must cite the
standard and keep every test here green.
"""

from keylayoutfixer.convert import convert_text, to_english, to_persian
from keylayoutfixer.mapping import EN_TO_FA, FA_TO_EN


def test_table_is_a_bijection():
    # Every Persian character must come from exactly one English key,
    # otherwise the reverse direction silently loses a mapping.
    assert len(FA_TO_EN) == len(EN_TO_FA)
    assert set(FA_TO_EN.values()) == set(EN_TO_FA.keys())


def test_round_trip_every_mappable_character():
    # convert(convert(x)) == x for every character in both directions.
    for english_char in EN_TO_FA:
        assert to_english(to_persian(english_char)) == english_char
    for persian_char in FA_TO_EN:
        assert to_persian(to_english(persian_char)) == persian_char


def test_auto_round_trip_persian_only_punctuation():
    # » « × ÷ exist only on the Persian layout, so auto-detect must
    # count them as Persian — otherwise a lone one never converts back.
    assert convert_text(convert_text("K")) == "K"
    assert convert_text(convert_text("L")) == "L"
    assert convert_text(convert_text("^")) == "^"
    assert convert_text(convert_text("~")) == "~"
    assert convert_text(convert_text("سلام »")) == "سلام »"


def test_lone_brackets_need_explicit_direction():
    # ] and [ are keys in both layouts, so auto-detect cannot know which
    # way a lone one goes. With an explicit direction both work.
    assert to_english("]") == "O"
    assert to_english("[") == "P"
    assert to_persian("]") == "چ"
    assert to_persian("[") == "ج"
    # Inside real text the letter majority decides, so this round-trips.
    assert convert_text(convert_text("سلام]")) == "سلام]"


def test_documented_examples():
    # The examples from the README. Note: the old README claimed
    # "سلام -> salam", which is wrong: the conversion is positional,
    # not a transliteration. سلام typed on the Persian layout is
    # s-g-h-l on the English layout.
    assert to_persian("sghl") == "سلام"
    assert to_english("سلام") == "sghl"


def test_lowercase_letters():
    assert to_persian("qwertyuiop") == "ضصثقفغعهخح"
    assert to_persian("asdfghjkl") == "شسیبلاتنم"
    assert to_persian("zxcvbnm") == "ظطزرذدپ"


def test_digits():
    assert to_persian("1234567890") == "۱۲۳۴۵۶۷۸۹۰"
    assert to_english("۱۲۳۴۵۶۷۸۹۰") == "1234567890"


def test_shifted_letters_diacritics_and_extra_letters():
    # Diacritics (tanvin, harakat, shadda, sukun).
    assert to_persian("QWERTYU") == "ًٌٍَُِْ"
    assert to_persian("I") == "ّ"
    # The old AHK table mapped A to ژ; ISIRI 9147 says Shift+A is ؤ
    # and ژ is Shift+C. This test pins the correction.
    assert to_persian("A") == "ؤ"
    assert to_persian("C") == "ژ"
    assert to_persian("S") == "ئ"
    assert to_persian("D") == "ي"  # Arabic Yeh, not Farsi Yeh (d -> ی)
    assert to_persian("F") == "إ"
    assert to_persian("G") == "أ"
    assert to_persian("H") == "آ"
    assert to_persian("J") == "ة"
    assert to_persian("K") == "»"
    assert to_persian("L") == "«"
    assert to_persian("Z") == "ك"  # Arabic Kaf, not Keheh (; -> ک)
    assert to_persian("X") == "ٓ"
    assert to_persian("V") == "ٰ"
    assert to_persian("N") == "ٔ"
    assert to_persian("M") == "ء"


def test_shifted_brackets_are_swapped_keys():
    # In the Persian layout Shift+O types "]" and Shift+P types "[",
    # while the [ and ] keys type ج and چ. Both directions work.
    assert to_persian("O") == "]"
    assert to_persian("P") == "["
    assert to_english("]") == "O"
    assert to_english("[") == "P"
    assert to_persian("[") == "ج"
    assert to_persian("]") == "چ"
    # Braces swap the same way: Shift+[ types "}" in Persian.
    assert to_persian("{") == "}"
    assert to_persian("}") == "{"
    # Parentheses and angle brackets swap too.
    assert to_persian("(") == ")"
    assert to_persian(")") == "("
    assert to_persian("<") == ">"
    assert to_persian(">") == "<"


def test_shifted_digits_and_punctuation():
    assert to_persian("@") == "٬"
    assert to_persian("#") == "٫"
    assert to_persian("$") == "﷼"
    assert to_persian("%") == "٪"
    assert to_persian("^") == "×"
    assert to_persian("&") == "،"
    assert to_persian("_") == "ـ"
    assert to_persian("~") == "÷"
    assert to_persian('"') == "؛"
    assert to_persian("?") == "؟"


def test_identity_characters_pass_through():
    # Characters that are the same in both layouts need no mapping.
    unchanged = " . / - = ! * + : | \\ \t"
    assert to_persian(unchanged) == unchanged
    assert to_english(unchanged) == unchanged


def test_joiners_pass_through():
    # ZWNJ (U+200C) and ZWJ (U+200D) occur legitimately inside Persian
    # text; they are never converted (deliberate, see mapping.py).
    # می‌خواهم -> l d ZWNJ o , h i l (positional, joiner untouched).
    assert to_english("می‌خواهم") == "ld‌o,hil"
    assert to_persian("ld‌o,hil") == "می‌خواهم"
    assert "\u200c" in to_english("می‌خواهم")


def test_mixed_text_keeps_unmapped_characters():
    assert to_persian("hello, world!") == "اثممخو صخقمی!"
    assert to_english("سلام!") == "sghl!"
