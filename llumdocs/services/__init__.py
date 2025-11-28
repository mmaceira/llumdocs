"""
Public service layer for LlumDocs.

This package exposes high-level functions used by the API and UI:
translation and various text transformation utilities.
"""

from __future__ import annotations

# Email intelligence is optional (requires [email] extra with torch/transformers)
try:
    from .email_intelligence_service import (
        DEFAULT_EMAIL_ROUTING_LABELS,
        EmailIntelligenceError,
        EmailIntelligenceService,
        analyze_sentiment,
        classify_email,
        detect_phishing,
    )

    EMAIL_INTEL_AVAILABLE = True
except ImportError:
    EMAIL_INTEL_AVAILABLE = False
    # Create dummy exports for type checking and runtime checks
    DEFAULT_EMAIL_ROUTING_LABELS = []  # type: ignore[assignment]
    EmailIntelligenceError = RuntimeError  # type: ignore[assignment, misc]
    EmailIntelligenceService = None  # type: ignore[assignment, misc]
    analyze_sentiment = None  # type: ignore[assignment, misc]
    classify_email = None  # type: ignore[assignment, misc]
    detect_phishing = None  # type: ignore[assignment, misc]

from .document_extraction_service import (
    DocumentExtractionError,
    extract_document_data,
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
    "DocumentExtractionError",
    "extract_document_data",
    "EMAIL_INTEL_AVAILABLE",
    "DEFAULT_EMAIL_ROUTING_LABELS",
    "EmailIntelligenceError",
    "EmailIntelligenceService",
    "classify_email",
    "detect_phishing",
    "analyze_sentiment",
]
