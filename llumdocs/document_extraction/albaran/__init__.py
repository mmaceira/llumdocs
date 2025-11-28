"""Delivery note-specific data models.

This module provides delivery note data models.
For extraction and visualization, use the unified functions:
- extract_document() from unified_extractor
"""

from .models import AlbaranReport, ProductoLinea

__all__ = ["AlbaranReport", "ProductoLinea"]
