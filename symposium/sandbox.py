"""User-made conversations: a dialogue directory whose prompts are borrowed from others."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from symposium import script as script_module
from symposium.dialogue import STRANGER
from symposium.script import DIALOGUES, Script

SLUG = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    return SLUG.sub("-", title.lower()).strip("-")


def catalog(root: Path | None = None) -> list[dict]:
    """Every character prompt on disk, with the dialogue it belongs to."""
    out = []
    for s in Script.discover(root or DIALOGUES):
        if s.sandbox:
            continue
        for p in sorted((s.dir / "prompts").glob("*.md")):
            out.append({"speaker": p.stem, "dialogue": s.name, "title": s.title})
    for p in sorted(script_module.SHARED.glob("*.md")):
        out.append({"speaker": p.stem, "dialogue": "shared", "title": "Shared"})
    return out


def create(
    title: str,
    cast: list[tuple[str, str]],
    setting: str,
    scene: str,
    opening: str = "",
    root: Path | None = None,
) -> Script:
    """Write dialogues/sandbox-<slug>/ with a script borrowing each (speaker, dialogue) prompt."""
    root = root or DIALOGUES
    slug = slugify(title)
    if not slug:
        raise ValueError("a title is needed")
    if not cast:
        raise ValueError("choose at least one character")
    speakers: list[str] = []
    sources: dict[str, str] = {}
    for speaker, source in cast:
        speaker = speaker.lower()
        if speaker in sources:
            raise ValueError(f"{speaker} is listed twice")
        prompt = (script_module.SHARED if source == "shared" else root / source / "prompts") / f"{speaker}.md"
        if not prompt.exists():
            raise ValueError(f"no prompt for {speaker} in {source}")
        speakers.append(speaker)
        sources[speaker] = source
    d = root / f"sandbox-{slug}"
    if d.exists():
        raise ValueError(f"{d.name} already exists")
    d.mkdir()
    (d / "script.json").write_text(json.dumps({
        "title": title.strip(),
        "setting": setting.strip(),
        "scene": scene.strip(),
        "sandbox": True,
        "cast": sources,
        "phases": [{"name": "all", "speakers": speakers, "length": 1}],
    }, indent=2) + "\n")
    present = ", ".join(s.capitalize() for s in speakers)
    seed = f"[{setting.strip().rstrip('.')}. Present: {present}.]\n"
    if opening.strip():
        seed += f"\n{STRANGER}: {opening.strip()}\n"
    (d / "seed.md").write_text(seed)
    return Script.load(d / "script.json")


def remove(script: Script) -> None:
    if not script.sandbox:
        raise ValueError(f"{script.name} is not a sandbox")
    shutil.rmtree(script.dir)
