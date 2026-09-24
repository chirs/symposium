from types import SimpleNamespace

import pytest


class FakeStream:
    def __init__(self, text, stop_reason):
        self.chunks = [text[i : i + 5] for i in range(0, len(text), 5)]
        self.stop_reason = stop_reason

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def text_stream(self):
        yield from self.chunks

    def get_final_message(self):
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="text", text="".join(self.chunks))],
        )


class FakeClient:
    """Stands in for anthropic.Anthropic; records the request and replays canned text."""

    def __init__(self, text="I do not know.", stop_reason="end_turn"):
        self.calls = []
        self.text = text
        self.stop_reason = stop_reason
        self.messages = SimpleNamespace(stream=self._stream)

    def _stream(self, **kwargs):
        self.calls.append(kwargs)
        return FakeStream(self.text, self.stop_reason)


@pytest.fixture
def fake_client():
    return FakeClient()


class FakeDirector:
    """Stands in for anthropic.Anthropic for the director's single non-streaming call."""

    def __init__(self, text="CALLICLES", error=None):
        self.calls = []
        self.text = text
        self.error = error
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.text)])
