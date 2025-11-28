"""Unified document visualization module.

This module provides a single visualization function that handles all document types
using configuration from document_config.py, eliminating code duplication.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .core.visualizer import annotate_pdf
from .document_config import get_config


def annotate_document_pdf(
    doc_type: str,
    input_pdf: Path,
    report: BaseModel,
    ocr_items: list[dict[str, Any]],
    output_pdf: Path,
    dpi: int | None = None,
    redact: bool = False,
    ocr_metadata: dict[str, Any] | None = None,
) -> Path:
    """Annotate a PDF with OCR bounding boxes and document-specific legend.

    This unified function replaces all document-type-specific visualizers by using
    configuration from document_config.py. It handles all document types (deliverynote,
    bank, payroll) with a single implementation.

    Args:
        doc_type: Document type identifier (e.g., "deliverynote", "bank", "payroll").
        input_pdf: Path to the input PDF file.
        report: Extracted document data (type depends on doc_type) to display in legend.
        ocr_items: List of OCR items with bounding boxes (from extract_ocr).
        output_pdf: Path where the annotated PDF will be saved.
        dpi: Resolution for rendering (defaults to SETTINGS.dpi).
        redact: Whether to redact sensitive information in legend.
        ocr_metadata: Optional OCR metadata with page dimensions for accurate coordinate scaling.

    Returns:
        Path to the created output PDF file.

    Raises:
        ValueError: If doc_type is not recognized.

    Example:
        >>> from llumdocs.document_extraction.core.ocr import extract_ocr
        >>> from llumdocs.document_extraction.unified_extractor import extract_document
        >>> ocr_result = extract_ocr("document.pdf")
        >>> report = extract_document("deliverynote", ocr_result["text"])
        >>> annotate_document_pdf(
        ...     "deliverynote", "document.pdf", report, ocr_result["ocr_items"], "output.pdf"
        ... )
    """
    config = get_config(doc_type)

    if not config.make_legend_lines:
        raise ValueError(f"Document type '{doc_type}' does not have legend generation configured")

    # Determine redaction function
    redact_fn = None
    if redact:
        redact_fn = config.redact_lines
        if redact_fn is None:
            # Use default redaction if none specified
            from .core.visualizer import redact_sensitive_info

            def default_redact(lines: list[str]) -> list[str]:
                text = "\n".join(lines)
                text = redact_sensitive_info(text)
                return text.splitlines()

            redact_fn = default_redact

    return annotate_pdf(
        input_pdf=input_pdf,
        ocr_items=ocr_items,
        output_pdf=output_pdf,
        legend_lines_fn=lambda: config.make_legend_lines(report),
        redact_fn=redact_fn,
        dpi=dpi,
        redact=redact,
        report=report,
        ocr_metadata=ocr_metadata,
    )
