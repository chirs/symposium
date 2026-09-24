import json
import shutil
from pathlib import Path

import pytest

from symposium import cli
from symposium.dialogue import Dialogue
from symposium.script import DIALOGUES


@pytest.fixture
def run_file(tmp_path: Path) -> Path:
    shutil.copy(DIALOGUES / "republic-1" / "script.json", tmp_path / "script.json")
    return tmp_path / "run.md"


@pytest.fixture
def stub_generate(monkeypatch):
    def fake(dialogue, speaker, script, client=None, on_text=None):
        if on_text:
            on_text("So it seems.")
        return "So it seems."

    monkeypatch.setattr(cli, "generate", fake)


def test_new_copies_seed(run_file, capsys):
    cli.main(["new", "republic-1", str(run_file)])
    assert run_file.read_text() == (DIALOGUES / "republic-1" / "seed.md").read_text()
    with pytest.raises(SystemExit):
        cli.main(["new", "republic-1", str(run_file)])
    cli.main(["new", "republic-1", str(run_file), "--force"])


def test_next_follows_script_and_saves(run_file, stub_generate, capsys):
    cli.main(["new", "republic-1", str(run_file)])
    cli.main(["next", str(run_file), "-n", "2"])
    d = Dialogue.load(run_file)
    assert [e.speaker for e in d.exchanges[-2:]] == ["SOCRATES", "POLEMARCHUS"]
    assert d.exchanges[-1].text == "So it seems."
    assert "SOCRATES\nSo it seems." in capsys.readouterr().out


def test_next_speaker_override(run_file, stub_generate):
    cli.main(["new", "republic-1", str(run_file)])
    cli.main(["next", str(run_file), "--speaker", "thrasymachus"])
    assert Dialogue.load(run_file).exchanges[-1].speaker == "THRASYMACHUS"


def test_interject_then_next_then_revert(run_file, stub_generate, capsys):
    cli.main(["new", "republic-1", str(run_file)])
    cli.main(["interject", str(run_file), "But what is a debt?", "--at", "3"])
    assert "8 discarded" in capsys.readouterr().out
    d = Dialogue.load(run_file)
    assert len(d.exchanges) == 4 and d.exchanges[-1].is_stranger
    assert (run_file.parent / "run.original.md").exists()

    cli.main(["next", str(run_file)])
    assert Dialogue.load(run_file).exchanges[-1].speaker == "CEPHALUS"

    cli.main(["show", str(run_file)])
    assert "diverged" in capsys.readouterr().out

    cli.main(["revert", str(run_file)])
    assert len(Dialogue.load(run_file).exchanges) == 11
    assert not (run_file.parent / "run.original.md").exists()
    with pytest.raises(SystemExit):
        cli.main(["revert", str(run_file)])


def test_run_interactive(run_file, stub_generate, monkeypatch, capsys):
    cli.main(["new", "republic-1", str(run_file)])
    inputs = iter(["", "", "Is a deposit a debt?", "", "/revert", "/end", "/quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    cli.main(["run", str(run_file)])
    out = capsys.readouterr().out
    assert "THE STRANGER\nIs a deposit a debt?" in out
    assert "returned to the original path" in out
    assert Dialogue.load(run_file).format() == (DIALOGUES / "republic-1" / "seed.md").read_text()


def test_next_without_script_exits(tmp_path, stub_generate):
    f = tmp_path / "x.md"
    f.write_text("SOCRATES: Hm.\n")
    with pytest.raises(SystemExit):
        cli.main(["next", str(f)])
    cli.main(["next", str(f), "--dialogue", "republic-1"])
    assert Dialogue.load(f).exchanges[-1].speaker == "CEPHALUS"


def test_script_json_is_valid():
    json.loads((DIALOGUES / "republic-1" / "script.json").read_text())


def test_show_renders_directions(tmp_path, capsys):
    f = tmp_path / "x.md"
    f.write_text("[A pause.]\n\nSOCRATES: Hm.\n")
    cli.main(["show", str(f)])
    out = capsys.readouterr().out
    assert out.startswith("[A pause.]\n")
    assert "SOCRATES\nHm." in out
