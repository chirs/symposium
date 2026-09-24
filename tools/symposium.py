"""Turn the Symposium (narrated by Apollodorus after Aristodemus) into script form.

The frame and the walk to Agathon's are dropped; the script begins as Aristodemus
arrives. Each corpus paragraph is handled by line number; narration becomes bracketed
stage directions in the third person.

    .venv/bin/python tools/symposium.py corpus/symposium.txt > dialogues/symposium/seed.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAMES = "he|she|Agathon|Socrates|Eryximachus|Aristophanes|Phaedrus|Pausanias|Alcibiades|Aristodemus|my informant"
TAIL = re.compile(
    rf",?\s+(?:said|replied|rejoined|added|cried|answered)\s+(?:{NAMES})"
    r"(?:,? the son of Acumenus| the Myrrhinusian)?([,;:.!?])?"
)
HEAD = re.compile(rf"^(?:Then |And )?(?:{NAMES})\s+(?:said|replied|added|answered)[:,!]?\s*")
MID = re.compile(r",?\s+(?:he|she) (?:said|replied|answered)([,;:.!?])?")


def cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def speech(speaker: str, text: str, **subs: str) -> str:
    for a, b in subs.items():
        if a not in text:
            raise SystemExit(f"expected {a!r} in line for {speaker}: {text[:60]}")
        text = text.replace(a, b)
    text = HEAD.sub("", text)
    text = TAIL.sub(lambda m: m.group(1) or "", text)
    text = MID.sub(lambda m: m.group(1) or "", text)
    for a, b in [("?;", "?"), ("!;", "!"), ("!,", "!"), ("?,", "?"), ("  ", " ")]:
        text = text.replace(a, b)
    return f"{speaker}: {text.strip()}"


def direction(text: str) -> str:
    return f"[{text.strip()}]"


def convert(lines: list[str]) -> str:
    L = lambda n: lines[n - 1].strip()
    out: list[str] = []
    add = out.append

    # --- arrival
    add(direction(
        "On the way to the banquet Socrates dropped behind in a fit of abstraction, and desired "
        "Aristodemus, who was waiting, to go on before him. When Aristodemus reached the house of "
        "Agathon he found the doors wide open, and a comical thing happened. A servant coming out "
        "met him, and led him at once into the banqueting-hall in which the guests were reclining, "
        "for the banquet was about to begin."
    ))
    add(speech("AGATHON", "Welcome, Aristodemus; " + L(60).split("as soon as he appeared-", 1)[1]))
    add(direction(
        "Aristodemus turned round, but Socrates was nowhere to be seen; and he had to explain that "
        "Socrates had been with him a moment before, and that he came by his invitation to the supper."
    ))
    add(speech("AGATHON", L(64)))
    add(speech("ARISTODEMUS", L(66)))
    add(speech("AGATHON", L(68)))
    add(direction(L(70).replace("our friend Socrates", "Socrates")))
    add(speech("AGATHON", L(72)))
    add(speech("ARISTODEMUS", L(74)))
    add(speech("AGATHON", "Well, if you think so, I will leave him."))
    add(direction("Then, turning to the servants:"))
    add(speech("AGATHON", L(76).split('"', 2)[1], **{"for there; is": "for there is", "you art our hosts": "you are our hosts"}))
    add(direction(
        "After this, supper was served, but still no Socrates; and during the meal Agathon several "
        "times expressed a wish to send for him, but Aristodemus objected; and at last when the feast "
        "was about half over, for the fit, as usual, was not of long duration, Socrates entered. "
        "Agathon, who was reclining alone at the end of the table, begged that he would take the "
        "place next to him."
    ))
    add(speech("AGATHON", "Here, Socrates, that I may touch you, and have the benefit" + L(76).split('"and have the benefit', 1)[1].replace('"', "")))
    add(direction("Socrates takes his place as he is desired."))
    add(speech("SOCRATES", L(78).replace("How I wish, said Socrates, taking his place as he was desired, that", "How I wish that")))
    add(speech("AGATHON", L(80)))
    pre, _, paus = L(82).partition("when Pausanias said, ")
    add(direction(pre.replace("they were about to commence drinking, ", "they were about to commence drinking.")))
    add(speech("PAUSANIAS", paus))
    add(speech("ARISTOPHANES", L(84).replace("I entirely agree, said Aristophanes, that", "I entirely agree that")))
    add(speech("ERYXIMACHUS", L(86)))
    add(speech("AGATHON", L(88)))
    add(speech("ERYXIMACHUS", L(90).replace("Then, the Eryximachus, the weak heads", "Then the weak heads")))
    add(speech("PHAEDRUS", L(92)))
    add(direction(L(94)))
    proposal = L(96).replace("Then, said Eryximachus, as you", "As you")
    proposal = proposal.split(" This proposal having been accepted", 1)[0]
    proposal += " " + L(98).replace("I will begin, he said, after", "I will begin after") + ' "' + L(100) + '" ' + L(101)
    add(speech("ERYXIMACHUS", proposal))
    soc, _, assent = L(102).partition(" All the company expressed their assent")
    add(speech("SOCRATES", soc))
    add(direction("All the company expressed their assent" + assent))

    # --- the speeches
    add(speech("PHAEDRUS", "\n\n".join([
        L(106).replace("Phaedrus began by affirming that love is a mighty god", "Love is a mighty god"),
        L(108), L(109), L(110), L(111), L(112), L(113), L(114),
    ])))
    add(direction("Some other speeches followed which Aristodemus did not remember; the next was that of Pausanias."))
    add(speech("PAUSANIAS", "\n\n".join([
        L(116).split("was that of Pausanias. ", 1)[1].replace("Phaedrus, he said, the argument", "Phaedrus, the argument"),
        L(118), L(120), L(122), L(124), L(126), L(128),
    ])))
    add(direction(
        "Pausanias came to a pause. The turn of Aristophanes was next, but either he had eaten too "
        "much, or from some other cause he had the hiccough, and was obliged to change turns with "
        "Eryximachus the physician, who was reclining on the couch below him."
    ))
    add(speech("ARISTOPHANES", L(130).split("below him. ", 1)[1].replace("Eryximachus, he said, you", "Eryximachus, you")))
    eryx, _, arist = L(132).partition(" I will do as you prescribe")
    add(speech("ERYXIMACHUS", eryx))
    add(speech("ARISTOPHANES", "I will do as you prescribe" + arist))
    add(speech("ERYXIMACHUS", "\n\n".join([L(134).replace("Eryximachus spoke as follows: ", ""), L(136), L(138)])))
    add(speech("ARISTOPHANES", L(140).replace("Yes, said Aristophanes, who followed, the hiccough", "Yes, the hiccough")))
    add(speech("ERYXIMACHUS", L(142)))
    add(direction("Laughing."))
    add(speech("ARISTOPHANES", L(144).replace("You are right, said Aristophanes, laughing. I will", "You are right. I will")))
    add(speech("ERYXIMACHUS", L(146)))
    add(speech("ARISTOPHANES", "\n\n".join([
        L(148).replace(
            "Aristophanes professed to open another vein of discourse; he had a mind to praise Love in another way",
            "I have a mind to praise Love in another way",
        ).replace("Mankind; he said, judging", "Mankind, judging"),
        L(150), L(152), L(154),
    ])))
    add(speech("ERYXIMACHUS", L(156)))
    add(speech("SOCRATES", L(158)))
    add(speech("AGATHON", L(160)))
    add(speech("SOCRATES", L(162).replace("Agathon replied Socrates,", "Agathon,")))
    add(speech("AGATHON", L(164)))
    add(speech("SOCRATES", L(166)))
    add(speech("AGATHON", L(168)))
    add(speech("SOCRATES", L(170)))
    add(speech("PHAEDRUS", L(172).replace("Here Phaedrus interrupted them, saying: not answer him", "Do not answer him")))
    add(speech("AGATHON", "\n\n".join([L(174), L(176), L(178), L(180), L(181), L(182), L(183), L(185), L(186), L(187)])))
    add(direction(
        "When Agathon had done speaking, there was a general cheer; the young man was thought to have "
        "spoken in a manner worthy of himself, and of the god. Socrates looked at Eryximachus."
    ))
    add(speech("SOCRATES", L(188).split("looking at Eryximachus, said: ", 1)[1]))
    add(speech("ERYXIMACHUS", L(190).replace("concerns Agathon, replied Eryximachus, appears", "concerns Agathon appears")))
    add(speech("SOCRATES", L(192)))
    add(direction("Phaedrus and the company bid him speak in any manner which he thought best."))
    add(speech("SOCRATES", cap(L(194).split("Then, he added, ", 1)[1])))
    add(speech("PHAEDRUS", L(196).split(" Socrates then proceeded", 1)[0]))
    turns = {204: "dir", 260: "dir"}
    for n in range(198, 286, 2):
        if turns.get(n) == "dir":
            add(direction("Agathon assents."))
        else:
            add(speech("SOCRATES" if n % 4 == 2 else "AGATHON", L(n)))
    add(speech("SOCRATES", "\n\n".join([L(286)] + [L(n) for n in range(288, 310, 2)])))

    # --- Alcibiades
    add(direction(L(310).split(' "If they are friends', 1)[0]))
    add(speech("AGATHON", "If they are friends of ours, invite them in, but if not, say that the drinking is over."))
    add(direction(
        "A little while afterwards they heard the voice of Alcibiades resounding in the court; he "
        "was in a great state of intoxication and kept roaring and shouting."
    ))
    add(speech("ALCIBIADES", "Where is Agathon? Lead me to Agathon."))
    add(direction(
        "At length, supported by the flute-girl and some of his attendants, he found his way to them, "
        "appearing at the door crowned with a massive garland of ivy and violets, his head flowing with ribands."
    ))
    add(speech("ALCIBIADES", "Hail, friends! Will you have" + L(310).split('"Will you have', 1)[1].replace('"', "").rstrip()))
    add(direction(L(312).split(" Take off his sandals", 1)[0]))
    add(speech("AGATHON", "Take off his sandals, and let him make a third on the same couch."))
    add(speech("ALCIBIADES", "By all means; but who makes the third partner in our revels?"))
    add(direction("Turning round and starting up as he caught sight of Socrates."))
    add(speech("ALCIBIADES", "By Heracles, " + L(314).split("By Heracles, he said, ", 1)[1]))
    add(speech("SOCRATES", L(316).replace("Socrates turned to Agathon and said: ", "")))
    alc, _, crown = L(318).partition(" Whereupon, taking")
    add(speech("ALCIBIADES", alc.replace("Agathoron", "Agathon")))
    add(direction("Whereupon, taking" + crown))
    alc, _, rest = L(320).partition(" The wine-cooler which")
    add(speech("ALCIBIADES", alc.replace("Then he said: ", "").replace("or rather, he said, addressing the attendant, bring", "or rather, boy, bring")))
    cooler, _, rest = ("The wine-cooler which" + rest).partition(" Observe, my friends")
    add(direction(cooler))
    observe, _, drank = ("Observe, my friends" + rest).partition(" Socrates drank")
    add(speech("ALCIBIADES", observe))
    add(direction("Socrates drank" + drank))
    add(speech("ERYXIMACHUS", L(322).replace("Eryximachus said! ", "")))
    add(speech("ALCIBIADES", L(324)))
    add(speech("ERYXIMACHUS", L(326)))
    add(speech("ALCIBIADES", L(328) + ' "' + L(330) + '" ' + L(331)))
    add(speech("ERYXIMACHUS", L(332)))
    add(speech("ALCIBIADES", L(334)))
    add(speech("SOCRATES", L(336)))
    add(speech("ALCIBIADES", L(338)))
    add(speech("ERYXIMACHUS", L(340)))
    add(speech("ALCIBIADES", L(342).replace("What do you think, Eryximachus-? said Alcibiades: shall", "What do you think, Eryximachus? Shall")))
    add(speech("SOCRATES", L(344)))
    add(speech("ALCIBIADES", L(346)))
    add(speech("SOCRATES", L(348)))
    add(speech("ALCIBIADES", "\n\n".join([L(350)] + [L(n) for n in range(352, 364, 2)])))
    laugh, _, soc = L(364).partition(" You are sober, Alcibiades")
    add(direction(laugh))
    add(speech("SOCRATES", "You are sober, Alcibiades" + soc))
    add(speech("AGATHON", L(366)))
    add(speech("SOCRATES", L(368)))
    add(speech("ALCIBIADES", L(370)))
    add(speech("SOCRATES", L(372)))
    add(speech("AGATHON", L(374)))
    add(speech("ALCIBIADES", L(376)))
    add(direction(L(378).replace(
        "Aristodemus said that Eryximachus, Phaedrus, and others went away-he himself fell asleep",
        "Eryximachus, Phaedrus, and others went away; Aristodemus himself fell asleep",
    )))
    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(convert(Path(sys.argv[1]).read_text().splitlines()))
