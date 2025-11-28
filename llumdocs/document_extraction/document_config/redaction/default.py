"""Default redaction function."""

from __future__ import annotations

import re


def redact_sensitive_info(text: str) -> str:
    """Redact sensitive information from text.

    Redacts:
    - Email addresses
    - IBAN codes (format: 2 letters + 2 digits + up to 30 alphanumeric)
    - Spanish tax IDs (NIF/CIF): 8 digits followed by letter, or letter + 8 digits

    Args:
        text: Text to redact.

    Returns:
        Text with sensitive information replaced by redaction markers.
    """
    # Redact emails
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b", "••REDACTED-EMAIL••", text)
    # Redact IBAN (2 letters + 2 digits + 11-30 alphanumeric)
    text = re.sub(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", "••REDACTED-IBAN••", text, flags=re.I)
    # Redact Spanish tax IDs
    return re.sub(r"\b(\d{8}[A-Z]|[A-Z]\d{8})\b", "••REDACTED-TAXID••", text, flags=re.I)


def default_redact(lines: list[str]) -> list[str]:
    """Default redaction using redact_sensitive_info."""
    text = "\n".join(lines)
    text = redact_sensitive_info(text)
    return text.splitlines()
