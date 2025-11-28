"""PDF visualization and annotation module.

This module provides functionality to annotate PDF documents with OCR bounding
boxes and optional legend panels showing extracted information.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from PIL import Image

from ...settings import SETTINGS
from .common import (
    clip_bbox,
    draw_bbox_with_annotations,
    extract_bbox_coordinates,
    extract_ocr_dimensions,
    get_font,
    overlay_legend,
)


def annotate_pdf(
    input_pdf: Path,
    ocr_items: list[dict[str, Any]],
    output_pdf: Path,
    legend_lines_fn: Callable[[], list[str]] | None = None,
    redact_fn: Callable[[list[str]], list[str]] | None = None,
    dpi: int | None = None,
    redact: bool = False,
    field_mapping: dict[int, str] | None = None,
    ocr_metadata: dict[str, Any] | None = None,
) -> Path:
    """Annotate a PDF with OCR bounding boxes and optional legend panel.

    This function:
    - Renders each page of the PDF as an image
    - Draws green bounding boxes around OCR-detected text
    - Optionally displays field tags above bounding boxes for LLM-detected fields
    - Optionally adds a legend panel on the first page
    - Optionally redacts sensitive information in the legend

    Args:
        input_pdf: Path to the input PDF file.
        ocr_items: List of OCR items, each with "page_no", "text", and "bbox" keys.
        output_pdf: Path where the annotated PDF will be saved.
        legend_lines_fn: Optional function that returns list of legend text lines.
        redact_fn: Optional function to redact sensitive information from legend lines.
        dpi: Resolution for rendering (defaults to SETTINGS.dpi).
        redact: Whether to apply redaction to legend (requires redact_fn).
        field_mapping: Optional mapping from OCR item index to field name for tagging.
        ocr_metadata: Optional OCR metadata with page dimensions for accurate coordinate scaling.

    Returns:
        Path to the created output PDF file.

    Example:
        >>> ocr_items = [
        ...     {"page_no": 1, "text": "Hello", "bbox": {"l": 100, "t": 200, "r": 150, "b": 220}}
        ... ]
        >>> annotate_pdf("input.pdf", ocr_items, "output.pdf")
    """
    dpi = dpi or SETTINGS.dpi
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    by_page: dict[int, list[dict[str, Any]]] = {}
    for item_index, item in enumerate(ocr_items):
        page_no = int(item.get("page_no", 1))
        by_page.setdefault(page_no, []).append(item)
        # Store index in item for field mapping lookup
        item["_index"] = item_index

    doc = fitz.open(input_pdf)
    annotated_pages: list[Image.Image] = []

    try:
        # Extract OCR dimensions from metadata if available
        ocr_page_dims = extract_ocr_dimensions(ocr_metadata)

        for page_idx in range(len(doc)):
            page = doc[page_idx]

            # Get OCR dimensions for this page if available
            ocr_w, ocr_h = ocr_page_dims.get(page_idx, (None, None))

            # If we have OCR dimensions, render at that exact resolution
            # Otherwise use the specified DPI
            if ocr_w and ocr_h:
                # Calculate zoom to match OCR dimensions exactly
                page_w_pt = float(page.rect.width)
                page_h_pt = float(page.rect.height)
                zoom_x = ocr_w / page_w_pt
                zoom_y = ocr_h / page_h_pt
                # Use average zoom for uniform scaling, but ensure we get close to target dimensions
                zoom = (zoom_x + zoom_y) / 2.0
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                # If the rendered size doesn't match OCR dimensions exactly, we'll scale bboxes
            else:
                zoom = dpi / 72.0
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)

            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            from PIL import ImageDraw

            draw = ImageDraw.Draw(img)

            page_items = by_page.get(page_idx + 1, [])
            page_h_pt = float(page.rect.height)
            page_w_pt = float(page.rect.width)
            scale_x = pix.width / page_w_pt
            scale_y = pix.height / page_h_pt

            font = get_font(9)
            tag_font = get_font(8)
            for item in page_items:
                ocr_text = item.get("text", "").strip()
                if not ocr_text:
                    continue

                bbox = item.get("bbox", {})
                if not bbox:
                    continue

                # Extract coordinates
                left, top, right, bottom = extract_bbox_coordinates(bbox)

                # Convert coordinates based on whether we have OCR dimensions
                if ocr_w and ocr_h:
                    # Bboxes are in OCR pixel coordinates (ocr_w x ocr_h)
                    # Scale to rendered image coordinates (pix.width x pix.height)
                    sx = pix.width / float(ocr_w)
                    sy = pix.height / float(ocr_h)
                    left = left * sx
                    top = top * sy
                    right = right * sx
                    bottom = bottom * sy
                else:
                    # Fallback to heuristic detection (for Docling or other engines)
                    # Check if bbox coordinates are in pixel space (from RapidOCR/Tesseract)
                    # vs PDF points (from Docling)
                    max_coord = max(right, bottom, abs(left), abs(top))
                    max_page_dim = max(page_w_pt, page_h_pt)
                    avg_coord = (abs(left) + abs(top) + right + bottom) / 4.0

                    if max_coord > max_page_dim * 1.2 or avg_coord > max_page_dim * 1.1:
                        # Assume 300 DPI conversion: 300 DPI / 72 DPI = 4.167
                        # Convert from 300 DPI pixels to PDF points
                        ocr_dpi = 300.0
                        points_per_pixel = 72.0 / ocr_dpi
                        left = left * points_per_pixel
                        top = top * points_per_pixel
                        right = right * points_per_pixel
                        bottom = bottom * points_per_pixel

                    # Handle coordinate system conversion (BOTTOMLEFT to TOPLEFT)
                    if bbox.get("coord_origin") == "BOTTOMLEFT" and page_h_pt > 0:
                        top, bottom = page_h_pt - top, page_h_pt - bottom

                    # Convert PDF points to pixels
                    left = left * scale_x
                    top = top * scale_y
                    right = right * scale_x
                    bottom = bottom * scale_y

                # Clip and validate bbox
                bbox_px = clip_bbox(left, top, right, bottom, pix.width, pix.height)
                if bbox_px is None:
                    continue

                l_px, t_px, r_px, b_px = bbox_px

                # Get field name if mapping exists
                item_idx = item.get("_index")
                field_name = None
                if field_mapping and item_idx is not None:
                    field_name = field_mapping.get(item_idx)

                # Draw bbox with annotations
                draw_bbox_with_annotations(
                    draw, l_px, t_px, r_px, b_px, ocr_text, field_name, font, tag_font
                )

            if page_idx == 0 and legend_lines_fn:
                lines = legend_lines_fn()
                if redact and redact_fn:
                    lines = redact_fn(lines)
                img = overlay_legend(img, lines)

            annotated_pages.append(img.convert("RGB"))
    finally:
        doc.close()

    if annotated_pages:
        annotated_pages[0].save(
            output_pdf,
            "PDF",
            save_all=True,
            append_images=annotated_pages[1:],
            resolution=dpi,
        )

    return Path(output_pdf)
