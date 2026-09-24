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
    seed = Dialogue.parse((DIALOGUES / "republic-1" / "seed.md").read_text())
    assert script.phase_at(script.phases[0].length - 1).name == "Cephalus"
    assert script.phase_at(seed.turn_count).name == "Polemarchus"
    assert seed.exchanges[script.phases[0].length - 1].key == "cephalus"
    assert script.next_speaker(seed) == "socrates"
    for c in script.characters:
        assert (ROOT / "prompts" / f"{c}.md").exists(), c
