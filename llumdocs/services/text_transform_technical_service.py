from __future__ import annotations

from .text_transform_common_service import _call_llm, _validate_text


def make_text_more_technical(
    text: str,
    *,
    domain: str | None = None,
    target_level: str | None = None,
    model_hint: str | None = None,
) -> str:
    """
    Rewrite `text` with a more technical tone.
    """

    _validate_text(text)

    constraints = [
        "Use formal, technical language.",
        "Do not change the original meaning or introduce new information.",
        "Preserve critical data, quantities, and references.",
    ]
    if domain:
        constraints.append(f"Align terminology with the {domain} domain.")
    if target_level:
        constraints.append(f"Write for a {target_level} expertise level.")

    user_prompt = (
        "Produce a more technical version of the text while keeping factual content intact.\n"
        "Constraints:\n" + "\n".join(f"- {item}" for item in constraints) + "\n\nText:\n"
        f"{text.strip()}"
    )

    return _call_llm(
        [
            {
                "role": "system",
                "content": (
                    "You are an expert technical writer. Produce precise and formal prose "
                    "without explanations outside the rewritten text."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        model_hint=model_hint,
    )


__all__ = ["make_text_more_technical"]
