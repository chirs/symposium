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


if __name__ == "__main__" and "--final" not in sys.argv:
    main()


# ---------------------------------------------------------------------------
# Second stage: hand corrections to the heuristic output, keyed by its 1-based
# block numbers, plus a rewritten opening (the Piraeus and Cephalus scenes are
# too narrated for the heuristics). Run `main()` for the raw pass and
# `assemble()` for the finished seed.

def para(lines: list[str], prefix: str) -> str:
    for i, line in enumerate(lines):
        if line.strip().startswith(prefix):
            return line.strip()
    raise SystemExit(f"paragraph not found: {prefix!r}")


def following(lines: list[str], prefix: str, n: int) -> list[str]:
    """The n non-blank paragraphs after the one starting with prefix."""
    for i, line in enumerate(lines):
        if line.strip().startswith(prefix):
            rest = [l.strip() for l in lines[i + 1 :] if l.strip()]
            return rest[:n]
    raise SystemExit(f"paragraph not found: {prefix!r}")


def opening(lines: list[str]) -> list[str]:
    ceph1 = para(lines, "You don't come to see me, Socrates")
    soc1 = para(lines, "I replied: There is nothing which").removeprefix("I replied: ")
    ceph2 = para(lines, "I will tell you, Socrates, he said, what my own feeling is").replace(
        "Socrates, he said, what", "Socrates, what"
    )
    soc2 = para(lines, "I listened in admiration")
    soc2 = "Yes, Cephalus; but " + soc2.split("--Yes, Cephalus, I said: but ", 1)[1]
    ceph3 = para(lines, "You are right, he replied;").replace("You are right, he replied;", "You are right;")
    soc3 = para(lines, "May I ask, Cephalus, whether your fortune")
    ceph4 = para(lines, "Acquired! Socrates")
    soc4 = para(lines, "That was why I asked you the question").replace(", I replied,", ",")
    soc4 = soc4.partition(" That is true, he said.")[0]
    soc5 = para(lines, "Yes, that is very true, but may I ask another question")
    ceph5 = para(lines, "One, he said, of which").replace("One, he said, of which", "One, of which")
    ceph5 = " ".join([ceph5] + following(lines, "One, he said, of which", 2))
    return [
        (
            "[Socrates went down yesterday to the Piraeus with Glaucon the son of Ariston, to offer up "
            "his prayers to the goddess, and also to see in what manner they would celebrate the "
            "festival, which was a new thing. When they had finished their prayers and viewed the "
            "spectacle, they turned in the direction of the city; and at that instant Polemarchus the "
            "son of Cephalus caught sight of them from a distance as they were starting on their way "
            "home, and told his servant to run and bid them wait for him. The servant took hold of "
            "Socrates by the cloak behind.]"
        ),
        "SERVANT: Polemarchus desires you to wait.",
        "SOCRATES: Where is your master?",
        "SERVANT: There he is, coming after you, if you will only wait.",
        "GLAUCON: Certainly we will.",
        (
            "[In a few minutes Polemarchus appeared, and with him Adeimantus, Glaucon's brother, "
            "Niceratus the son of Nicias, and several others who had been at the procession.]"
        ),
        "POLEMARCHUS: I perceive, Socrates, that you and our companion are already on your way to the city.",
        "SOCRATES: You are not far wrong.",
        "POLEMARCHUS: But do you see how many we are?",
        "SOCRATES: Of course.",
        "POLEMARCHUS: And are you stronger than all these? for if not, you will have to remain where you are.",
        "SOCRATES: May there not be the alternative, that we may persuade you to let us go?",
        "POLEMARCHUS: But can you persuade us, if we refuse to listen to you?",
        "GLAUCON: Certainly not.",
        "POLEMARCHUS: Then we are not going to listen; of that you may be assured.",
        (
            "ADEIMANTUS: Has no one told you of the torch-race on horseback in honour of the goddess "
            "which will take place in the evening?"
        ),
        (
            "SOCRATES: With horses! That is a novelty. Will horsemen carry torches and pass them one to "
            "another during the race?"
        ),
        (
            "POLEMARCHUS: Yes, and not only so, but a festival will be celebrated at night, which you "
            "certainly ought to see. Let us rise soon after supper and see this festival; there will be "
            "a gathering of young men, and we will have a good talk. Stay then, and do not be perverse."
        ),
        "GLAUCON: I suppose, since you insist, that we must.",
        "SOCRATES: Very good.",
        (
            "[Accordingly they went with Polemarchus to his house; and there they found his brothers "
            "Lysias and Euthydemus, and with them Thrasymachus the Chalcedonian, Charmantides the "
            "Paeanian, and Cleitophon the son of Aristonymus. There too was Cephalus the father of "
            "Polemarchus, whom Socrates had not seen for a long time, and thought very much aged. He "
            "was seated on a cushioned chair, and had a garland on his head, for he had been "
            "sacrificing in the court; and there were some other chairs in the room arranged in a "
            "semicircle, upon which they sat down by him. He saluted Socrates eagerly.]"
        ),
        f"CEPHALUS: {ceph1}",
        f"SOCRATES: {soc1}",
        f"CEPHALUS: {ceph2}",
        "[Socrates listened in admiration, and wanting to draw him out, that he might go on:]",
        f"SOCRATES: {soc2}",
        f"CEPHALUS: {ceph3}",
        f"SOCRATES: {soc3}",
        f"CEPHALUS: {ceph4}",
        f"SOCRATES: {soc4}",
        "CEPHALUS: That is true.",
        f"SOCRATES: {soc5}",
        f"CEPHALUS: {ceph5}",
    ]


def relabel(block: str, speaker: str) -> str:
    return f"{speaker}: {block.split(': ', 1)[1]}"


