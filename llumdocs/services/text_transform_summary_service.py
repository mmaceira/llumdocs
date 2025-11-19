from __future__ import annotations

from typing import Literal

from .text_transform_common_service import TextTransformError, _call_llm, _validate_text

SummaryType = Literal["short", "detailed", "executive"]


def summarize_document(
    text: str,
    *,
    summary_type: SummaryType = "short",
    model_hint: str | None = None,
) -> str:
    """
    Produce a summary of `text` according to `summary_type`.
    """

    _validate_text(text)
    if summary_type not in {"short", "detailed", "executive"}:
        raise TextTransformError("summary_type must be short, detailed, or executive.")

    style_notes = {
        "short": "Provide 3-5 concise sentences.",
        "detailed": "Provide a thorough summary with logical sections or bullet points.",
        "executive": (
            "Provide a summary for decision-makers covering goals, key points, "
            "risks, and recommendations."
        ),
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You summarize documents faithfully. Focus on key points, avoid speculation, "
                "and do not add metadata or explanations outside the summary."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Summary type: {summary_type}\n"
                f"{style_notes[summary_type]}\n"
                "Text to summarize:\n"
                f"{text.strip()}"
            ),
        },
    ]

    return _call_llm(messages, model_hint=model_hint)


__all__ = ["SummaryType", "summarize_document"]
