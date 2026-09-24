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
    for c in script.characters:
        path = script.dir / "prompts" / f"{c}.md"
        assert path.exists(), c
        assert "# System Prompt" in path.read_text(), c
        assert (ROOT / "prompts" / "orchestration.md").exists()


def test_prompt_path_defaults_to_the_dialogue_directory():
    s = Script.named("gorgias")
    assert s.prompt_path("polus") == s.dir / "prompts" / "polus.md"
    assert not s.sandbox and s.cast == {}
