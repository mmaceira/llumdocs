"""OCR extraction using multiple engines (RapidOCR, Tesseract, Docling)."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from PIL import Image

from ..ocr import build_ocr_engine
from ..settings import SETTINGS


def _extract_with_engine(file_path: Path, ocr_engine_name: str = "rapidocr") -> dict[str, Any]:
    """Extract OCR using the specified engine.

    Args:
        file_path: Path to the document file (PDF or image).
        ocr_engine_name: OCR engine name ("rapidocr", "tesseract", or "docling").

    Returns:
        Dictionary with OCR results in the expected format.
    """
    from pdf2image import convert_from_path

    # Parse languages from settings
    ocr_langs = [lang.strip() for lang in SETTINGS.ocr_langs.split(",") if lang.strip()]
    if not ocr_langs:
        ocr_langs = ["eng"]

    # Use Docling for "docling" engine, otherwise use factory
    if ocr_engine_name == "docling":
        return _extract_with_docling(file_path)

    # Build OCR engine
    ocr_engine = build_ocr_engine(name=ocr_engine_name, langs=ocr_langs)

    t0 = time.perf_counter()
    pages = []

    # Determine file type
    file_ext = file_path.suffix.lower()
    is_pdf = file_ext == ".pdf"

    if is_pdf:
        # Convert PDF pages to images
        pdf_images = convert_from_path(str(file_path), dpi=300)
        for page_idx, img in enumerate(pdf_images):
            page = ocr_engine.recognize_page(img, page_idx)
            pages.append(page)
    else:
        # Process single image
        img = Image.open(file_path).convert("RGB")
        page = ocr_engine.recognize_page(img, 0)
        pages.append(page)

    total_runtime = time.perf_counter() - t0

    # Get engine config (store relevant args)
    engine_config = {
        "langs": ocr_langs,
    }
    if hasattr(ocr_engine, "oem"):
        engine_config["tesseract_oem"] = ocr_engine.oem
        engine_config["tesseract_psm"] = ocr_engine.psm
        if hasattr(ocr_engine, "extra_cfg") and ocr_engine.extra_cfg:
            engine_config["tesseract_extra"] = ocr_engine.extra_cfg

    # Convert pages to result format
    full_text = "\n\n".join(p.text for p in pages)

    # Convert words to ocr_items format
    ocr_items = []
    for page in pages:
        for word in page.words:
            ocr_items.append(
                {
                    "page_no": page.page_index + 1,  # Convert to 1-indexed
                    "text": word.text,
                    "bbox": {
                        "l": word.bbox[0],
                        "t": word.bbox[1],
                        "r": word.bbox[2],
                        "b": word.bbox[3],
                        "x0": word.bbox[0],
                        "y0": word.bbox[1],
                        "x1": word.bbox[2],
                        "y1": word.bbox[3],
                    },
                }
            )

    # Generate markdown (simple conversion from text)
    markdown = full_text.replace("\n\n", "\n\n")

    return {
        "text": full_text,
        "markdown": markdown,
        "ocr_items": ocr_items,
        "metadata": {
            "ocr": {
                "engine": ocr_engine_name,
                "engine_config": engine_config,
                "runtime_sec": total_runtime,
                "pages": [
                    {
                        "page_index": p.page_index,
                        "width": p.width,
                        "height": p.height,
                        "runtime_sec": p.runtime_sec,
                    }
                    for p in pages
                ],
            }
        },
    }


def _extract_with_docling(file_path: Path) -> dict[str, Any]:
    """Extract OCR using Docling (original implementation).

    Args:
        file_path: Path to the document file.

    Returns:
        Dictionary with OCR results in the expected format.
    """
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        AcceleratorDevice,
        AcceleratorOptions,
        OcrAutoOptions,
        PdfPipelineOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions()
    opts.do_ocr = True
    opts.do_table_structure = False
    opts.images_scale = SETTINGS.images_scale
    if SETTINGS.max_pages is not None:
        opts.max_pages = SETTINGS.max_pages

    ocr_opts = OcrAutoOptions()
    ocr_langs = [lang.strip() for lang in SETTINGS.ocr_langs.split(",") if lang.strip()]
    if ocr_langs:
        ocr_opts.lang = ocr_langs
    opts.ocr_options = ocr_opts

    accel = AcceleratorOptions(
        device=AcceleratorDevice.GPU if SETTINGS.docling_gpu else AcceleratorDevice.CPU
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=opts, accelerator_options=accel)
        }
    )

    t0 = time.perf_counter()
    result = converter.convert(str(file_path))
    doc = result.document
    total_runtime = time.perf_counter() - t0

    # Extract OCR items
    ocr_items = []
    doc_dict = doc.export_to_dict()

    # Track page dimensions from bboxes if available
    page_dims: dict[int, tuple[int, int]] = {}

    for text_item in doc_dict.get("texts", []):
        if not isinstance(text_item, dict):
            continue
        text_content = text_item.get("text") or text_item.get("orig") or ""
        if not text_content:
            continue
        for prov in text_item.get("prov", []):
            if isinstance(prov, dict) and prov.get("page_no") is not None:
                page_no = int(prov["page_no"])
                bbox = prov.get("bbox", {})

                # Try to extract page dimensions from bbox if available
                # Docling coordinates are in PDF points, so we can estimate page size
                if bbox and page_no - 1 not in page_dims:
                    # Use bbox coordinates to estimate page dimensions
                    # This is approximate - Docling bboxes are in PDF points
                    right = bbox.get("r") or bbox.get("x1", 0.0)
                    bottom = bbox.get("b") or bbox.get("y1", 0.0)
                    # Estimate page size (most PDFs are standard sizes)
                    # We'll use a default if we can't determine from bboxes
                    if right > 0 and bottom > 0:
                        # Estimate based on largest bbox coordinates seen
                        page_dims[page_no - 1] = (int(right * 1.1), int(bottom * 1.1))

                item = {
                    "page_no": page_no,
                    "text": text_content.strip(),
                    "bbox": bbox,
                }
                # Split large items into smaller ones for better visualization
                split_items = _split_large_ocr_item(item)
                ocr_items.extend(split_items)

    # Build metadata (Docling uses PDF points, not pixels, so dimensions are approximate)
    ocr_langs = [lang.strip() for lang in SETTINGS.ocr_langs.split(",") if lang.strip()]
    engine_config = {
        "langs": ocr_langs,
        "images_scale": SETTINGS.images_scale,
    }

    return {
        "markdown": doc.export_to_markdown(),
        "text": doc.export_to_text(),
        "ocr_items": ocr_items,
        "metadata": {
            "ocr": {
                "engine": "docling",
                "engine_config": engine_config,
                "runtime_sec": total_runtime,
                "pages": (
                    [
                        {
                            "page_index": page_idx,
                            "width": dims[0] if dims[0] > 0 else None,
                            "height": dims[1] if dims[1] > 0 else None,
                            "runtime_sec": 0.0,  # Docling doesn't provide per-page timing
                        }
                        for page_idx, dims in page_dims.items()
                    ]
                    if page_dims
                    else []
                ),
            }
        },
    }


def _split_large_ocr_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Split large OCR items containing multiple fields into separate items."""
    text = item.get("text", "").strip()
    bbox = item.get("bbox", {})
    page_no = item.get("page_no", 1)

    # Don't split if text is short
    if len(text) < 30:
        return [item]

    # Check if text contains multiple fields (colons, pipes, or common patterns)
    colon_count = text.count(":")
    pipe_count = text.count("|")

    # Need at least 2 colons or 1 pipe to consider splitting
    if colon_count < 2 and pipe_count == 0:
        return [item]

    # Split by common separators
    parts = []

    # First, try splitting by "|" if present (e.g., "Field|Value Field|Value")
    if pipe_count > 0:
        parts = [p.strip() for p in text.split("|") if p.strip()]
    elif colon_count >= 2:
        # Split by field-value patterns: "Field: Value" followed by space and next field
        # Pattern matches: "FieldName: Value" (where Value can contain spaces)
        # Look for patterns like "Numero Delivery Note: ALB-54288 Fecha: 2025-11-27"
        pattern = r"([A-Za-zÁÉÍÓÚáéíóúÑñ\s/]+:\s*[^\s:]+(?:\s+[^\s:]+)*)"
        matches = re.findall(pattern, text)
        if len(matches) > 1:
            parts = [m.strip() for m in matches if m.strip()]
        else:
            # Fallback: split by multiple consecutive spaces (likely field separators)
            parts = re.split(r"\s{2,}", text)
            parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]

    # If we couldn't split meaningfully, return original
    if len(parts) <= 1:
        return [item]

    # Calculate bounding box dimensions
    left = bbox.get("l") or bbox.get("x0", 0.0)
    top = bbox.get("t") or bbox.get("y0", 0.0)
    right = bbox.get("r") or bbox.get("x1", 0.0)
    bottom = bbox.get("b") or bbox.get("y1", 0.0)

    bbox_width = right - left
    bbox_height = bottom - top

    # Create split items with proportional bounding boxes
    split_items = []
    current_pos = 0

    for part in parts:
        if not part.strip():
            continue

        # Find position of this part in the original text
        part_start = text.find(part, current_pos)
        if part_start == -1:
            part_start = current_pos
        part_end = part_start + len(part)
        current_pos = max(part_end, current_pos + 1)  # Avoid infinite loops

        # Calculate proportional bounding box based on text position
        total_length = len(text)
        if total_length == 0:
            continue

        part_start_ratio = part_start / total_length
        part_end_ratio = part_end / total_length

        # Estimate horizontal position (assuming left-to-right text)
        part_left = left + (bbox_width * part_start_ratio)
        part_right = left + (bbox_width * part_end_ratio)

        # For vertical positioning, estimate based on number of parts
        # If we have many parts, they might be on different lines
        num_parts = len(parts)
        if num_parts > 3 and bbox_height > bbox_width * 0.5:
            # Likely multi-line: distribute vertically
            part_index = parts.index(part)
            lines_estimate = min(num_parts, max(1, int(bbox_height / (bbox_width * 0.1))))
            line_height = bbox_height / lines_estimate
            line_num = min(part_index, lines_estimate - 1)
            part_top = top + (line_num * line_height)
            part_bottom = part_top + line_height
        else:
            # Single line or horizontal layout: use same vertical bounds
            part_top = top
            part_bottom = bottom

        split_items.append(
            {
                "page_no": page_no,
                "text": part.strip(),
                "bbox": {
                    "l": part_left,
                    "t": part_top,
                    "r": part_right,
                    "b": part_bottom,
                    "coord_origin": bbox.get("coord_origin", "BOTTOMLEFT"),
                },
            }
        )

    return split_items if len(split_items) > 1 else [item]


def extract_ocr(pdf_path: Path | str, ocr_engine: str | None = None) -> dict[str, Any]:
    """Extract OCR text and bounding boxes from PDF or image.

    Args:
        pdf_path: Path to PDF or image file.
        ocr_engine: OCR engine name ("rapidocr", "tesseract", or "docling").
            Defaults to "rapidocr" if not specified.

    Returns:
        Dictionary with "text", "markdown", and "ocr_items" (list of items with
        page_no, text, bbox).
    """
    pdf_path = Path(pdf_path)
    ocr_engine_name = ocr_engine or "rapidocr"
    return _extract_with_engine(pdf_path, ocr_engine_name)
