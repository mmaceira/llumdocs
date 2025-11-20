"""
Public service layer for LlumDocs.

This package exposes high-level functions used by the API and UI:
translation and various text transformation utilities.
"""

from __future__ import annotations

from .email_intelligence_service import (
    EmailIntelligenceError,
    EmailIntelligenceService,
    analyze_sentiment,
    classify_email,
    detect_phishing,
)
from .text_transform_service import (
    SummaryType,
    TextTransformError,
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
)
from .translation_service import TranslationError, translate_text

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
