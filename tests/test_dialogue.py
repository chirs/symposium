from pathlib import Path

import pytest

from symposium.dialogue import STAGE, STRANGER, Dialogue, Exchange, format, original_path, parse

SCRIPT = """SOCRATES: Is it so?

CEPHALUS: It is, Socrates.
And I will tell you why.

Men of my age flock together.

THE STRANGER: I doubt it.
"""


def test_parse_round_trip():
    exchanges = parse(SCRIPT)
    assert [e.speaker for e in exchanges] == ["SOCRATES", "CEPHALUS", STRANGER]
    assert exchanges[1].text == "It is, Socrates.\nAnd I will tell you why.\n\nMen of my age flock together."
    assert exchanges[2].is_stranger
    assert exchanges[1].key == "cephalus"
    assert format(exchanges) == SCRIPT


def test_parse_rejects_text_before_label():
    with pytest.raises(ValueError):
        parse("Once upon a time.\n\nSOCRATES: Hm.")


def test_parse_ignores_leading_blank_lines():
    assert parse("\n\nSOCRATES: Hm.\n") == [Exchange("SOCRATES", "Hm.")]


def test_interject_at_end_snapshots_original():
    d = Dialogue.parse(SCRIPT[: SCRIPT.index("THE STRANGER")])
    d.interject("But surely not.")
    assert [e.speaker for e in d.exchanges] == ["SOCRATES", "CEPHALUS", STRANGER]
    assert d.has_original
    assert [e.speaker for e in d.original] == ["SOCRATES", "CEPHALUS"]


def test_interject_at_position_discards_rest():
    d = Dialogue.parse(SCRIPT)
    d.interject("Wait.", at=1)
    assert [e.speaker for e in d.exchanges] == ["SOCRATES", STRANGER]
    assert d.exchanges[1].text == "Wait."
    assert len(d.original) == 3


def test_second_interjection_keeps_first_snapshot():
    d = Dialogue.parse(SCRIPT)
    d.interject("One.", at=2)
    d.append("socrates", "Reply.")
    d.interject("Two.", at=1)
    assert [e.speaker for e in d.exchanges] == ["SOCRATES", STRANGER]
    assert len(d.original) == 3
    d.revert()
    assert d.format() == SCRIPT
    assert not d.has_original


def test_revert_without_original_raises():
    with pytest.raises(ValueError):
        Dialogue.parse(SCRIPT).revert()


def test_interject_out_of_range():
    with pytest.raises(ValueError):
        Dialogue.parse(SCRIPT).interject("x", at=4)


def test_turn_count_and_last_speaker_skip_stranger():
    d = Dialogue.parse(SCRIPT)
    assert d.turn_count == 2
    assert d.last_speaker == "cephalus"
    assert Dialogue().last_speaker is None


def test_save_and_load_with_sidecar(tmp_path: Path):
    path = tmp_path / "run.md"
    d = Dialogue.parse(SCRIPT)
    d.interject("Hm.", at=1)
    d.save(path)
    assert original_path(path) == tmp_path / "run.original.md"
    assert original_path(path).exists()

    loaded = Dialogue.load(path)
    assert loaded.exchanges == d.exchanges
    assert loaded.original == d.original

    loaded.revert()
    loaded.save(path)
    assert not original_path(path).exists()
    assert Dialogue.load(path).format() == SCRIPT


STAGED = """[Thrasymachus, who has several times tried to interrupt, bursts in.]

THRASYMACHUS: What folly, Socrates, has taken possession of you all?

[He glares round the room.]

SOCRATES: I was panic-stricken.
"""


def test_stage_directions_round_trip():
    exchanges = parse(STAGED)
    assert [e.speaker for e in exchanges] == [STAGE, "THRASYMACHUS", STAGE, "SOCRATES"]
    assert exchanges[0].is_stage and not exchanges[0].is_scripted
    assert exchanges[0].text.startswith("Thrasymachus, who")
    assert exchanges[2].as_text() == "[He glares round the room.]"
    assert format(exchanges) == STAGED


def test_stage_directions_do_not_count_as_turns():
    d = Dialogue.parse(STAGED + "\n[Silence.]\n")
    assert d.turn_count == 2
    assert d.last_speaker == "socrates"


def test_text_after_direction_without_label_is_rejected():
    with pytest.raises(ValueError):
        parse("[A pause.]\nHe coughs.\n")
