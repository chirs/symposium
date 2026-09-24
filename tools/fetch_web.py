"""Fetch chapters of the World English Bible (public domain) into corpus/nt/ as verse-per-line text.

    .venv/bin/python tools/fetch_web.py "John 3" "Acts 17"
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "corpus" / "nt"


def fetch(ref: str) -> Path:
    url = f"https://bible-api.com/{urllib.parse.quote(ref)}?translation=web"
    with urllib.request.urlopen(url, timeout=30) as res:
        data = json.load(res)
    verses = data["verses"]
    book = verses[0]["book_name"].lower().replace(" ", "-")
    chapter = verses[0]["chapter"]
    lines = [f"{v['chapter']}:{v['verse']} {' '.join(v['text'].split())}" for v in verses]
    path = OUT / f"{book}-{chapter}.txt"
    path.write_text(f"{data['reference']} (World English Bible)\n\n" + "\n".join(lines) + "\n")
    return path


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for ref in sys.argv[1:]:
        print(fetch(ref))
