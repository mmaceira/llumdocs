"""Image visualization and annotation module.

This module provides functionality to annotate image files with OCR bounding
boxes and optional legend panels showing extracted information.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from ...settings import SETTINGS
from .common import (
    clip_bbox,
    draw_bbox_with_annotations,
    extract_bbox_coordinates,
    extract_ocr_dimensions,
    get_font,
    overlay_legend,
)


def annotate_image_as_pdf(
    image_path: Path,
    ocr_items: list[dict[str, Any]],
    output_pdf: Path,
    legend_lines_fn: Callable[[], list[str]] | None = None,
    redact_fn: Callable[[list[str]], list[str]] | None = None,
    dpi: int | None = None,
    redact: bool = False,
    field_mapping: dict[int, str] | None = None,
    ocr_metadata: dict[str, Any] | None = None,
) -> Path:
    """Annotate an image and save as PDF with OCR bounding boxes and optional legend.

    This function loads an image, draws green bounding boxes around OCR-detected text,
    optionally displays field tags above bounding boxes for LLM-detected fields,
    and saves the result as a PDF with optional legend panel.

    Args:
        image_path: Path to the input image file.
        ocr_items: List of OCR items, each with "page_no", "text", and "bbox" keys.
        output_pdf: Path where the annotated PDF will be saved.
        legend_lines_fn: Optional function that returns list of legend text lines.
        redact_fn: Optional function to redact sensitive information from legend lines.
        dpi: Resolution for rendering (defaults to Docling's OCR DPI).
        redact: Whether to apply redaction to legend (requires redact_fn).
        field_mapping: Optional mapping from OCR item index to field name for tagging.
        ocr_metadata: Optional OCR metadata with page dimensions for accurate coordinate scaling.

    Returns:
        Path to the created output PDF file.
    """
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # For images, use Docling's OCR DPI to match coordinate space
    # Docling uses 72 * images_scale DPI for OCR
    docling_dpi = int(round(72.0 * SETTINGS.images_scale))
    dpi = dpi or docling_dpi

    # Load image
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    img_width, img_height = img.size

    # Get OCR dimensions from metadata if available (images are single page, use index 0)
    ocr_page_dims = extract_ocr_dimensions(ocr_metadata)
    ocr_w, ocr_h = ocr_page_dims.get(0, (None, None))

    # Get OCR items for page 1 (images are single page) and add indices
    page_items = []
    for item_index, item in enumerate(ocr_items):
        if item.get("page_no", 1) == 1:
            item["_index"] = item_index
            page_items.append(item)

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

        # If OCR dimensions are available and differ from image size, scale bboxes
        if ocr_w and ocr_h and (ocr_w != img_width or ocr_h != img_height):
            # Bboxes are in OCR pixel coordinates (ocr_w x ocr_h)
            # Scale to image coordinates (img_width x img_height)
            sx = img_width / float(ocr_w)
            sy = img_height / float(ocr_h)
            left = left * sx
            top = top * sy
            right = right * sx
            bottom = bottom * sy
        else:
            # Bboxes are already in image pixel space
            # Convert BOTTOMLEFT to TOPLEFT if needed
            if bbox.get("coord_origin") == "BOTTOMLEFT":
                # In BOTTOMLEFT: y increases upward, so flip Y
                top, bottom = img_height - top, img_height - bottom
                # After flip, ensure top <= bottom (top should have smaller y than bottom)
                top, bottom = min(top, bottom), max(top, bottom)

        # Clip and validate bbox
        bbox_px = clip_bbox(left, top, right, bottom, img_width, img_height)
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

    if legend_lines_fn:
        lines = legend_lines_fn()
        if redact and redact_fn:
            lines = redact_fn(lines)
        img = overlay_legend(img, lines)

    # Save as PDF
    annotated_pages = [img.convert("RGB")]
    if annotated_pages:
        annotated_pages[0].save(
            output_pdf,
            "PDF",
            save_all=True,
            append_images=annotated_pages[1:],
            resolution=dpi,
        )

    return Path(output_pdf)
