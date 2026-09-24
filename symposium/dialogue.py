"""A dialogue is a list of exchanges, stored as a plain text script."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

STRANGER = "THE STRANGER"
LABEL = re.compile(r"^([A-Z][A-Z' -]*[A-Z]):[ \t]*(.*)$")


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


def parse(source: str) -> list[Exchange]:
    exchanges: list[Exchange] = []
    speaker = None
    lines: list[str] = []
    for line in source.splitlines():
        m = LABEL.match(line)
        if m:
            if speaker is not None:
                exchanges.append(Exchange(speaker, "\n".join(lines).strip()))
            speaker, lines = m.group(1), [m.group(2)]
        elif speaker is not None:
            lines.append(line)
        elif line.strip():
            raise ValueError(f"text before first speaker label: {line!r}")
    if speaker is not None:
        exchanges.append(Exchange(speaker, "\n".join(lines).strip()))
    return exchanges


def format(exchanges: list[Exchange]) -> str:
    return "\n\n".join(f"{e.speaker}: {e.text}" for e in exchanges) + "\n"


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

    def interject(self, text: str, at: int | None = None) -> Exchange:
        """Insert The Stranger after the first `at` exchanges and discard the rest."""
        if at is None:
            at = len(self.exchanges)
        if not 0 <= at <= len(self.exchanges):
            raise ValueError(f"at={at} out of range (0..{len(self.exchanges)})")
        if self.original is None:
            self.original = list(self.exchanges)
        e = Exchange(STRANGER, text.strip())
        self.exchanges = self.exchanges[:at] + [e]
        return e

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
            if not e.is_stranger:
                return e.key
        return None

    @property
    def turn_count(self) -> int:
        """Exchanges that count toward the script, i.e. not The Stranger's."""
        return sum(1 for e in self.exchanges if not e.is_stranger)
