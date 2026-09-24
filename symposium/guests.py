"""Characters invited into a run of a dialogue they were not written into."""

from __future__ import annotations

import json
from pathlib import Path

from symposium.dialogue import Dialogue, Exchange
from symposium.script import Script, source_prompt


def path_for(run: Path) -> Path:
    return run.with_name(f"{run.stem}.guests.json")


def load(run: Path) -> dict[str, str]:
    p = path_for(run)
    return json.loads(p.read_text()) if p.exists() else {}


def save(run: Path, guests: dict[str, str]) -> None:
    p = path_for(run)
    if guests:
        p.write_text(json.dumps(guests, indent=2) + "\n")
    elif p.exists():
        p.unlink()


def attach(script: Script, run: Path) -> None:
    """Give the script the guests recorded for this run."""
    script.guests = load(run)


def clear(script: Script, run: Path) -> None:
    script.guests = {}
    save(run, {})


def display(speaker: str) -> str:
    return speaker[:1].upper() + speaker[1:]


def invite(
    dialogue: Dialogue, script: Script, run: Path, speaker: str, source: str, at: int | None = None
) -> Exchange:
    """Bring `speaker` (whose prompt lives in `source`) into the company after `at` exchanges."""
    speaker = speaker.lower().strip()
    if speaker in script.speakers or speaker in script.cast:
        raise ValueError(f"{display(speaker)} is already present")
    if not source_prompt(script.dir.parent, speaker, source).exists():
        raise ValueError(f"no prompt for {speaker} in {source}")
    e = dialogue.insert_direction(f"{display(speaker)} has come in and joined the company.", at)
    script.guests[speaker] = source
    save(run, script.guests)
    return e
