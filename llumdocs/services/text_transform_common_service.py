from __future__ import annotations

from llumdocs.llm import LLMConfigurationError, chat_completion


class TextTransformError(Exception):
    """Raised when a text transformation cannot be completed."""


def _validate_text(text: str, *, field_name: str = "text") -> str:
    if not text or not text.strip():
        raise TextTransformError(f"{field_name} cannot be empty.")
    return text.strip()


def _call_llm(messages: list[dict[str, str]], *, model_hint: str | None) -> str:
    try:
        return chat_completion(messages, model_hint=model_hint)
    except LLMConfigurationError as exc:
        raise TextTransformError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise TextTransformError(f"LLM request failed: {exc}") from exc


__all__ = ["TextTransformError", "_call_llm", "_validate_text"]
