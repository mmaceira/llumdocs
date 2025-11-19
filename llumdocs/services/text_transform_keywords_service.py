from __future__ import annotations

import json

from .text_transform_common_service import TextTransformError, _call_llm, _validate_text


def extract_keywords(
    text: str,
    *,
    max_keywords: int = 10,
    model_hint: str | None = None,
) -> list[str]:
    """
    Return a list of relevant keywords for `text`.
    """

    _validate_text(text)
    if not isinstance(max_keywords, int) or max_keywords <= 0:
        raise TextTransformError("max_keywords must be a positive integer.")
    if max_keywords > 50:
        raise TextTransformError("max_keywords must be <= 50.")

    system_prompt = (
        "You extract concise keywords from a document. "
        "Return ONLY a JSON array of strings without duplicates. "
        "Do not include explanations, numbering, or additional keys."
    )
    user_prompt = (
        f"Maximum keywords: {max_keywords}\n"
        "List the most relevant keywords or short phrases.\n"
        "Text:\n"
        f"{text.strip()}"
    )
    raw_response = _call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model_hint=model_hint,
    )

    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise TextTransformError("Model response was not valid JSON.") from exc

    if not isinstance(parsed, list):
        raise TextTransformError("Model response must be a JSON array.")

    keywords: list[str] = []
    for item in parsed[:max_keywords]:
        if isinstance(item, str):
            keyword = item.strip()
            if keyword:
                keywords.append(keyword)

    if not keywords:
        raise TextTransformError("No keywords returned by the model.")

    return keywords


__all__ = ["extract_keywords"]
