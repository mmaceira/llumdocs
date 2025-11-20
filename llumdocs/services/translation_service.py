"""
Translation service implementation using LiteLLM.
"""

from __future__ import annotations

from typing import Literal

from llumdocs.llm import LLMConfigurationError, chat_completion

SUPPORTED_LANGUAGES = {
    "ca": "Catalan",
    "es": "Spanish",
    "en": "English",
}

SourceLanguage = Literal["auto", "ca", "es", "en"]
TargetLanguage = Literal["ca", "es", "en"]


class TranslationError(Exception):
    """Raised when a translation cannot be completed."""


def _validate_languages(
    source_lang: str, target_lang: str
) -> tuple[SourceLanguage, TargetLanguage]:
    source = source_lang.lower()
    target = target_lang.lower()

    if source not in {"auto", *SUPPORTED_LANGUAGES}:
        raise TranslationError(
            f"source_lang must be one of auto, ca, es, en (received {source_lang!r})."
        )

    if target not in SUPPORTED_LANGUAGES:
        raise TranslationError(f"target_lang must be one of ca, es, en (received {target_lang!r}).")

    if source != "auto" and source == target:
        raise TranslationError("source_lang and target_lang must differ.")

    return source, target  # type: ignore[return-value]


def _build_prompt(
    text: str, source_lang: SourceLanguage, target_lang: TargetLanguage
) -> list[dict[str, str]]:
    if not text or not text.strip():
        raise TranslationError("text cannot be empty.")

    source_label = "auto-detect" if source_lang == "auto" else SUPPORTED_LANGUAGES[source_lang]
    target_label = SUPPORTED_LANGUAGES[target_lang]

    instruction = (
        "You are a professional translator. "
        "Translate the user's text while preserving the meaning, tone, and formatting. "
        "If the source language is 'auto-detect', detect Catalan, Spanish, or "
        "English automatically. "
        "Return only the translated text with no explanations."
    )

    user_content = (
        f"Source language: {source_label}\n"
        f"Target language: {target_label}\n"
        "Constraints:\n"
        "- Maintain punctuation and numeric values.\n"
        "- Do not add explanations or notes.\n"
        "- Keep markdown elements if present.\n"
        "\n"
        "Text to translate:\n"
        f"{text.strip()}"
    )

    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content},
    ]


def translate_text(
    text: str,
    source_lang: SourceLanguage = "auto",
    target_lang: TargetLanguage = "ca",
    *,
    model_hint: str | None = None,
) -> str:
    """
    Translate `text` between Catalan, Spanish, and English using LiteLLM.

    Args:
        text: Content to translate.
        source_lang: "auto" or ISO-like code (ca/es/en).
        target_lang: ISO-like code (ca/es/en).
        model_hint: Optional explicit model id.

    Returns:
        The translated text as returned by the model.

    Raises:
        TranslationError: For validation or backend failures.
    """

    source, target = _validate_languages(source_lang, target_lang)
    messages = _build_prompt(text, source, target)

    try:
        return chat_completion(messages, model_hint=model_hint)
    except LLMConfigurationError as exc:
        raise TranslationError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise TranslationError(f"Translation failed: {exc}") from exc
