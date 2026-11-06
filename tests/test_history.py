"""Tests for history storage: round-trip, search, export, corruption."""

import json

from keylayoutfixer.history import History


def test_add_and_list_round_trip(tmp_path):
    history = History(path=tmp_path / "history.json")
    history.add("sghl", "سلام", "enToFa")
    history.add("سلام", "sghl", "faToEn")
    # File order is chronological; list() is newest first.
    assert [item["original"] for item in history.list()] == ["سلام", "sghl"]
    stored = json.loads((tmp_path / "history.json").read_text(encoding="utf-8"))
    assert stored[0]["original"] == "sghl"
    assert stored[0]["dir"] == "enToFa"
    # Reloading from disk gives the same entries.
    reloaded = History(path=tmp_path / "history.json")
    assert len(reloaded.items) == 2
    assert reloaded.items[1]["converted"] == "sghl"


def test_history_survives_special_characters(tmp_path):
    # Braces, quotes, backslashes and "},{" inside converted text must
    # survive a save/load cycle (the old hand-rolled parser lost them).
    nasty = 'a{b}c "quoted" C:\\new\\test }{, x'
    history = History(path=tmp_path / "history.json")
    history.add(nasty, nasty, "enToFa")
    reloaded = History(path=tmp_path / "history.json")
    assert reloaded.items[0]["original"] == nasty
    assert reloaded.items[0]["converted"] == nasty


def test_max_items_cap(tmp_path):
    history = History(path=tmp_path / "history.json", max_items=3)
    for index in range(5):
        history.add(f"text{index}", f"converted{index}", "enToFa")
    assert [item["original"] for item in history.items] == [
        "text2",
        "text3",
        "text4",
    ]


def test_search(tmp_path):
    history = History(path=tmp_path / "history.json")
    history.add("sghl", "سلام", "enToFa")
    history.add("hello", "اثممخ", "enToFa")
    assert [item["original"] for item in history.search("سلام")] == ["sghl"]
    assert [item["original"] for item in history.search("HELLO")] == ["hello"]
    assert len(history.search("")) == 2


def test_export_csv(tmp_path):
    history = History(path=tmp_path / "history.json")
    history.add("a,b", "x\ny", "enToFa")
    out = tmp_path / "out.csv"
    history.export_csv(out)
    content = out.read_text(encoding="utf-8-sig")
    assert "Index,Time,Original,Converted,Direction" in content
    assert "English to Persian" in content
    # csv module quotes the comma/newline fields instead of breaking rows.
    assert content.count("English to Persian") == 1


def test_corrupt_file_is_backed_up_not_lost(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{not json at all", encoding="utf-8")
    history = History(path=path)
    assert history.items == []
    assert (tmp_path / "history.json.corrupt").exists()
    # And the history still works afterwards.
    history.add("sghl", "سلام", "enToFa")
    assert len(History(path=path).items) == 1


def test_clear(tmp_path):
    history = History(path=tmp_path / "history.json")
    history.add("sghl", "سلام", "enToFa")
    history.clear()
    assert history.items == []
    assert History(path=tmp_path / "history.json").items == []


def test_empty_original_is_not_recorded(tmp_path):
    history = History(path=tmp_path / "history.json")
    assert history.add("", "", "enToFa") is None
    assert history.items == []
