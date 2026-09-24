"""Turn Republic Book I (narrated by Socrates) into script form.

Heuristic first pass: speaker markers ("I said", "he replied", "said Polemarchus")
decide the speaker where present; otherwise speakers alternate between Socrates and
the last other speaker. Paragraphs that look like pure narration are emitted as
``[NARRATION: ...]`` for rewriting by hand. Review the output before use.

    .venv/bin/python tools/republic1.py corpus/republic.txt > /tmp/republic-1.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

OTHERS = ["Glaucon", "Polemarchus", "Adeimantus", "Cephalus", "Thrasymachus", "Cleitophon"]
NAMED = re.compile(r"\b(?:said|replied|answered|rejoined|added|interposed|interrupted|asked)\s+("
                   + "|".join(OTHERS) + r")\b|\b(" + "|".join(OTHERS)
                   + r")\s+(?:said|replied|answered|rejoined|added|interposed|interrupted|asked)\b")
ME = re.compile(r"\b(?:I said|said I|I replied|I answered|I rejoined|I asked|I retorted)\b")
HE = re.compile(r"\b(?:he said|said he|he replied|he answered|he rejoined|he asked|he retorted|he continued)\b")
HEADER = re.compile(r"^[A-Z][A-Z -]*[A-Z]$")
# main interlocutor of each speaker-list section, in order of the headers in Book I
MAINS = ["GLAUCON", "POLEMARCHUS", "CEPHALUS", "CEPHALUS", "POLEMARCHUS", "THRASYMACHUS",
         "THRASYMACHUS", "THRASYMACHUS", "THRASYMACHUS", "GLAUCON", "THRASYMACHUS"]
MIXED = re.compile(r"^(.*\b(?:said|replied|answered|saluted|roared)\b[^:]*):\s*(.+)$")
NARRATION = re.compile(r"^I (?:WENT|went|turned|was|listened|thought|saw|had|could|looked|found|felt|perceived|then)\b")

STRIP = [
    r",?\s*\bI (?:said|replied|answered|rejoined|asked|retorted)\b,?",
    r",?\s*\bsaid I\b,?",
    r",?\s*\bhe (?:said|replied|answered|rejoined|asked|retorted|continued)\b,?",
    r",?\s*\bsaid he\b,?",
    r",?\s*\b(?:said|replied|answered|rejoined|added|interposed)\s+(?:" + "|".join(OTHERS) + r")\b(?:\s+interposing)?,?",
    r"^(?:" + "|".join(OTHERS) + r")\s+(?:said|replied|answered|added)(?: to me)?:\s*",
]


def clean(text: str) -> str:
    for pat in STRIP:
        text = re.sub(pat, "", text)
    text = re.sub(r"\s+([,;:.?!])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"^[,;\s]+", "", text)
    return text.strip()


def convert(lines: list[str]) -> str:
    out: list[str] = []
    prev = None  # last speaker emitted
    section = -1
    other = "GLAUCON"
    for raw in lines:
        para = raw.strip()
        if not para or para.startswith("-----"):
            continue
        if HEADER.match(para):
            section += 1
            other = MAINS[section]
            continue
        if NARRATION.match(para) and ":" not in para:
            out.append(f"[NARRATION: {para}]")
            continue
        if (mm := MIXED.match(para)) and not NAMED.search(mm.group(1)) and not ME.search(mm.group(1)):
            # narration leading into speech: "He saluted me eagerly, and then he said: ..."
            out.append(f"[NARRATION: {mm.group(1)}]")
            para = mm.group(2)
        m = NAMED.search(para)
        if m:
            speaker = (m.group(1) or m.group(2)).upper()
        elif ME.search(para):
            speaker = "SOCRATES"
        elif HE.search(para):
            speaker = other
        else:
            speaker = other if prev == "SOCRATES" else "SOCRATES"
        out.append(f"{speaker}: {clean(para)}")
        prev = speaker
    return "\n\n".join(out) + "\n"


def main() -> None:
    lines = Path(sys.argv[1]).read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == "BOOK I" and i > 10)
    end = next(i for i, l in enumerate(lines) if l.strip() == "BOOK II" and i > start)
    sys.stdout.write(convert(lines[start + 1 : end]))


if __name__ == "__main__":
    main()
