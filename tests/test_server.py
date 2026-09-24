import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from symposium.dialogue import Dialogue
from symposium.generate import GenerationError
from symposium.script import DIALOGUES
from symposium.server import build_app

TINY_SCRIPT = """{"title": "Tiny", "setting": "A porch", "scene": "Two men talk.",
 "phases": [{"name": "all", "speakers": ["alpha", "beta"], "length": 1}]}
"""


REPUBLIC_LEN = len(Dialogue.parse((DIALOGUES / "republic-1" / "seed.md").read_text()).exchanges)


def fake_generate(dialogue, speaker, script):
    return f"({speaker} speaks in {script.name})"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    shutil.copytree(DIALOGUES / "republic-1", tmp_path / "republic-1", ignore=shutil.ignore_patterns("run*.md"))
    tiny = tmp_path / "tiny"
    (tiny / "prompts").mkdir(parents=True)
    (tiny / "script.json").write_text(TINY_SCRIPT)
    (tiny / "seed.md").write_text("ALPHA: Hello.\n")
    for c in ["alpha", "beta"]:
        (tiny / "prompts" / f"{c}.md").write_text(f"# {c}\n\n---\n\n# System Prompt\n\nYou are {c}.\n")
    return tmp_path


@pytest.fixture
def client(root):
    return TestClient(build_app(dialogues_dir=root, generate=fake_generate))


def test_index_and_list(client):
    assert "<title>Symposium</title>" in client.get("/").text
    names = [d["name"] for d in client.get("/api/dialogues").json()]
    assert names == ["republic-1", "tiny"]


def test_state_creates_run_file(client, root):
    assert not (root / "tiny" / "run.md").exists()
    data = client.get("/api/dialogues/tiny").json()
    assert (root / "tiny" / "run.md").exists()
    assert data["title"] == "Tiny" and data["setting"] == "A porch"
    assert data["characters"] == ["ALPHA", "BETA"]
    assert data["next_speaker"] == "BETA"
    assert client.get("/api/dialogues/nope").status_code == 404


def test_next_follows_script_and_accepts_override(client):
    data = client.post("/api/dialogues/republic-1/next", json={}).json()
    assert data["exchanges"][-1] == {"speaker": "THRASYMACHUS", "text": "(thrasymachus speaks in republic-1)"}
    data = client.post("/api/dialogues/republic-1/next", json={"speaker": "thrasymachus"}).json()
    assert data["exchanges"][-1]["speaker"] == "THRASYMACHUS"
    assert data["next_speaker"] == "SOCRATES"


def test_dialogues_are_independent(client, root):
    client.post("/api/dialogues/tiny/next", json={})
    assert len(client.get("/api/dialogues/tiny").json()["exchanges"]) == 2
    assert len(client.get("/api/dialogues/republic-1").json()["exchanges"]) == REPUBLIC_LEN
    assert Dialogue.load(root / "tiny" / "run.md").exchanges[-1].speaker == "BETA"


def test_interject_revert_and_reset(client, root):
    base = "/api/dialogues/republic-1"
    data = client.post(f"{base}/interject", json={"text": "What is a debt?", "at": 3}).json()
    assert len(data["exchanges"]) == 4 and data["exchanges"][-1]["speaker"] == "THE STRANGER"
    assert data["has_original"] is True and data["next_speaker"] == "POLEMARCHUS"
    assert (root / "republic-1" / "run.original.md").exists()
    data = client.post(f"{base}/revert").json()
    assert len(data["exchanges"]) == REPUBLIC_LEN and data["has_original"] is False
    assert client.post(f"{base}/revert").status_code == 400
    assert client.post(f"{base}/interject", json={"text": "  "}).status_code == 400
    assert client.post(f"{base}/interject", json={"text": "x", "at": 99999}).status_code == 400

    client.post(f"{base}/interject", json={"text": "Again.", "at": 2})
    client.post(f"{base}/next", json={})
    data = client.post(f"{base}/reset").json()
    assert len(data["exchanges"]) == REPUBLIC_LEN and data["has_original"] is False
    assert not (root / "republic-1" / "run.original.md").exists()
    assert (root / "republic-1" / "run.md").read_text() == (DIALOGUES / "republic-1" / "seed.md").read_text()


def test_generation_error_is_502(root):
    def broken(dialogue, speaker, script):
        raise GenerationError("refusal")

    client = TestClient(build_app(dialogues_dir=root, generate=broken))
    res = client.post("/api/dialogues/tiny/next", json={})
    assert res.status_code == 502 and "refusal" in res.json()["detail"]
