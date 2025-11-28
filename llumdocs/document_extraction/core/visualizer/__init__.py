"""PDF and image visualization and annotation module.

This module provides functionality to annotate PDF documents and images with OCR
bounding boxes and optional legend panels showing extracted information.

The module is organized into:
- common: Shared utilities (fonts, legends, coordinate conversion, redaction)
- pdf: PDF-specific visualization functions
- image: Image-specific visualization functions
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .common import (
    get_bbox_coords,
    get_font,
    map_fields_to_ocr_items,
    overlay_legend,
    redact_sensitive_info,
)
from .image import annotate_image_as_pdf
from .pdf import annotate_pdf as _annotate_pdf_pure


def annotate_pdf(
    input_pdf: Path,
    ocr_items: list[dict[str, Any]],
    output_pdf: Path,
    legend_lines_fn: Callable[[], list[str]] | None = None,
    redact_fn: Callable[[list[str]], list[str]] | None = None,
    dpi: int | None = None,
    redact: bool = False,
    report: Any | None = None,
    ocr_metadata: dict[str, Any] | None = None,
) -> Path:
    """Annotate a PDF or image with OCR bounding boxes and optional legend panel.

    This is a generic visualization function that:
    - Renders each page of the PDF/image as an image
    - Draws green bounding boxes around OCR-detected text
    - Optionally displays field tags above bounding boxes for LLM-detected fields
    - Optionally adds a legend panel on the first page
    - Optionally redacts sensitive information in the legend

    Args:
        input_pdf: Path to the input PDF or image file.
        ocr_items: List of OCR items, each with "page_no", "text", and "bbox" keys.
        output_pdf: Path where the annotated PDF will be saved.
        legend_lines_fn: Optional function that returns list of legend text lines.
        redact_fn: Optional function to redact sensitive information from legend lines.
        dpi: Resolution for rendering (defaults to SETTINGS.dpi for PDFs, Docling DPI for images).
        redact: Whether to apply redaction to legend (requires redact_fn).
        report: Optional Pydantic model with extracted fields to tag on bounding boxes.
        ocr_metadata: Optional OCR metadata with page dimensions for accurate coordinate scaling.

    Returns:
        Path to the created output PDF file.

    Example:
        >>> ocr_items = [
        ...     {"page_no": 1, "text": "Hello", "bbox": {"l": 100, "t": 200, "r": 150, "b": 220}}
        ... ]
        >>> annotate_pdf("input.pdf", ocr_items, "output.pdf")
    """
    # Check if input is an image file
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"}
    is_image = input_pdf.suffix.lower() in image_extensions

    # Create field mapping if report is provided
    field_mapping = None
    if report is not None:
        field_mapping = map_fields_to_ocr_items(report, ocr_items)

    if is_image:
        # Route to image handler
        return annotate_image_as_pdf(
            image_path=input_pdf,
            ocr_items=ocr_items,
            output_pdf=output_pdf,
            legend_lines_fn=legend_lines_fn,
            redact_fn=redact_fn,
            dpi=dpi,
            redact=redact,
            field_mapping=field_mapping,
            ocr_metadata=ocr_metadata,
        )
    # Route to PDF handler
    return _annotate_pdf_pure(
        input_pdf=input_pdf,
        ocr_items=ocr_items,
        output_pdf=output_pdf,
        legend_lines_fn=legend_lines_fn,
        redact_fn=redact_fn,
        dpi=dpi,
        redact=redact,
        field_mapping=field_mapping,
        ocr_metadata=ocr_metadata,
    )


__all__ = [
    "annotate_pdf",
    "annotate_image_as_pdf",
    "get_font",
    "overlay_legend",
    "get_bbox_coords",
    "redact_sensitive_info",
    "map_fields_to_ocr_items",
]
