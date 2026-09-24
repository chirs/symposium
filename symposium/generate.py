"""One API call: the character's system prompt plus the transcript yields the next speech."""

from __future__ import annotations

import os
import re
from collections.abc import Callable

import anthropic

from symposium.dialogue import Dialogue
from symposium.script import ROOT

PROMPTS = ROOT / "prompts"
DEFAULT_MODEL = "claude-opus-5"
MARKER = "# System Prompt"


class GenerationError(Exception):
    pass


def model_id() -> str:
    return os.environ.get("SYMPOSIUM_MODEL", DEFAULT_MODEL)


def character_prompt(speaker: str) -> str:
    path = PROMPTS / f"{speaker}.md"
    if not path.exists():
        raise GenerationError(f"no prompt for {speaker!r} at {path}")
    text = path.read_text()
    if MARKER not in text:
        raise GenerationError(f"{path} has no '{MARKER}' section")
    return text.split(MARKER, 1)[1].strip()


def system_prompt(speaker: str) -> str:
    preamble = (PROMPTS / "orchestration.md").read_text().strip()
    return f"{preamble}\n\n---\n\n{character_prompt(speaker)}"


def cue(speaker: str) -> str:
    return (
        f"Speak next as {speaker.upper()}. "
        "Give only the words spoken, with no label and no stage directions."
    )


def user_content(dialogue: Dialogue, speaker: str) -> list[dict]:
    """One block per exchange so prompt caching can reuse the growing transcript."""
    blocks: list[dict] = [{"type": "text", "text": "The dialogue so far:"}]
    blocks += [{"type": "text", "text": f"{e.speaker}: {e.text}"} for e in dialogue.exchanges]
    blocks[-1]["cache_control"] = {"type": "ephemeral"}
    blocks.append({"type": "text", "text": cue(speaker)})
    return blocks


def clean(text: str, speaker: str) -> str:
    text = text.strip()
    return re.sub(rf"^{re.escape(speaker)}\s*:\s*", "", text, count=1, flags=re.IGNORECASE)


def request_params(dialogue: Dialogue, speaker: str) -> dict:
    params = {
        "model": model_id(),
        "max_tokens": 16000,
        "system": system_prompt(speaker),
        "messages": [{"role": "user", "content": user_content(dialogue, speaker)}],
    }
    if effort := os.environ.get("SYMPOSIUM_EFFORT"):
        params["output_config"] = {"effort": effort}
    return params


def generate(
    dialogue: Dialogue,
    speaker: str,
    client: anthropic.Anthropic | None = None,
    on_text: Callable[[str], None] | None = None,
) -> str:
    """Return the next speech for `speaker`. Streams text to `on_text` as it arrives."""
    client = client or anthropic.Anthropic()
    with client.messages.stream(**request_params(dialogue, speaker)) as stream:
        for text in stream.text_stream:
            if on_text:
                on_text(text)
        message = stream.get_final_message()
    if message.stop_reason != "end_turn":
        raise GenerationError(f"generation stopped early: {message.stop_reason}")
    return clean("".join(b.text for b in message.content if b.type == "text"), speaker)
