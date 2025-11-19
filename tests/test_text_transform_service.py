from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from llumdocs.llm import LLMConfigurationError
from llumdocs.services.text_transform_service import (
    TextTransformError,
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
)


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_parses_json(mock_chat_completion):
    captured = {}

    def fake_chat_completion(messages, model_hint=None):
        captured["messages"] = messages
        captured["model_hint"] = model_hint
        return json.dumps(["alpha", "beta", "gamma"])

    mock_chat_completion.side_effect = fake_chat_completion

    keywords = extract_keywords("Example text", max_keywords=5, model_hint="test-model")

    assert keywords == ["alpha", "beta", "gamma"]
    assert captured["model_hint"] == "test-model"
    assert "Maximum keywords: 5" in captured["messages"][1]["content"]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_parses_bullet_list(mock_chat_completion):
    mock_chat_completion.return_value = "- alpha\n- beta\n- gamma"

    keywords = extract_keywords("Example text")

    assert keywords == ["alpha", "beta", "gamma"]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_parses_comma_separated(mock_chat_completion):
    mock_chat_completion.return_value = "alpha, beta, gamma"

    keywords = extract_keywords("Example text")

    assert keywords == ["alpha", "beta", "gamma"]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_parses_numbered_list(mock_chat_completion):
    mock_chat_completion.return_value = "1. alpha\n2. beta\n3. gamma"

    keywords = extract_keywords("Example text")

    assert keywords == ["alpha", "beta", "gamma"]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_parses_invalid_json_array(mock_chat_completion):
    mock_chat_completion.return_value = "[alpha, beta, gamma]"  # Missing quotes

    keywords = extract_keywords("Example text")

    assert keywords == ["alpha", "beta", "gamma"]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_parses_json_with_trailing_comma(mock_chat_completion):
    mock_chat_completion.return_value = '["alpha", "beta", "gamma",]'  # Trailing comma

    keywords = extract_keywords("Example text")

    assert keywords == ["alpha", "beta", "gamma"]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_rejects_unparseable_text(mock_chat_completion):
    mock_chat_completion.return_value = "This is just a paragraph with no list structure at all."

    with pytest.raises(TextTransformError):
        extract_keywords("Example text")


@pytest.mark.parametrize("value", [0, -1, "three", 51])
def test_extract_keywords_validates_max_keywords(value):
    with pytest.raises(TextTransformError):
        extract_keywords("Example text", max_keywords=value)  # type: ignore[arg-type]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_requires_json_array(mock_chat_completion):
    mock_chat_completion.return_value = json.dumps({"keywords": []})

    with pytest.raises(TextTransformError):
        extract_keywords("Example text")


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_rejects_empty_items(mock_chat_completion):
    mock_chat_completion.return_value = json.dumps(["   ", "\n"])

    with pytest.raises(TextTransformError):
        extract_keywords("Example text")


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_extract_keywords_wraps_llm_configuration_errors(mock_chat_completion):
    mock_chat_completion.side_effect = LLMConfigurationError("missing provider")

    with pytest.raises(TextTransformError) as exc:
        extract_keywords("Example text")

    assert "missing provider" in str(exc.value)


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_summarize_document_respects_type(mock_chat_completion):
    captured = {}

    def fake_chat_completion(messages, model_hint=None):
        captured["messages"] = messages
        return "Summary"

    mock_chat_completion.side_effect = fake_chat_completion

    summary = summarize_document("Long text", summary_type="executive", model_hint=None)

    assert summary == "Summary"
    assert "Summary type: executive" in captured["messages"][1]["content"]


def test_summarize_document_validates_type():
    with pytest.raises(TextTransformError):
        summarize_document("text", summary_type="invalid")  # type: ignore[arg-type]


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_make_text_more_technical_includes_domain_and_level(mock_chat_completion):
    captured = {}

    def fake_chat_completion(messages, model_hint=None):
        captured["messages"] = messages
        return "Technical text"

    mock_chat_completion.side_effect = fake_chat_completion

    result = make_text_more_technical(
        "Some text",
        domain="medical",
        target_level="expert",
        model_hint="model-1",
    )

    assert result == "Technical text"
    body = captured["messages"][1]["content"]
    assert "medical" in body
    assert "expertise level" in body or "expert" in body


def test_make_text_more_technical_requires_text():
    with pytest.raises(TextTransformError):
        make_text_more_technical("   ")


def test_simplify_text_validation():
    with pytest.raises(TextTransformError):
        simplify_text("")


@patch("llumdocs.services.text_transform_service.common.chat_completion")
def test_simplify_text_includes_reading_level(mock_chat_completion):
    captured = {}

    def fake_chat_completion(messages, model_hint=None):
        captured["messages"] = messages
        return "Simplified"

    mock_chat_completion.side_effect = fake_chat_completion

    result = simplify_text("Complex concepts", target_reading_level="teen")

    assert result == "Simplified"
    assert "teen" in captured["messages"][1]["content"]
