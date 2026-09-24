import shutil
from pathlib import Path

import pytest

from symposium import director, guests
from symposium import generate as g
from symposium.dialogue import Dialogue
from symposium.script import DIALOGUES, Script
from tests.conftest import FakeDirector


@pytest.fixture
def root(tmp_path: Path) -> Path:
    for name in ("republic-1", "gorgias"):
        shutil.copytree(DIALOGUES / name, tmp_path / name, ignore=shutil.ignore_patterns("run*"))
    return tmp_path


@pytest.fixture
def run(root):
    script = Script.named("republic-1", root)
    run = script.dir / "run.md"
    shutil.copy(script.dir / "seed.md", run)
    return Dialogue.load(run), script, run


def test_invite_diverges_and_records(run):
    d, script, path = run
    before = len(d.exchanges)
    e = guests.invite(d, script, path, "jesus", "shared", at=5)
    assert e.is_stage and e.text == "Jesus has come in and joined the company."
    assert len(d.exchanges) == 6 and d.exchanges[-1] is e
    assert d.has_original and len(d.original) == before
    assert script.guests == {"jesus": "shared"}
    assert guests.load(path) == {"jesus": "shared"}
    assert script.speakers == ["socrates", "polemarchus", "cephalus", "thrasymachus", "jesus"]
    assert script.directed
    assert script.prompt_path("jesus").name == "jesus.md" and script.prompt_path("jesus").exists()

    guests.invite(d, script, path, "callicles", "gorgias")
    assert script.prompt_path("callicles") == script.dir.parent / "gorgias" / "prompts" / "callicles.md"
    fresh = Script.named("republic-1", script.dir.parent)
    guests.attach(fresh, path)
    assert fresh.guests == {"jesus": "shared", "callicles": "gorgias"}
    guests.clear(fresh, path)
    assert not guests.path_for(path).exists() and fresh.guests == {}


def test_invite_rejects_present_and_unknown(run):
    d, script, path = run
    with pytest.raises(ValueError, match="already present"):
        guests.invite(d, script, path, "thrasymachus", "republic-1")
    with pytest.raises(ValueError, match="no prompt"):
        guests.invite(d, script, path, "glaucon", "republic-1")
    guests.invite(d, script, path, "jesus", "shared")
    with pytest.raises(ValueError, match="already present"):
        guests.invite(d, script, path, "jesus", "shared")


def test_guest_gets_the_guest_note_and_the_scene(run):
    d, script, path = run
    guests.invite(d, script, path, "jesus", "shared")
    text = g.system_prompt(script, "jesus")
    assert "You are Jesus" in text
    assert text.index("You were not in this scene") < text.index("house of Cephalus")
    assert "You were not in this scene" not in g.system_prompt(script, "socrates")


def test_director_takes_over_with_a_guest(run):
    d, script, path = run
    client = FakeDirector("JESUS")
    assert director.choose_speaker(d, script, client=client) == "thrasymachus" and client.calls == []
    guests.invite(d, script, path, "jesus", "shared")
    assert director.choose_speaker(d, script, client=client) == "jesus"
    assert client.calls[0]["messages"][0]["content"].endswith(
        "Answer with one name from: SOCRATES, POLEMARCHUS, CEPHALUS, THRASYMACHUS, JESUS."
    )
    d.append("jesus", "Why do you ask?")
    assert director.choose_speaker(d, script, client=FakeDirector("nobody")) == "socrates"
