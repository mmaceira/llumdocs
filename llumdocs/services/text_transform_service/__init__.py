"""
Discrete services for text transformation tasks.

Each functionality previously housed in a single module now lives in its own
file to keep responsibilities focused and maintenance simpler.
"""

from .common import TextTransformError
from .company_tone import CALM_PROFESSIONAL, SERIOUS_IMPORTANT, apply_company_tone
from .keywords import extract_keywords
from .simplify import simplify_text
from .summary import SummaryType, summarize_document
from .technical import make_text_more_technical

__all__ = [
    "TextTransformError",
    "SummaryType",
    "CALM_PROFESSIONAL",
    "SERIOUS_IMPORTANT",
    "apply_company_tone",
    "extract_keywords",
    "simplify_text",
    "summarize_document",
    "make_text_more_technical",
]
