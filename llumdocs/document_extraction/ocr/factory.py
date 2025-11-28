"""Factory for creating OCR engines.

This module provides a factory function to create OCR engine instances
based on engine name.
"""

from __future__ import annotations

from .base import OcrEngine


def build_ocr_engine(name: str, langs: list[str], **kwargs) -> OcrEngine:
    """Build an OCR engine instance.

    Args:
        name: Engine name ("tesseract" or "rapidocr").
        langs: List of language codes (e.g., ["spa", "eng", "cat"]).
        **kwargs: Engine-specific configuration options.

    Returns:
        OcrEngine instance.

    Raises:
        ValueError: If engine name is not recognized.
        ImportError: If required dependencies for the engine are not installed.
    """
    name = (name or "rapidocr").lower().strip()

    if name == "tesseract":
        # Lazy import to avoid requiring pytesseract at module level
        from .tesseract_engine import TesseractEngine

        return TesseractEngine(langs=langs, **kwargs)
    if name == "rapidocr":
        # Lazy import to avoid requiring rapidocr-onnxruntime at module level
        from .rapidocr_engine import RapidOCREngine

        return RapidOCREngine(langs=langs, **kwargs)
    raise ValueError(f"Unknown OCR engine: {name}. Supported engines: 'tesseract', 'rapidocr'")
