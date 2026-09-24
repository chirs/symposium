"""JSON API over one in-memory Dialogue, plus the reading page."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from symposium import generate as gen
from symposium.dialogue import Dialogue
from symposium.script import DIALOGUES, ROOT, Script

WEB = ROOT / "web"


class NextBody(BaseModel):
    speaker: str | None = None


class InterjectBody(BaseModel):
    text: str
    at: int | None = None


def build_app(
    path: Path | None = None,
    name: str = "republic-1",
    generate: Callable[[Dialogue, str, Script], str] = gen.generate,
) -> FastAPI:
    if path is not None:
        dialogue = Dialogue.load(path)
        local = path.parent / "script.json"
        script = Script.load(local) if local.exists() else Script.named(name)
    else:
        dialogue = Dialogue.parse((DIALOGUES / name / "seed.md").read_text())
        script = Script.named(name)
    lock = threading.Lock()
    app = FastAPI(title="Symposium")

    def save() -> None:
        if path is not None:
            dialogue.save(path)

    def state() -> dict:
        return {
            "title": script.title,
            "setting": script.setting,
            "characters": [c.upper() for c in script.characters],
            "exchanges": [{"speaker": e.speaker, "text": e.text} for e in dialogue.exchanges],
            "has_original": dialogue.has_original,
            "next_speaker": script.next_speaker(dialogue).upper(),
        }

    @app.get("/")
    def index():
        return FileResponse(WEB / "index.html")

    @app.get("/api/dialogue")
    def get_dialogue():
        return state()

    @app.post("/api/next")
    def post_next(body: NextBody):
        if not lock.acquire(blocking=False):
            raise HTTPException(409, "already generating")
        try:
            speaker = (body.speaker or script.next_speaker(dialogue)).lower()
            try:
                text = generate(dialogue, speaker, script)
            except gen.GenerationError as err:
                raise HTTPException(502, str(err)) from err
            dialogue.append(speaker, text)
            save()
        finally:
            lock.release()
        return state()

    @app.post("/api/interject")
    def post_interject(body: InterjectBody):
        if not body.text.strip():
            raise HTTPException(400, "empty interjection")
        try:
            dialogue.interject(body.text, at=body.at)
        except ValueError as err:
            raise HTTPException(400, str(err)) from err
        save()
        return state()

    @app.post("/api/revert")
    def post_revert():
        try:
            dialogue.revert()
        except ValueError as err:
            raise HTTPException(400, str(err)) from err
        save()
        return state()

    return app
