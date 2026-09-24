"""Turn a speaker-tagged Jowett text from corpus/ into script form.

Handles the corpus files that tag every speech like ``[Soc.]`` / ``[Socrates]``:
Euthyphro, Crito, Gorgias. Untagged paragraphs continue the current speech.

    .venv/bin/python tools/from_corpus.py corpus/crito.txt Soc=SOCRATES Cr=CRITO > dialogues/crito/seed.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TAG = re.compile(r"^\[([A-Za-z]+)\.?\]\s*(.*)$")
NOISE = re.compile(r"^(PERSONS OF THE DIALOGUE|SCENE:|•|-{5,})")


def convert(text: str, names: dict[str, str]) -> str:
    out: list[str] = []
    current: list[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if m := TAG.match(line):
            if current:
                out.append("\n\n".join(p for p in current if p))
            tag = m.group(1)
            name = names.get(tag) or names.get(tag[:3]) or names.get(tag[:2])
            if not name:
                raise SystemExit(f"unknown tag {tag!r}; pass {tag}=NAME")
            current = [f"{name}: {m.group(2)}".rstrip()]
        elif current is None:
            if line and not NOISE.match(line):
                raise SystemExit(f"text before first tag: {line!r}")
        elif line:
            current.append(line)
    if current:
        out.append("\n\n".join(p for p in current if p))
    return "\n\n".join(out) + "\n"


def main() -> None:
    src = Path(sys.argv[1])
    names = {}
    for arg in sys.argv[2:]:
        tag, name = arg.split("=", 1)
        names[tag] = name
        names[tag[:3]] = name
        names[tag[:2]] = name
    sys.stdout.write(convert(src.read_text(), names))


if __name__ == "__main__":
    main()
