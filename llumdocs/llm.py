"""
Shared LiteLLM utilities for LlumDocs.

The goal is to reuse the same configuration logic (model selection,
provider-specific kwargs) across services, API endpoints, and Gradio UI.
"""

from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from litellm import completion
from litellm.exceptions import (
    InternalServerError,
    RateLimitError,
    Timeout,
)

# Configurable timeout for LLM calls (in seconds)
LLM_TIMEOUT_SECONDS = float(os.getenv("LLUMDOCS_LLM_TIMEOUT_SECONDS", "30.0"))


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


def _candidate_vision_models(env_preference: Optional[str]) -> List[str]:
    """Return ordered list of vision model identifiers we can try."""
    preferred = env_preference or os.getenv("LLUMDOCS_DEFAULT_VISION_MODEL")
    ordered: List[str] = []

    if preferred:
        ordered.append(preferred)

    ordered.extend(
        [
            "ollama/qwen3-vl:8b",
            "o4-mini",
            "gpt-4o",
            "gpt-4o-mini",
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


def resolve_vision_model(env_preference: Optional[str] = None) -> ModelConfig:
    """
    Resolve which vision model to use and the required kwargs for LiteLLM.

    Preference order:
        1. `env_preference` argument.
        2. `LLUMDOCS_DEFAULT_VISION_MODEL` environment variable.
        3. Fallback list defined in `_candidate_vision_models`.
    """

    for model in _candidate_vision_models(env_preference):
        if model.startswith("ollama/"):
            if os.getenv("LLUMDOCS_DISABLE_OLLAMA") == "1":
                continue

            api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
            return ModelConfig(model_id=model, kwargs={"api_base": api_base})

        # Assume OpenAI-compatible API for any other model id
        if os.getenv("OPENAI_API_KEY"):
            return ModelConfig(model_id=model, kwargs={})

    raise LLMConfigurationError(
        "No vision LLM providers configured. Enable Ollama locally or set OPENAI_API_KEY."
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


def available_vision_models() -> List[Tuple[str, str]]:
    """
    Return display name plus model id for all configured vision providers.
    """

    models: List[Tuple[str, str]] = []

    if os.getenv("LLUMDOCS_DISABLE_OLLAMA") != "1":
        models.append(("Ollama (qwen3-vl:8b)", "ollama/qwen3-vl:8b"))

    if os.getenv("OPENAI_API_KEY"):
        models.append(("OpenAI (o4-mini)", "o4-mini"))
        models.append(("OpenAI (gpt-4o)", "gpt-4o"))
        models.append(("OpenAI (gpt-4o-mini)", "gpt-4o-mini"))

    return models


def chat_completion(messages: List[Dict[str, str]], model_hint: Optional[str] = None) -> str:
    """
    Execute a LiteLLM chat completion and return the assistant content.

    Retries on transient errors (connection errors, timeouts, rate limits, 5xx errors)
    with exponential backoff.
    """
    config = resolve_model(model_hint)

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            response = completion(
                model=config.model_id,
                messages=messages,
                timeout=LLM_TIMEOUT_SECONDS,
                **config.kwargs,
            )
            return response.choices[0].message.content.strip()
        except (InternalServerError, Timeout, RateLimitError):
            # Retry on transient errors
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = base_delay * (2**attempt) + (time.time() % 1)
                time.sleep(delay)
                continue
            # Last attempt failed, re-raise
            raise


def vision_completion(
    prompt: str,
    image_bytes: bytes,
    model_hint: Optional[str] = None,
) -> str:
    """
    Execute a LiteLLM vision completion and return the assistant content.

    Args:
        prompt: Text prompt describing what to do with the image.
        image_bytes: Image data as bytes.
        model_hint: Optional explicit vision model id.

    Returns:
        The model's response text.
    """
    # Detect image MIME type from magic bytes
    mime_type = "image/jpeg"  # default
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
    elif image_bytes.startswith(b"\xff\xd8\xff"):
        mime_type = "image/jpeg"
    elif image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
        mime_type = "image/gif"
    elif image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:12]:
        mime_type = "image/webp"

    # Encode image to base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{mime_type};base64,{image_base64}"

    # Build messages with image content
    # LiteLLM handles the format conversion for different providers
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url},
                },
            ],
        }
    ]

    config = resolve_vision_model(model_hint)

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            response = completion(
                model=config.model_id,
                messages=messages,
                timeout=LLM_TIMEOUT_SECONDS,
                **config.kwargs,
            )
            return response.choices[0].message.content.strip()
        except (InternalServerError, Timeout, RateLimitError):
            # Retry on transient errors
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = base_delay * (2**attempt) + (time.time() % 1)
                time.sleep(delay)
                continue
            # Last attempt failed, re-raise
            raise
