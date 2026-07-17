import types
import claude_api as capi


def test_demo_stream_when_no_client(monkeypatch):
    monkeypatch.setattr(capi, "client", None)
    out = "".join(capi.analyze_idea_stream(
        "любая идея длиннее пятидесяти символов для проверки демо-режима сейчас"
    ))
    assert isinstance(out, str) and len(out) > 0


def test_live_call_params_streaming(monkeypatch):
    captured = {}

    class FakeStream:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        @property
        def text_stream(self):
            return iter(["LIVE", "-OK"])

    class FakeMessages:
        def stream(self, **kwargs):
            captured.update(kwargs)
            return FakeStream()

    fake_client = types.SimpleNamespace(messages=FakeMessages())
    monkeypatch.setattr(capi, "client", fake_client)

    out = "".join(capi.analyze_idea_stream(
        "Сервис доставки здоровой еды по подписке для офисов в крупных городах России"
    ))
    assert out == "LIVE-OK"
    assert captured["model"] == "claude-sonnet-5"
    assert captured["max_tokens"] == 6000
    assert captured["thinking"] == {"type": "disabled"}
    assert captured["output_config"] == {"effort": "medium"}
    # промпт должен содержать текст идеи
    assert "доставки здоровой еды" in captured["messages"][0]["content"]
