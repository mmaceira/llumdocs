"""
Shared LiteLLM utilities for LlumDocs.

The goal is to reuse the same configuration logic (model selection,
provider-specific kwargs) across services, API endpoints, and Gradio UI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from litellm import completion


class LLMConfigurationError(RuntimeError):
    """Raised when no valid LLM backend is available."""


@dataclass(frozen=True)
class ModelConfig:
    """Resolved model configuration."""

    model_id: str
    kwargs: Dict[str, Any]


def _candidate_models(env_preference: Optional[str]) -> List[str]:
    """Return ordered list of model identifiers we can try."""
    preferred = env_preference or os.getenv("LLUMDOCS_DEFAULT_MODEL")
    ordered: List[str] = []

    if preferred:
        ordered.append(preferred)

    ordered.extend(
        [
            "ollama/llama3.1:8b",
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo",
        ]
    )

    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_ordered = []
    for model in ordered:
        if model not in seen:
            unique_ordered.append(model)
            seen.add(model)

    return unique_ordered


def resolve_model(env_preference: Optional[str] = None) -> ModelConfig:
    """
    Resolve which model to use and the required kwargs for LiteLLM.

    Preference order:
        1. `env_preference` argument.
        2. `LLUMDOCS_DEFAULT_MODEL` environment variable.
        3. Fallback list defined in `_candidate_models`.
    """

    for model in _candidate_models(env_preference):
        if model.startswith("ollama/"):
            if os.getenv("LLUMDOCS_DISABLE_OLLAMA") == "1":
                continue

            api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
            return ModelConfig(model_id=model, kwargs={"api_base": api_base})

        # Assume OpenAI-compatible API for any other model id
        if os.getenv("OPENAI_API_KEY"):
            return ModelConfig(model_id=model, kwargs={})

    raise LLMConfigurationError(
        "No LLM providers configured. Enable Ollama locally or set OPENAI_API_KEY."
    )


def available_models() -> List[Tuple[str, str]]:
    """
    Return display name plus model id for all configured providers.
    """

    models: List[Tuple[str, str]] = []

    if os.getenv("LLUMDOCS_DISABLE_OLLAMA") != "1":
        models.append(("Ollama (llama3.1:8b)", "ollama/llama3.1:8b"))

    if os.getenv("OPENAI_API_KEY"):
        models.append(("OpenAI (gpt-4o-mini)", "gpt-4o-mini"))
        models.append(("OpenAI (gpt-4o)", "gpt-4o"))
        models.append(("OpenAI (gpt-3.5-turbo)", "gpt-3.5-turbo"))

    return models


def chat_completion(messages: List[Dict[str, str]], model_hint: Optional[str] = None) -> str:
    """
    Execute a LiteLLM chat completion and return the assistant content.
    """

    config = resolve_model(model_hint)
    response = completion(model=config.model_id, messages=messages, **config.kwargs)
    return response.choices[0].message.content.strip()
