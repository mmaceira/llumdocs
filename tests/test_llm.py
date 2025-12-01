"""
Tests for llumdocs.llm module, including keep_alive=0 verification for Ollama.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from llumdocs.llm import (
    LLMConfigurationError,
    available_models,
    available_vision_models,
    chat_completion,
    resolve_model,
    resolve_vision_model,
    vision_completion,
)
from llumdocs.settings import get_ollama_base


def test_resolve_model_ollama_includes_keep_alive(monkeypatch):
    """Verify that resolve_model includes keep_alive=0 for Ollama models."""
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "0")
    monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = resolve_model("ollama/llama3.1:8b")

    assert config.model_id == "ollama/llama3.1:8b"
    assert config.kwargs["api_base"] == "http://localhost:11434"
    assert config.kwargs["keep_alive"] == 0


def test_resolve_vision_model_ollama_includes_keep_alive(monkeypatch):
    """Verify that resolve_vision_model includes keep_alive=0 for Ollama models."""
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "0")
    monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = resolve_vision_model("ollama/qwen3-vl:8b")

    assert config.model_id == "ollama/qwen3-vl:8b"
    assert config.kwargs["api_base"] == "http://localhost:11434"
    assert config.kwargs["keep_alive"] == 0


@patch("llumdocs.llm.completion")
def test_chat_completion_passes_keep_alive_to_litellm(mock_completion, monkeypatch):
    """Verify that chat_completion passes keep_alive=0 to LiteLLM for Ollama models."""
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "0")
    monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Mock LiteLLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_completion.return_value = mock_response

    result = chat_completion(
        [{"role": "user", "content": "Hello"}], model_hint="ollama/llama3.1:8b"
    )

    assert result == "Test response"
    # Verify completion was called with keep_alive=0
    call_kwargs = mock_completion.call_args[1]
    assert call_kwargs["keep_alive"] == 0
    assert call_kwargs["api_base"] == "http://localhost:11434"
    assert call_kwargs["model"] == "ollama/llama3.1:8b"


@patch("llumdocs.llm.completion")
def test_vision_completion_passes_keep_alive_to_litellm(mock_completion, monkeypatch):
    """Verify that vision_completion passes keep_alive=0 to LiteLLM for Ollama models."""
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "0")
    monkeypatch.setenv("OLLAMA_API_BASE", "http://localhost:11434")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Mock LiteLLM response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test vision response"
    mock_completion.return_value = mock_response

    result = vision_completion(
        "Describe this image", b"fake_image_bytes", model_hint="ollama/qwen3-vl:8b"
    )

    assert result == "Test vision response"
    # Verify completion was called with keep_alive=0
    call_kwargs = mock_completion.call_args[1]
    assert call_kwargs["keep_alive"] == 0
    assert call_kwargs["api_base"] == "http://localhost:11434"
    assert call_kwargs["model"] == "ollama/qwen3-vl:8b"


def test_resolve_model_openai_no_keep_alive(monkeypatch):
    """Verify that resolve_model does not include keep_alive for non-Ollama models."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "1")

    config = resolve_model("gpt-4o-mini")

    assert config.model_id == "gpt-4o-mini"
    assert "keep_alive" not in config.kwargs
    assert "api_base" not in config.kwargs


def test_resolve_model_raises_when_no_provider(monkeypatch):
    """Verify that resolve_model raises when no provider is available."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "1")

    with pytest.raises(LLMConfigurationError):
        resolve_model()


def test_available_models_includes_ollama(monkeypatch):
    """Verify that available_models includes Ollama when enabled."""
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "0")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    models = available_models()

    assert len(models) >= 1
    assert any("ollama" in model_id.lower() for _, model_id in models)


def test_get_ollama_base_uses_env_when_set(monkeypatch):
    """get_ollama_base should reflect OLLAMA_API_BASE and strip trailing slash."""
    monkeypatch.setenv("OLLAMA_API_BASE", "http://example:1234/")
    base = get_ollama_base()
    assert base == "http://example:1234"


def test_available_vision_models_includes_ollama(monkeypatch):
    """Verify that available_vision_models includes Ollama when enabled."""
    monkeypatch.setenv("LLUMDOCS_DISABLE_OLLAMA", "0")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    models = available_vision_models()

    assert len(models) >= 1
    assert any("ollama" in model_id.lower() for _, model_id in models)