def body(block: str) -> str:
    return block.split(": ", 1)[1]


def third_person(text: str, pairs: list[tuple[str, str]]) -> str:
    for a, b in pairs:
        if a not in text:
            raise SystemExit(f"expected {a!r} in narration: {text[:60]}")
        text = text.replace(a, b)
    return text


def assemble(lines: list[str]) -> str:
    start = next(i for i, l in enumerate(lines) if l.strip() == "BOOK I" and i > 10)
    end = next(i for i, l in enumerate(lines) if l.strip() == "BOOK II" and i > start)
    book = lines[start + 1 : end]
    raw = convert(book).strip().split("\n\n")
    b = {i + 1: blk for i, blk in enumerate(raw)}  # 1-based, as in the review overview

    out = opening(book)
    out += [b[37], b[38], b[39], b[40], b[41], "SOCRATES: Is not Polemarchus your heir?",
            "CEPHALUS: To be sure.", "[Cephalus goes away laughing to the sacrifices.]",
            b[44], b[45]]

    fixes: dict[int, str | list[str] | None] = {
        128: [b[128].removesuffix(" True."), "POLEMARCHUS: True."],
        129: relabel(b[129], "SOCRATES"), 130: relabel(b[130], "POLEMARCHUS"),
        131: relabel(b[131], "SOCRATES"), 132: relabel(b[132], "POLEMARCHUS"),
        133: relabel(b[133], "SOCRATES"), 134: relabel(b[134], "POLEMARCHUS"),
        135: relabel(b[135], "SOCRATES"), 136: relabel(b[136], "POLEMARCHUS"),
        137: relabel(b[137], "SOCRATES"),
        138: None,
        139: "POLEMARCHUS: Very true; " + body(b[139]),
        187: "[" + third_person(body(b[187]), [
            ("Polemarchus and I had done", "Polemarchus and Socrates had done"),
            ("came at us", "came at them"), ("devour us", "devour them"),
            ("We were quite panic-stricken", "All were quite panic-stricken"),
        ]) + " He roared out to the whole company:]",
        188: None,
        189: relabel(b[189], "THRASYMACHUS"),
        190: "[" + third_person(body(b[190]), [
            ("I was panic-stricken", "Socrates was panic-stricken"),
            ("Indeed I believe that if I had not fixed my eye upon him, I should have been struck dumb",
             "Indeed, if he had not fixed his eye upon him, he would have been struck dumb"),
            ("when I saw his fury rising, I looked at him first", "when he saw his fury rising, he looked at him first"),
        ]) + "]",
        191: b[191].replace("Thrasymachus with a quiver, don't", "Thrasymachus, don't"),
        192: ["[With a bitter laugh.]",
              b[192].replace("How characteristic of Socrates! with a bitter laugh; --that's", "How characteristic of Socrates! That's")],
        205: ["[" + third_person(body(b[205]).split(" Behold the wisdom", 1)[0], [
                  ("joined in my request", "joined in the request"),
                  ("But at first he to insist on my answering", "But at first he affected to insist on Socrates answering"),
              ]) + "]",
              "THRASYMACHUS: Behold the wisdom" + body(b[205]).split(" Behold the wisdom", 1)[1]],
        236: b[236].replace("Yes interposing, if", "Yes, if"),
        238: relabel(b[238], "CLEITOPHON"), 239: relabel(b[239], "POLEMARCHUS"),
        245: relabel(b[245], "THRASYMACHUS"), 246: relabel(b[246], "SOCRATES"),
        275: "[Thrasymachus assents, with a good deal of reluctance.]",
        277: "[He makes an attempt to contest this proposition also, but finally acquiesces.]",
        278: b[278].replace("Then, I continued, no physician", "Then no physician"),
        283: ["[Reluctantly.]", "THRASYMACHUS: Yes."],
        285: "[When they had got to this point in the argument, and every one saw that the definition "
             "of justice had been completely upset, Thrasymachus, instead of replying, said:]",
        290: relabel(b[290], "THRASYMACHUS"),
        291: ["[" + third_person(body(b[291]).split(" Thrasymachus to him, excellent man", 1)[0], [
                  ("deluged our ears", "deluged their ears"),
                  ("and I myself added my own humble request that he would not leave us",
                   "and Socrates added his own humble request that he would not leave them"),
              ]) + "]",
              "SOCRATES: Thrasymachus, excellent man" + body(b[291]).split(" Thrasymachus to him, excellent man", 1)[1]],
        312: "[He gives a reluctant assent.]",
        317: b[317] + " " + body(b[318]),
        318: None,
        345: b[345] + " " + body(b[346]),
        346: None,
        403: b[403].replace("the lust will not", "the just will not"),
        410: "[" + third_person(body(b[410]), [
            ("as I repeat them", "as they are set down here"),
            ("and then I saw what I had never seen before", "and then Socrates saw what he had never seen before"),
            ("As we were now agreed", "As they were now agreed"),
            ("I proceeded to another point:", "Socrates proceeded to another point."),
        ]) + "]",
        417: b[417].replace("the question which before", "the question which I asked before"),
    }
    for n in range(46, len(raw) + 1):
        if n in fixes:
            fix = fixes[n]
            if fix is None:
                continue
            out += fix if isinstance(fix, list) else [fix]
        else:
            out.append(b[n])
    text = "\n\n".join(out) + "\n"
    for a, c in [("?.", "?"), ("!.", "!"), ("!;", "!"), ("?;", "?"), ("!:", "!"),
                 ("understand you. justice", "understand you. Justice")]:
        text = text.replace(a, c)
    return text


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[2] == "--final":
    sys.stdout.write(assemble(Path(sys.argv[1]).read_text().splitlines()))
