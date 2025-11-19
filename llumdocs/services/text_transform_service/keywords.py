from __future__ import annotations

import json
import re

from .common import TextTransformError, _call_llm, _validate_text


def _coerce_to_json_array(text: str) -> list[str]:
    """
    Attempt to parse model output into a list of strings.

    Tries multiple strategies:
    1. Strict JSON parsing
    2. Invalid JSON array salvage (trailing commas, missing quotes, etc.)
    3. Bullet list extraction
    4. Numbered list extraction
    5. Comma-separated items (only if clearly a list)
    """
    text = text.strip()

    # Try strict JSON first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [str(item).strip() for item in data if item]
        # Reject JSON objects (dicts)
        if isinstance(data, dict):
            raise ValueError("JSON object received, expected array")
    except json.JSONDecodeError:
        pass
    except ValueError:
        raise

    # Try to fix and parse invalid JSON arrays (trailing commas, etc.)
    # First, try removing trailing comma before closing bracket
    fixed = re.sub(r",\s*\]", "]", text)
    if fixed != text:
        try:
            data = json.loads(fixed)
            if isinstance(data, list):
                return [str(item).strip() for item in data if item]
        except Exception:
            pass

    # Try to salvage invalid JSON arrays with missing quotes
    array_match = re.search(r"\[(.*?)\]", text, re.DOTALL)
    if array_match:
        raw = array_match.group(1).strip()
        if raw:  # Only if there's content inside
            # Split by comma, clean up quotes and whitespace
            parts = [p.strip().strip("\"'") for p in raw.split(",") if p.strip()]
            if parts:
                return parts

    # Extract bullet list items
    bullet_items = re.findall(r"[-•]\s*(.+)", text, re.MULTILINE)
    if bullet_items:
        return [item.strip() for item in bullet_items if item.strip()]

    # Try numbered list (1. item, 2. item, etc.)
    numbered_items = re.findall(r"\d+[.)]\s*(.+)", text, re.MULTILINE)
    if numbered_items:
        return [item.strip() for item in numbered_items if item.strip()]

    # Comma-separated list (single line, no newlines, multiple items)
    if "," in text and "\n" not in text:
        items = [x.strip() for x in text.split(",") if x.strip()]
        # Only treat as list if we have multiple items
        if len(items) > 1:
            return items

    # Last resort: split by newlines and take non-empty lines
    # Only if we have multiple lines (single line = likely not a list)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) > 1:
        # Filter out lines that look like explanations or headers
        filtered = [
            line
            for line in lines
            if not line.lower().startswith(("here", "the", "keywords", "key", "list"))
            and len(line) < 100  # Reasonable keyword length
        ]
        if filtered:
            return filtered

    raise ValueError("Could not coerce model output to a JSON array.")


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
        parsed = _coerce_to_json_array(raw_response)
    except ValueError as exc:
        raise TextTransformError(f"Could not parse model response: {exc}") from exc

    keywords: list[str] = []
    for item in parsed[:max_keywords]:
        if isinstance(item, str):
            keyword = item.strip()
            if keyword:
                keywords.append(keyword)

    if not keywords:
        raise TextTransformError("No keywords returned by the model.")

    return keywords
