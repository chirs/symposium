"""JSON API over the dialogues on disk, plus the reading page."""

from __future__ import annotations

import shutil
import threading
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from symposium import director, sandbox
from symposium import generate as gen
from symposium.dialogue import Dialogue
from symposium.script import DIALOGUES, ROOT, Script

WEB = ROOT / "web"


class NextBody(BaseModel):
    speaker: str | None = None


class InterjectBody(BaseModel):
    text: str
    at: int | None = None


class CastMember(BaseModel):
    speaker: str
    dialogue: str


class SandboxBody(BaseModel):
    title: str
    cast: list[CastMember]
    setting: str = ""
    scene: str = ""
    opening: str = ""


class Room:
    """One dialogue's script, working file (run.md, created from the seed), and lock."""

    def __init__(self, script: Script):
        self.script = script
        self.path = script.dir / "run.md"
        self.lock = threading.Lock()
        if not self.path.exists():
            shutil.copy(script.dir / "seed.md", self.path)
        self.dialogue = Dialogue.load(self.path)

    def save(self) -> None:
        self.dialogue.save(self.path)

    def reset(self) -> None:
        self.dialogue = Dialogue.parse((self.script.dir / "seed.md").read_text())
        self.save()

    def state(self) -> dict:
        d = self.dialogue
        return {
            **summary(self.script),
            "exchanges": [{"speaker": e.speaker, "text": e.text} for e in d.exchanges],
            "has_original": d.has_original,
            "next_speaker": "" if self.script.sandbox else self.script.next_speaker(d).upper(),
        }


def summary(script: Script) -> dict:
    return {
        "name": script.name,
        "title": script.title,
        "setting": script.setting,
        "characters": [c.upper() for c in script.characters],
        "sandbox": script.sandbox,
        "collection": script.collection,
    }


def build_app(
    dialogues_dir: Path = DIALOGUES,
    generate: Callable[[Dialogue, str, Script], str] = gen.generate,
    choose: Callable[[Dialogue, Script], str] = director.choose_speaker,
) -> FastAPI:
    scripts = {s.name: s for s in Script.discover(dialogues_dir)}
    rooms: dict[str, Room] = {}
    app = FastAPI(title="Symposium")

    def room(name: str) -> Room:
        if name not in scripts:
            raise HTTPException(404, f"no dialogue named {name!r}")
        if name not in rooms:
            rooms[name] = Room(scripts[name])
        return rooms[name]

    @app.get("/")
    def index():
        return FileResponse(WEB / "index.html")

    @app.get("/api/dialogues")
    def list_dialogues():
        return [summary(s) for s in scripts.values()]

    @app.get("/api/characters")
    def list_characters():
        return sandbox.catalog(dialogues_dir)

    @app.post("/api/sandboxes")
    def post_sandbox(body: SandboxBody):
        try:
            script = sandbox.create(
                body.title, [(c.speaker, c.dialogue) for c in body.cast],
                body.setting, body.scene, body.opening, root=dialogues_dir,
            )
        except ValueError as err:
            raise HTTPException(400, str(err)) from err
        scripts[script.name] = script
        return summary(script)

    @app.get("/api/dialogues/{name}")
    def get_dialogue(name: str):
        return room(name).state()

    @app.delete("/api/dialogues/{name}")
    def delete_dialogue(name: str):
        if name not in scripts:
            raise HTTPException(404, f"no dialogue named {name!r}")
        try:
            sandbox.remove(scripts[name])
        except ValueError as err:
            raise HTTPException(400, str(err)) from err
        del scripts[name]
        rooms.pop(name, None)
        return {"removed": name}

    @app.post("/api/dialogues/{name}/next")
    def post_next(name: str, body: NextBody):
        r = room(name)
        if not r.lock.acquire(blocking=False):
            raise HTTPException(409, "already generating")
        try:
            speaker = (body.speaker or choose(r.dialogue, r.script)).lower()
            try:
                text = generate(r.dialogue, speaker, r.script)
            except gen.GenerationError as err:
                raise HTTPException(502, str(err)) from err
            r.dialogue.append(speaker, text)
            r.save()
        finally:
            r.lock.release()
        return r.state()

    @app.post("/api/dialogues/{name}/interject")
    def post_interject(name: str, body: InterjectBody):
        r = room(name)
        if not body.text.strip():
            raise HTTPException(400, "empty interjection")
        try:
            r.dialogue.interject(body.text, at=body.at)
        except ValueError as err:
            raise HTTPException(400, str(err)) from err
        r.save()
        return r.state()

    @app.post("/api/dialogues/{name}/revert")
    def post_revert(name: str):
        r = room(name)
        try:
            r.dialogue.revert()
        except ValueError as err:
            raise HTTPException(400, str(err)) from err
        r.save()
        return r.state()

    @app.post("/api/dialogues/{name}/reset")
    def post_reset(name: str):
        r = room(name)
        r.reset()
        return r.state()

    return app
