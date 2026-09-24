import shutil
from pathlib import Path

import pytest

from symposium import sandbox
from symposium.dialogue import Dialogue
from symposium.script import DIALOGUES, Script


@pytest.fixture
def root(tmp_path: Path) -> Path:
    for name in ("republic-1", "gorgias"):
        shutil.copytree(DIALOGUES / name, tmp_path / name, ignore=shutil.ignore_patterns("run*.md"))
    return tmp_path


def test_catalog_lists_every_prompt_with_its_dialogue():
    rows = sandbox.catalog()
    assert {r["dialogue"] for r in rows if r["speaker"] == "socrates"} == {
        "republic-1", "euthyphro", "crito", "gorgias", "symposium"
    }
    assert {"speaker": "callicles", "dialogue": "gorgias", "title": "Gorgias"} in rows


def test_create_writes_script_and_seed(root):
    s = sandbox.create(
        "Power & Justice",
        [("socrates", "gorgias"), ("callicles", "gorgias"), ("thrasymachus", "republic-1")],
        "A wine shop in the Piraeus",
        "Late at night. They have been drinking.",
        "Is the strong man happier than the just one?",
        root=root,
    )
    assert s.name == "sandbox-power-justice" and s.sandbox
    assert s.characters == ["socrates", "callicles", "thrasymachus"]
    assert s.prompt_path("thrasymachus") == root / "republic-1" / "prompts" / "thrasymachus.md"
    assert s.prompt_path("socrates") == root / "gorgias" / "prompts" / "socrates.md"
    seed = Dialogue.parse((s.dir / "seed.md").read_text())
    assert seed.exchanges[0].is_stage
    assert seed.exchanges[0].text == "A wine shop in the Piraeus. Present: Socrates, Callicles, Thrasymachus."
    assert seed.exchanges[1].is_stranger
    assert s.next_speaker(seed) == "socrates"
    assert sandbox.catalog(root) and all(not r["dialogue"].startswith("sandbox") for r in sandbox.catalog(root))
    assert [x.name for x in Script.discover(root)] == ["gorgias", "republic-1", "sandbox-power-justice"]


def test_create_without_opening_has_only_the_direction(root):
    s = sandbox.create("Quiet", [("cephalus", "republic-1")], "The porch.", "y", root=root)
    assert (s.dir / "seed.md").read_text() == "[The porch. Present: Cephalus.]\n"


def test_create_validates(root):
    with pytest.raises(ValueError, match="title"):
        sandbox.create("!!!", [("socrates", "gorgias")], "s", "c", root=root)
    with pytest.raises(ValueError, match="at least one"):
        sandbox.create("T", [], "s", "c", root=root)
    with pytest.raises(ValueError, match="no prompt"):
        sandbox.create("T", [("glaucon", "republic-1")], "s", "c", root=root)
    with pytest.raises(ValueError, match="twice"):
        sandbox.create("T", [("socrates", "gorgias"), ("socrates", "republic-1")], "s", "c", root=root)
    sandbox.create("T", [("socrates", "gorgias")], "s", "c", root=root)
    with pytest.raises(ValueError, match="already exists"):
        sandbox.create("t", [("socrates", "gorgias")], "s", "c", root=root)


def test_remove_only_sandboxes(root):
    s = sandbox.create("Gone", [("socrates", "gorgias")], "s", "c", root=root)
    sandbox.remove(s)
    assert not s.dir.exists()
    with pytest.raises(ValueError):
        sandbox.remove(Script.named("gorgias", root))
