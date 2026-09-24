"""A dialogue is a list of exchanges, stored as a plain text script."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

STRANGER = "THE STRANGER"
STAGE = ""  # the "speaker" of a stage direction, written as a bracketed paragraph
LABEL = re.compile(r"^([A-Z][A-Z' -]*[A-Z]):[ \t]*(.*)$")
DIRECTION = re.compile(r"^\[(.+)\]$")


@dataclass
class Exchange:
    speaker: str  # display form: "SOCRATES", "THE STRANGER"
    text: str

    @property
    def key(self) -> str:
        return self.speaker.lower()

    @property
    def is_stranger(self) -> bool:
        return self.speaker == STRANGER

    @property
    def is_stage(self) -> bool:
        return self.speaker == STAGE

    @property
    def is_scripted(self) -> bool:
        """Counts toward the turn order: a character's speech, not the Stranger's or a direction."""
        return not self.is_stranger and not self.is_stage

    def as_text(self) -> str:
        return f"[{self.text}]" if self.is_stage else f"{self.speaker}: {self.text}"


def parse(source: str) -> list[Exchange]:
    exchanges: list[Exchange] = []
    speaker = None
    lines: list[str] = []

    def flush() -> None:
        if speaker is not None:
            exchanges.append(Exchange(speaker, "\n".join(lines).strip()))

    for line in source.splitlines():
        if m := DIRECTION.match(line):
            flush()
            exchanges.append(Exchange(STAGE, m.group(1).strip()))
            speaker, lines = None, []
        elif m := LABEL.match(line):
            flush()
            speaker, lines = m.group(1), [m.group(2)]
        elif speaker is not None:
            lines.append(line)
        elif line.strip():
            raise ValueError(f"text outside any speech or direction: {line!r}")
    flush()
    return exchanges


def format(exchanges: list[Exchange]) -> str:
    return "\n\n".join(e.as_text() for e in exchanges) + "\n"


def original_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.original{path.suffix}")


@dataclass
class Dialogue:
    exchanges: list[Exchange] = field(default_factory=list)
    original: list[Exchange] | None = None  # the path before the first interjection

    @classmethod
    def parse(cls, source: str) -> Dialogue:
        return cls(parse(source))

    @classmethod
    def load(cls, path: Path) -> Dialogue:
        d = cls.parse(path.read_text())
        snapshot = original_path(path)
        if snapshot.exists():
            d.original = parse(snapshot.read_text())
        return d

    def save(self, path: Path) -> None:
        path.write_text(self.format())
        snapshot = original_path(path)
        if self.original is not None:
            snapshot.write_text(format(self.original))
        elif snapshot.exists():
            snapshot.unlink()

    def format(self) -> str:
        return format(self.exchanges)

    def append(self, speaker: str, text: str) -> Exchange:
        e = Exchange(speaker.upper(), text.strip())
        self.exchanges.append(e)
        return e

    def diverge(self, exchange: Exchange, at: int | None = None) -> Exchange:
        """Insert `exchange` after the first `at` exchanges and discard the rest."""
        if at is None:
            at = len(self.exchanges)
        if not 0 <= at <= len(self.exchanges):
            raise ValueError(f"at={at} out of range (0..{len(self.exchanges)})")
        if self.original is None:
            self.original = list(self.exchanges)
        self.exchanges = self.exchanges[:at] + [exchange]
        return exchange

    def interject(self, text: str, at: int | None = None) -> Exchange:
        """The Stranger speaks after the first `at` exchanges; the rest is discarded."""
        return self.diverge(Exchange(STRANGER, text.strip()), at)

    def insert_direction(self, text: str, at: int | None = None) -> Exchange:
        """A stage direction after the first `at` exchanges; the rest is discarded."""
        return self.diverge(Exchange(STAGE, text.strip()), at)

    def revert(self) -> None:
        if self.original is None:
            raise ValueError("no original path to return to")
        self.exchanges, self.original = self.original, None

    @property
    def has_original(self) -> bool:
        return self.original is not None

    @property
    def last_speaker(self) -> str | None:
        for e in reversed(self.exchanges):
            if e.is_scripted:
                return e.key
        return None

    @property
    def turn_count(self) -> int:
        """Exchanges that count toward the script: not The Stranger's, not directions."""
        return sum(1 for e in self.exchanges if e.is_scripted)
