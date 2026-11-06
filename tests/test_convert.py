"""Tests for direction detection and convert_text()."""

from keylayoutfixer.convert import convert_text, detect_source, to_english, to_persian


def test_detect_source():
    assert detect_source("سلام دنیا") == "fa"
    assert detect_source("hello world") == "en"
    # Majority wins: 4 Persian letters vs 5 Latin ones -> English.
    assert detect_source("سلام hello") == "en"
    assert detect_source("سلام دنیا hello") == "fa"
    assert detect_source("hello سلام دنیا") == "fa"
    assert detect_source("123") == "en"  # no letters: defaults to English
    assert detect_source("") == "en"
    assert detect_source("۱۲۳") == "fa"  # Persian digits count as Persian


def test_convert_text_auto():
    assert convert_text("sghl") == "سلام"
    assert convert_text("سلام") == "sghl"
    assert convert_text("hello") == "اثممخ"
    assert convert_text("") == ""


def test_convert_text_explicit_source():
    assert convert_text("sghl", source="en") == "سلام"
    assert convert_text("sghl", source="fa") == "sghl"  # no Persian chars to map
    assert convert_text("سلام", source="fa") == "sghl"
    assert convert_text("سلام", source="en") == "سلام"  # no English keys to map


def test_convert_text_reverse():
    # --reverse flips the auto-detected direction.
    assert convert_text("sghl", reverse=True) == "sghl"
    assert convert_text("سلام", reverse=True) == "سلام"


def test_round_trip_sentences():
    # Round-trip holds in the direction the text was typed in:
    # English-layout text survives en->fa->en, Persian text fa->en->fa.
    english_texts = [
        "sghl hk, ;hkd?",
        "Hello 123, test.",
        "C++ <code> {x: 1} #tag @user 100%",
    ]
    for text in english_texts:
        assert to_english(to_persian(text)) == text
    persian_texts = [
        "سلام دنیا!",
        "می‌خواهم بروم.",
    ]
    for text in persian_texts:
        assert to_persian(to_english(text)) == text
