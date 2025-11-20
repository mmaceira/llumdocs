"""
Top-level public API for LlumDocs.

This module re-exports the most commonly used service functions so that
applications and notebooks can simply do:

    from llumdocs import translate_text, summarize_document

instead of importing from internal subpackages.
"""

from __future__ import annotations

# Re-export public API from services
from llumdocs.services import (
    EmailIntelligenceError,
    EmailIntelligenceService,
    SummaryType,
    TextTransformError,
    TranslationError,
    analyze_sentiment,
    classify_email,
    detect_phishing,
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
    translate_text,
)

__all__ = [
    "TranslationError",
    "translate_text",
    "TextTransformError",
    "SummaryType",
    "extract_keywords",
    "make_text_more_technical",
    "simplify_text",
    "summarize_document",
    "EmailIntelligenceError",
    "EmailIntelligenceService",
    "classify_email",
    "detect_phishing",
    "analyze_sentiment",
]
