"""OCR engine implementations for document processing.

This module provides interchangeable OCR engines (Tesseract, RapidOCR)
with a common interface for text extraction and bounding box detection.
"""

from .base import OcrEngine, OcrPage, OcrWord
from .factory import build_ocr_engine

__all__ = ["OcrEngine", "OcrPage", "OcrWord", "build_ocr_engine"]
