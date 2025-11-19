from __future__ import annotations

import pytest

from llumdocs.llm import LLMConfigurationError
from llumdocs.services.translation_service import TranslationError, translate_text


def test_translate_text_calls_llm(monkeypatch):
    captured = {}

    def fake_chat_completion(messages, model_hint=None):
        captured["messages"] = messages
        captured["model_hint"] = model_hint
        return "Hola mon"

    monkeypatch.setattr(
        "llumdocs.services.translation_service.chat_completion",
        fake_chat_completion,
    )

    result = translate_text(
        "Hello world!", source_lang="en", target_lang="ca", model_hint="test-model"
    )

    assert result == "Hola mon"
    assert captured["model_hint"] == "test-model"
    assert captured["messages"][0]["role"] == "system"
    assert "Translate the user's text" in captured["messages"][0]["content"]
    assert "Hello world!" in captured["messages"][1]["content"]


def test_translate_text_includes_auto_detect(monkeypatch):
    captured = {}

    def fake_chat_completion(messages, model_hint=None):
        captured["messages"] = messages
        return "Hola món"

    monkeypatch.setattr(
        "llumdocs.services.translation_service.chat_completion",
        fake_chat_completion,
    )

    translate_text("Hello world!", source_lang="auto", target_lang="es")

    assert "auto-detect" in captured["messages"][1]["content"]
    assert "Spanish" in captured["messages"][1]["content"]


def test_translate_text_rejects_empty_text():
    with pytest.raises(TranslationError):
        translate_text("   ", source_lang="en", target_lang="es")


def test_translate_text_wraps_llm_errors(monkeypatch):
    def fake_chat_completion(*_, **__):
        raise LLMConfigurationError("no provider")

    monkeypatch.setattr(
        "llumdocs.services.translation_service.chat_completion",
        fake_chat_completion,
    )

    with pytest.raises(TranslationError) as exc:
        translate_text("Hello", source_lang="en", target_lang="es")

    assert "no provider" in str(exc.value)


@pytest.mark.parametrize(
    ("source_lang", "target_lang"),
    [
        ("xx", "en"),
        ("en", "xx"),
        ("en", "en"),
    ],
)
def test_translate_text_validation(source_lang, target_lang):
    with pytest.raises(TranslationError):
        translate_text("test", source_lang=source_lang, target_lang=target_lang)
