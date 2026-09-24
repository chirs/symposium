import pytest

from symposium import director, sandbox
from symposium.dialogue import Dialogue
from symposium.script import Script
from tests.conftest import FakeDirector
from tests.test_sandbox import root  # noqa: F401


@pytest.fixture
def box(root):  # noqa: F811
    return sandbox.create(
        "Box", [("socrates", "gorgias"), ("callicles", "gorgias"), ("polus", "gorgias")],
        "A porch", "They argue.", "Who is happier, the tyrant or the just man?", root=root,
    )


def test_scripted_dialogues_never_call_the_director():
    client = FakeDirector()
    d = Dialogue.parse("SOCRATES: Hm.\n")
    assert director.choose_speaker(d, Script.named("republic-1"), client=client) == "polemarchus"
    assert client.calls == []


def test_parse_choice_takes_the_earliest_name():
    cast = ["socrates", "callicles", "polus"]
    assert director.parse_choice("Callicles.", cast) == "callicles"
    assert director.parse_choice("Surely Polus, since Callicles was addressed... no, Polus.", cast) == "polus"
    assert director.parse_choice("Nobody.", cast) is None


def test_director_call_and_reply(box):
    d = Dialogue.parse((box.dir / "seed.md").read_text())
    client = FakeDirector("CALLICLES")
    assert director.choose_speaker(d, box, client=client) == "callicles"
    call = client.calls[0]
    assert call["model"] == director.DEFAULT_DIRECTOR_MODEL
    assert "Never choose THE STRANGER" in call["system"]
    content = call["messages"][0]["content"]
    assert content.startswith("THE STRANGER: Who is happier")
    assert content.endswith("Answer with one name from: SOCRATES, CALLICLES, POLUS.")


def test_director_only_sees_the_tail(box):
    d = Dialogue.parse((box.dir / "seed.md").read_text())
    for i in range(12):
        d.append("socrates" if i % 2 else "polus", f"line {i}")
    client = FakeDirector("polus")
    director.choose_speaker(d, box, client=client)
    content = client.calls[0]["messages"][0]["content"]
    assert "THE STRANGER" not in content and "line 4" in content and "line 3" not in content


def test_fallbacks(box):
    d = Dialogue.parse((box.dir / "seed.md").read_text())
    d.append("callicles", "The tyrant, obviously.")
    assert director.choose_speaker(d, box, client=FakeDirector("I cannot say.")) == "polus"
    assert director.choose_speaker(d, box, client=FakeDirector(error=TypeError("auth"))) == "polus"


def test_empty_transcript_picks_the_first_without_a_call(root):  # noqa: F811
    s = sandbox.create("Silent", [("polus", "gorgias"), ("socrates", "gorgias")], "s", "c", root=root)
    d = Dialogue.parse((s.dir / "seed.md").read_text())
    client = FakeDirector()
    assert director.choose_speaker(d, s, client=client) == "polus"
    assert client.calls == []
