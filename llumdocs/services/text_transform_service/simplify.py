from __future__ import annotations

from .common import _call_llm, _validate_text


def simplify_text(
    text: str,
    *,
    target_reading_level: str | None = None,
    model_hint: str | None = None,
) -> str:
    """
    Rewrite `text` into plain language.
    """

    _validate_text(text)

    constraints = [
        "Use clear sentences and everyday vocabulary.",
        "Explain complex ideas with simple examples.",
        "Never change the meaning or omit critical facts.",
    ]
    if target_reading_level:
        constraints.append(f"Adapt tone for {target_reading_level} readers.")

    user_prompt = (
        "Rewrite the text into an accessible plain-language version.\n"
        "Constraints:\n" + "\n".join(f"- {item}" for item in constraints) + "\n\nText:\n"
        f"{text.strip()}"
    )

    return _call_llm(
        [
            {
                "role": "system",
                "content": (
                    "You simplify texts for broad audiences. Produce only the simplified text "
                    "without commentary."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        model_hint=model_hint,
    )
