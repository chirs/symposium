import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from symposium.dialogue import Dialogue
from symposium.generate import GenerationError
from symposium.script import DIALOGUES
from symposium.server import build_app


def fake_generate(dialogue, speaker, script):
    return f"({speaker} speaks)"


@pytest.fixture
def client():
    return TestClient(build_app(generate=fake_generate))


def test_index_and_state(client):
    assert "<title>Symposium</title>" in client.get("/").text
    data = client.get("/api/dialogue").json()
    assert data["title"] == "Republic, Book I"
    assert data["setting"] == "The house of Cephalus, in the Piraeus"
    assert data["characters"] == ["SOCRATES", "CEPHALUS", "POLEMARCHUS", "THRASYMACHUS"]
    assert len(data["exchanges"]) == 11
    assert data["next_speaker"] == "SOCRATES"
    assert data["has_original"] is False


def test_next_follows_script_and_accepts_override(client):
    data = client.post("/api/next", json={}).json()
    assert data["exchanges"][-1] == {"speaker": "SOCRATES", "text": "(socrates speaks)"}
    data = client.post("/api/next", json={"speaker": "thrasymachus"}).json()
    assert data["exchanges"][-1]["speaker"] == "THRASYMACHUS"
    assert data["next_speaker"] == "SOCRATES"


def test_interject_and_revert(client):
    data = client.post("/api/interject", json={"text": "What is a debt?", "at": 3}).json()
    assert len(data["exchanges"]) == 4
    assert data["exchanges"][-1]["speaker"] == "THE STRANGER"
    assert data["has_original"] is True
    assert data["next_speaker"] == "CEPHALUS"
    data = client.post("/api/revert").json()
    assert len(data["exchanges"]) == 11 and data["has_original"] is False
    assert client.post("/api/revert").status_code == 400
    assert client.post("/api/interject", json={"text": "  "}).status_code == 400
    assert client.post("/api/interject", json={"text": "x", "at": 99}).status_code == 400


def test_generation_error_is_502():
    def broken(dialogue, speaker, script):
        raise GenerationError("refusal")

    client = TestClient(build_app(generate=broken))
    res = client.post("/api/next", json={})
    assert res.status_code == 502 and "refusal" in res.json()["detail"]


def test_file_backed_app_persists(tmp_path: Path):
    shutil.copy(DIALOGUES / "republic-1" / "script.json", tmp_path / "script.json")
    run = tmp_path / "run.md"
    shutil.copy(DIALOGUES / "republic-1" / "seed.md", run)
    client = TestClient(build_app(path=run, generate=fake_generate))
    client.post("/api/interject", json={"text": "Hm."})
    client.post("/api/next", json={})
    d = Dialogue.load(run)
    assert d.has_original and d.exchanges[-1].speaker == "SOCRATES"
    client.post("/api/revert")
    assert not Dialogue.load(run).has_original
