"""Scripted turn order: which character speaks next."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from symposium.dialogue import Dialogue

ROOT = Path(__file__).resolve().parent.parent
DIALOGUES = ROOT / "dialogues"


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
        )

    def prompt_path(self, speaker: str) -> Path:
        if speaker in self.cast:
            return self.dir.parent / self.cast[speaker] / "prompts" / f"{speaker}.md"
        return self.dir / "prompts" / f"{speaker}.md"

    @classmethod
    def named(cls, name: str, root: Path = DIALOGUES) -> Script:
        return cls.load(root / name / "script.json")

    @classmethod
    def discover(cls, root: Path = DIALOGUES) -> list[Script]:
        return [cls.load(p) for p in sorted(root.glob("*/script.json"))]

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
        cycle = self.phase_at(dialogue.turn_count).speakers
        last = dialogue.last_speaker
        if last in cycle:
            return cycle[(cycle.index(last) + 1) % len(cycle)]
        return cycle[0]
