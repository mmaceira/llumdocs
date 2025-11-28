"""UI panel components for LlumDocs Gradio interface."""

from __future__ import annotations

from llumdocs.ui.panels.common import LANGUAGE_OPTIONS
from llumdocs.ui.panels.document_extraction import create_document_extraction_panel
from llumdocs.ui.panels.email_intelligence import create_email_intelligence_panel
from llumdocs.ui.panels.image import create_image_panel
from llumdocs.ui.panels.keywords import create_keywords_panel
from llumdocs.ui.panels.summary import create_summary_panel
from llumdocs.ui.panels.text_transformation import create_text_transformation_panel
from llumdocs.ui.panels.translation import create_translation_panel

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
