import pytest

from symposium.dialogue import Dialogue
from symposium.script import DIALOGUES, ROOT, Phase, Script

SCRIPT = Script(
    "Test",
    [
        Phase("one", ["a", "b"], 3),
        Phase("two", ["c", "a"], 2),
    ],
)


def test_phase_at_uses_cumulative_lengths_and_repeats_last():
    assert [SCRIPT.phase_at(i).name for i in range(7)] == ["one"] * 3 + ["two"] * 4


def test_next_speaker_alternates_within_phase():
    d = Dialogue()
    assert SCRIPT.next_speaker(d) == "a"
    d.append("a", "x")
    assert SCRIPT.next_speaker(d) == "b"
    d.append("b", "x")
    assert SCRIPT.next_speaker(d) == "a"


def test_stranger_does_not_consume_a_turn():
    d = Dialogue()
    d.append("a", "x")
    d.interject("hm")
    assert SCRIPT.next_speaker(d) == "b"
    assert d.turn_count == 1


def test_phase_transition_starts_new_cycle():
    d = Dialogue()
    for s in ["a", "b", "a"]:
        d.append(s, "x")
    assert SCRIPT.next_speaker(d) == "c"
    d.append("c", "x")
    assert SCRIPT.next_speaker(d) == "a"
    d.append("a", "x")
    assert SCRIPT.next_speaker(d) == "c"


def test_characters_in_order_of_appearance():
    assert SCRIPT.characters == ["a", "b", "c"]


def test_republic_seed_matches_script():
    script = Script.named("republic-1")
    assert script.name == "republic-1"
    assert script.dir == DIALOGUES / "republic-1"
    seed = Dialogue.parse((script.dir / "seed.md").read_text())
    scripted = [e for e in seed.exchanges if e.is_scripted]
    assert len(scripted) > 400
    starts = [0]
    for p in script.phases[:-1]:
        starts.append(starts[-1] + p.length)
    assert [scripted[i].speaker for i in starts] == ["SERVANT", "CEPHALUS", "SOCRATES", "THRASYMACHUS"]
    assert scripted[starts[3]].text.startswith("What folly")
    assert script.next_speaker(seed) == "thrasymachus"


@pytest.mark.parametrize("script", Script.discover(), ids=lambda s: s.name)
def test_every_dialogue_is_complete(script: Script):
    assert script.title and script.setting and script.scene
    seed = Dialogue.parse((script.dir / "seed.md").read_text())
    assert seed.exchanges
    assert script.next_speaker(seed) in script.characters
    assert script.collection in ("Plato", "New Testament")
    for c in script.characters:
        path = script.prompt_path(c)
        assert path.exists(), c
        assert "# System Prompt" in path.read_text(), c
        assert (ROOT / "prompts" / "orchestration.md").exists()


def test_prompt_path_defaults_to_the_dialogue_directory():
    s = Script.named("gorgias")
    assert s.prompt_path("polus") == s.dir / "prompts" / "polus.md"
    assert not s.sandbox and s.cast == {}


def test_prompt_path_falls_back_to_the_shared_pool(tmp_path, monkeypatch):
    from symposium import script as script_module

    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "alpha.md").write_text("# System Prompt\n\nYou are Alpha.\n")
    monkeypatch.setattr(script_module, "SHARED", shared)
    d = tmp_path / "dialogues" / "x"
    (d / "prompts").mkdir(parents=True)
    (d / "prompts" / "beta.md").write_text("# System Prompt\n\nYou are Beta.\n")
    s = Script("X", [Phase("all", ["alpha", "beta"], 1)], dir=d)
    assert s.prompt_path("beta") == d / "prompts" / "beta.md"
    assert s.prompt_path("alpha") == shared / "alpha.md"
    s.cast = {"alpha": "shared", "beta": "y"}
    assert s.prompt_path("alpha") == shared / "alpha.md"
    assert s.prompt_path("beta") == tmp_path / "dialogues" / "y" / "prompts" / "beta.md"


def test_discover_orders_plato_before_the_new_testament():
    names = [s.name for s in Script.discover()]
    assert names[:5] == ["crito", "euthyphro", "gorgias", "republic-1", "symposium"]
    assert names[5] == "acts-17-athens"


def test_speakers_and_directed_with_guests():
    s = Script.named("gorgias")
    assert s.speakers == s.characters and not s.directed
    s.guests = {"jesus": "shared", "polus": "gorgias"}
    assert s.speakers == ["socrates", "gorgias", "polus", "callicles", "jesus"] and s.directed
    d = Dialogue.parse("JESUS: Hm.\n")
    assert s.next_speaker(d) == "socrates"
