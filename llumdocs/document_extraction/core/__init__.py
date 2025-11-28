"""Generic framework for document extraction pipelines.

This module provides reusable components for any document extraction pipeline:
- LLM-based structured data extraction
- OCR extraction from PDFs and images
- PDF/image visualization and annotation
"""

from .extractor import extract_structured_data
from .ocr import extract_ocr
from .visualizer import annotate_pdf

__all__ = ["extract_structured_data", "extract_ocr", "annotate_pdf"]
