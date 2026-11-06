"""Conversion history: JSON storage, search, CSV export.

History is a plain JSON array of ``{"time", "original", "converted",
"dir"}`` objects, newest last in the file. Writes are atomic (temp
file + rename). A corrupt file is backed up as ``history.json.corrupt``
and replaced with an empty history instead of crashing.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

from .config import get_data_dir

FILENAME = "history.json"


class History:
    def __init__(self, path=None, max_items=200):
        self.path = Path(path) if path is not None else get_data_dir() / FILENAME
        self.max_items = max(0, int(max_items))
        self.items = self._load()

    def _load(self):
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            backup = self.path.with_suffix(".json.corrupt")
            try:
                self.path.replace(backup)
            except OSError:
                pass
            return []
        if not isinstance(data, list):
            return []
        items = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            if not entry.get("original"):
                continue
            items.append(
                {
                    "time": str(entry.get("time", "")),
                    "original": str(entry.get("original", "")),
                    "converted": str(entry.get("converted", "")),
                    "dir": str(entry.get("dir", "")),
                }
            )
        return items[-self.max_items :] if self.max_items else items

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(self.items, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(tmp, self.path)

    def add(self, original, converted, direction):
        """Record one conversion. Returns the stored entry or None."""
        if not original:
            return None
        entry = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "original": original,
            "converted": converted,
            "dir": direction,
        }
        self.items.append(entry)
        if self.max_items and len(self.items) > self.max_items:
            del self.items[: len(self.items) - self.max_items]
        self._save()
        return entry

    def list(self, newest_first=True):
        """All entries, newest first by default."""
        items = list(self.items)
        if newest_first:
            items.reverse()
        return items

    def search(self, query):
        """Case-insensitive substring search over original/converted text."""
        query = (query or "").strip().lower()
        if not query:
            return self.list()
        return [
            item
            for item in self.list()
            if query in item["original"].lower()
            or query in item["converted"].lower()
        ]

    def clear(self):
        self.items = []
        self._save()

    def export_csv(self, path):
        """Export history to CSV (UTF-8 with BOM, so Excel opens it)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Index", "Time", "Original", "Converted", "Direction"])
            for index, item in enumerate(self.items, start=1):
                label = (
                    "English to Persian"
                    if item["dir"] == "enToFa"
                    else "Persian to English"
                )
                writer.writerow(
                    [index, item["time"], item["original"], item["converted"], label]
                )
        return path
