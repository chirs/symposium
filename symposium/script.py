"""Scripted turn order: which character speaks next."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from symposium.dialogue import Dialogue

ROOT = Path(__file__).resolve().parent.parent
DIALOGUES = ROOT / "dialogues"
SHARED = ROOT / "prompts" / "characters"  # prompts for characters who recur across dialogues
COLLECTIONS = ("Plato", "New Testament")  # landing-page order; unknown collections come last


@dataclass
class Phase:
    name: str
    speakers: list[str]
    length: int


@dataclass
class Script:
    title: str
    phases: list[Phase]
    setting: str = ""
    scene: str = ""
    dir: Path | None = None  # the dialogue directory: script.json, seed.md, prompts/
    sandbox: bool = False  # a user-made conversation: prompts borrowed, speaker chosen by the director
    cast: dict[str, str] = field(default_factory=dict)  # speaker -> dialogue whose prompt to use
    collection: str = ""  # "Plato", "New Testament": how the landing page groups dialogues
    guests: dict[str, str] = field(default_factory=dict)  # invited into this run: speaker -> source

    @classmethod
    def load(cls, path: Path) -> Script:
        data = json.loads(path.read_text())
        phases = [Phase(p["name"], p["speakers"], p["length"]) for p in data["phases"]]
        return cls(
            data["title"],
            phases,
            data.get("setting", ""),
            data.get("scene", ""),
            path.parent,
            data.get("sandbox", False),
            data.get("cast", {}),
            data.get("collection", ""),
        )

    def prompt_path(self, speaker: str) -> Path:
        """A cast or guest entry's source, else the dialogue's own prompt, else the shared pool."""
        source = self.cast.get(speaker) or self.guests.get(speaker)
        if source:
            return source_prompt(self.dir.parent, speaker, source)
        local = self.dir / "prompts" / f"{speaker}.md"
        return local if local.exists() else SHARED / f"{speaker}.md"

    @property
    def speakers(self) -> list[str]:
        """The scripted characters plus any guests, in order of arrival."""
        return self.characters + [g for g in self.guests if g not in self.characters]

    @property
    def directed(self) -> bool:
        """No script covers this company, so a director picks the next speaker."""
        return self.sandbox or bool(self.guests)

    @classmethod
    def named(cls, name: str, root: Path = DIALOGUES) -> Script:
        return cls.load(root / name / "script.json")

    @classmethod
    def discover(cls, root: Path = DIALOGUES) -> list[Script]:
        scripts = [cls.load(p) for p in root.glob("*/script.json")]
        return sorted(scripts, key=lambda s: (s.sandbox, s.rank, s.name))

    @property
    def rank(self) -> int:
        return COLLECTIONS.index(self.collection) if self.collection in COLLECTIONS else len(COLLECTIONS)

    @property
    def name(self) -> str:
        return self.dir.name if self.dir else ""

    @property
    def characters(self) -> list[str]:
        seen: list[str] = []
        for p in self.phases:
            seen += [s for s in p.speakers if s not in seen]
        return seen

    def phase_at(self, turn: int) -> Phase:
        """The phase containing the `turn`-th scripted exchange (0-based). Last phase repeats."""
        start = 0
        for p in self.phases:
            if turn < start + p.length:
                return p
            start += p.length
        return self.phases[-1]

    def next_speaker(self, dialogue: Dialogue) -> str:
        cycle = self.speakers if self.guests else self.phase_at(dialogue.turn_count).speakers
        last = dialogue.last_speaker
        if last in cycle:
            return cycle[(cycle.index(last) + 1) % len(cycle)]
        return cycle[0]


def source_prompt(root: Path, speaker: str, source: str) -> Path:
    """Where a borrowed character's prompt lives: the shared pool or another dialogue."""
    if source == "shared":
        return SHARED / f"{speaker}.md"
    return root / source / "prompts" / f"{speaker}.md"
