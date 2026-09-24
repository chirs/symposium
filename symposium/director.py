"""Who speaks next. Scripted dialogues follow their script; sandboxes ask a small model."""

from __future__ import annotations

import os

import anthropic

from symposium.dialogue import Dialogue
from symposium.script import ROOT, Script

DEFAULT_DIRECTOR_MODEL = "claude-haiku-4-5"
TAIL = 8


def director_model() -> str:
    return os.environ.get("SYMPOSIUM_DIRECTOR_MODEL", DEFAULT_DIRECTOR_MODEL)


def parse_choice(text: str, cast: list[str]) -> str | None:
    """The cast member named earliest in the reply, if any."""
    lower = text.lower()
    hits = [(lower.find(name), name) for name in cast if name in lower]
    return min(hits)[1] if hits else None


def choose_speaker(
    dialogue: Dialogue, script: Script, client: anthropic.Anthropic | None = None
) -> str:
    if not script.sandbox:
        return script.next_speaker(dialogue)
    cast = script.characters
    spoken = [e for e in dialogue.exchanges if not e.is_stage]
    if not spoken:
        return cast[0]
    transcript = "\n\n".join(e.as_text() for e in spoken[-TAIL:])
    names = ", ".join(c.upper() for c in cast)
    client = client or anthropic.Anthropic()
    try:
        reply = client.messages.create(
            model=director_model(),
            max_tokens=50,
            system=(ROOT / "prompts" / "director.md").read_text().strip(),
            messages=[{
                "role": "user",
                "content": f"{transcript}\n\nWho speaks next? Answer with one name from: {names}.",
            }],
        )
        text = "".join(b.text for b in reply.content if b.type == "text")
    except (anthropic.APIError, TypeError):
        return script.next_speaker(dialogue)
    return parse_choice(text, cast) or script.next_speaker(dialogue)
