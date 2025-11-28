"""Redaction for payroll documents."""

from __future__ import annotations

import re

from .default import redact_sensitive_info


def redact_payroll(lines: list[str]) -> list[str]:
    """Redact sensitive information from payroll legend."""
    text = "\n".join(lines)
    text = redact_sensitive_info(text)
    text = re.sub(r"\b\d{8}[A-Z]\b", "••REDACTED-DNI••", text, flags=re.I)
    text = re.sub(r"\b[A-Z]\d{7}[A-Z]\b", "••REDACTED-NIE••", text, flags=re.I)
    return text.splitlines()
