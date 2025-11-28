"""UI component builders for LlumDocs Gradio interface.

This module re-exports panel functions from llumdocs.ui.panels for backward compatibility.
New code should import directly from llumdocs.ui.panels.
"""

from __future__ import annotations

from llumdocs.ui.panels import (
    LANGUAGE_OPTIONS,
    create_document_extraction_panel,
    create_email_intelligence_panel,
    create_image_panel,
    create_keywords_panel,
    create_summary_panel,
    create_text_transformation_panel,
    create_translation_panel,
)

__all__ = [
    "LANGUAGE_OPTIONS",
    "create_document_extraction_panel",
    "create_email_intelligence_panel",
    "create_image_panel",
    "create_keywords_panel",
    "create_summary_panel",
    "create_text_transformation_panel",
    "create_translation_panel",
]
