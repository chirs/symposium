import pytest

from symposium import generate as g
from symposium.dialogue import Dialogue
from tests.conftest import FakeClient

SEED = "SOCRATES: What is justice?\n\nPOLEMARCHUS: Paying debts.\n"


def test_character_prompt_is_the_system_prompt_section():
    text = g.character_prompt("socrates")
    assert text.startswith("You are Socrates")
    assert "Character Profile" not in text


def test_system_prompt_has_preamble_then_character():
    text = g.system_prompt("thrasymachus")
    assert text.index("THE STRANGER") < text.index("You are Thrasymachus")


def test_missing_prompt_raises():
    with pytest.raises(g.GenerationError):
        g.character_prompt("glaucon")


def test_user_content_blocks_and_cache_breakpoint():
    blocks = g.user_content(Dialogue.parse(SEED), "socrates")
    assert [b["text"] for b in blocks[1:3]] == ["SOCRATES: What is justice?", "POLEMARCHUS: Paying debts."]
    assert blocks[2]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in blocks[3]
    assert blocks[3]["text"].startswith("Speak next as SOCRATES.")


def test_generate_streams_and_cleans_label(fake_client):
    fake_client.text = "Socrates: Is it just, then?"
    seen = []
    text = g.generate(Dialogue.parse(SEED), "socrates", client=fake_client, on_text=seen.append)
    assert text == "Is it just, then?"
    assert "".join(seen) == fake_client.text
    call = fake_client.calls[0]
    assert call["model"] == g.DEFAULT_MODEL
    assert call["messages"][0]["role"] == "user"
    assert "You are Socrates" in call["system"]


def test_generate_rejects_early_stop():
    client = FakeClient(stop_reason="max_tokens")
    with pytest.raises(g.GenerationError, match="max_tokens"):
        g.generate(Dialogue.parse(SEED), "socrates", client=client)


def test_model_and_effort_from_env(monkeypatch):
    monkeypatch.setenv("SYMPOSIUM_MODEL", "claude-sonnet-5")
    monkeypatch.setenv("SYMPOSIUM_EFFORT", "low")
    params = g.request_params(Dialogue.parse(SEED), "socrates")
    assert params["model"] == "claude-sonnet-5"
    assert params["output_config"] == {"effort": "low"}


def test_missing_credentials_is_a_generation_error():
    class NoAuth:
        class messages:
            @staticmethod
            def stream(**kwargs):
                raise TypeError("Could not resolve authentication method.")

    with pytest.raises(g.GenerationError, match="ANTHROPIC_API_KEY"):
        g.generate(Dialogue.parse(SEED), "socrates", client=NoAuth())
