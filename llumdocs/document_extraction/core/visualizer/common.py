"""Common utilities for PDF and image visualization."""

from __future__ import annotations

import re
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def normalize_text(text: str) -> str:
    """Normalize text for matching (lowercase, remove extra whitespace).

    Args:
        text: Text to normalize.

    Returns:
        Normalized text string.
    """
    if not text:
        return ""
    # Convert to lowercase, remove extra whitespace
    return re.sub(r"\s+", " ", str(text).strip().lower())


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a font with the specified size, falling back to default if unavailable.

    Args:
        size: Font size in points.

    Returns:
        Font object (FreeTypeFont if DejaVuSans is available, otherwise default).
    """
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def overlay_legend(
    img: Image.Image, lines: list[str], title: str = "Extracted Fields"
) -> Image.Image:
    """Overlay a semi-transparent legend panel on the right side of an image.

    Args:
        img: PIL Image to overlay the legend on.
        lines: List of text lines to display in the legend.
        title: Title text for the legend panel.

    Returns:
        New Image with legend overlay applied.
    """
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    panel_width = int(width * 0.4)
    panel_x = width - panel_width

    overlay = Image.new("RGBA", (panel_width, height), (0, 0, 0, 180))
    img.paste(overlay, (panel_x, 0), overlay)

    font_title = get_font(20)
    font_body = get_font(14)

    x, y = panel_x + 15, 15
    draw.text((x, y), title, fill=(255, 255, 255), font=font_title)
    y += 30

    for line in lines:
        if not line:
            y += 5
            continue
        draw.text((x, y), line, fill=(230, 230, 230), font=font_body)
        y += 18
        if y > height - 20:
            break

    return img


def get_bbox_coords(bbox: dict[str, Any], page_height: float) -> tuple[float, float, float, float]:
    """Extract bounding box coordinates and handle coordinate system conversion.

    Converts between different coordinate systems (top-left vs bottom-left origin).

    Args:
        bbox: Bounding box dictionary with coordinates (l/t/r/b or x0/y0/x1/y1).
        page_height: Height of the page in points (for coordinate conversion).

    Returns:
        Tuple of (left, top, right, bottom) coordinates in points.
    """
    if not bbox:
        return 0.0, 0.0, 0.0, 0.0

    left = bbox.get("l") or bbox.get("x0", 0.0)
    top = bbox.get("t") or bbox.get("y0", 0.0)
    right = bbox.get("r") or bbox.get("x1", 0.0)
    bottom = bbox.get("b") or bbox.get("y1", 0.0)

    if bbox.get("coord_origin") == "BOTTOMLEFT" and page_height > 0:
        top, bottom = page_height - top, page_height - bottom

    return float(left), float(top), float(right), float(bottom)


def redact_sensitive_info(text: str) -> str:
    """Redact sensitive information from text.

    Redacts:
    - Email addresses
    - IBAN codes (format: 2 letters + 2 digits + up to 30 alphanumeric)
    - Spanish tax IDs (NIF/CIF): 8 digits followed by letter, or letter + 8 digits

    Args:
        text: Text to redact.

    Returns:
        Text with sensitive information replaced by redaction markers.
    """
    # Redact emails
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b", "••REDACTED-EMAIL••", text)
    # Redact IBAN (2 letters + 2 digits + 11-30 alphanumeric)
    text = re.sub(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", "••REDACTED-IBAN••", text, flags=re.I)
    # Redact Spanish tax IDs
    return re.sub(r"\b(\d{8}[A-Z]|[A-Z]\d{8})\b", "••REDACTED-TAXID••", text, flags=re.I)


def map_fields_to_ocr_items(report: Any, ocr_items: list[dict[str, Any]]) -> dict[int, str]:
    """Map extracted field values to OCR items by matching text content.

    Creates a mapping from OCR item index to field name when the OCR text
    matches an extracted field value.

    Args:
        report: Pydantic model with extracted fields.
        ocr_items: List of OCR items with "text" keys.

    Returns:
        Dictionary mapping OCR item index to field name.
    """
    field_mapping: dict[int, str] = {}

    if not hasattr(report, "model_dump"):
        return field_mapping

    # Get all field values from the report
    field_values = report.model_dump()

    # Normalize field values for matching
    normalized_fields: dict[str, str] = {}
    for field_name, field_value in field_values.items():
        if field_value is None:
            continue
        # Handle different value types
        if isinstance(field_value, list | dict):
            # For complex types, skip or handle differently
            continue
        normalized_value = normalize_text(str(field_value))
        if normalized_value:
            normalized_fields[field_name] = normalized_value

    # Match OCR items to field values
    for idx, ocr_item in enumerate(ocr_items):
        ocr_text = ocr_item.get("text", "").strip()
        if not ocr_text:
            continue

        normalized_ocr = normalize_text(ocr_text)

        # Try to match against field values
        for field_name, normalized_value in normalized_fields.items():
            # Check if OCR text contains the field value or vice versa
            # Use a threshold to handle partial matches
            if normalized_value in normalized_ocr or normalized_ocr in normalized_value:
                # Prefer longer matches or exact matches
                if field_name not in field_mapping.values():
                    field_mapping[idx] = field_name
                    break
            # Also check for exact match after normalization
            elif normalized_ocr == normalized_value:
                field_mapping[idx] = field_name
                break

    return field_mapping


def extract_ocr_dimensions(
    ocr_metadata: dict[str, Any] | None,
) -> dict[int, tuple[int, int]]:
    """Extract OCR page dimensions from metadata.

    Args:
        ocr_metadata: OCR metadata dictionary with "ocr" -> "pages" structure.

    Returns:
        Dictionary mapping page_index (0-based) to (width, height) tuple.
    """
    ocr_page_dims: dict[int, tuple[int, int]] = {}
    if ocr_metadata and "ocr" in ocr_metadata:
        ocr_pages = ocr_metadata["ocr"].get("pages", [])
        for page_info in ocr_pages:
            page_idx = page_info.get("page_index", 0)
            ocr_w = page_info.get("width")
            ocr_h = page_info.get("height")
            if ocr_w and ocr_h:
                ocr_page_dims[page_idx] = (int(ocr_w), int(ocr_h))
    return ocr_page_dims


def extract_bbox_coordinates(bbox: dict[str, Any]) -> tuple[float, float, float, float]:
    """Extract bounding box coordinates from dictionary.

    Supports both l/t/r/b and x0/y0/x1/y1 formats.

    Args:
        bbox: Bounding box dictionary.

    Returns:
        Tuple of (left, top, right, bottom) coordinates.
    """
    if not bbox:
        return 0.0, 0.0, 0.0, 0.0

    left = bbox.get("l") or bbox.get("x0", 0.0)
    top = bbox.get("t") or bbox.get("y0", 0.0)
    right = bbox.get("r") or bbox.get("x1", 0.0)
    bottom = bbox.get("b") or bbox.get("y1", 0.0)

    return float(left), float(top), float(right), float(bottom)


def clip_bbox(
    left: float,
    top: float,
    right: float,
    bottom: float,
    img_width: int,
    img_height: int,
) -> tuple[int, int, int, int] | None:
    """Clip and validate bounding box coordinates.

    Args:
        left: Left coordinate.
        top: Top coordinate.
        right: Right coordinate.
        bottom: Bottom coordinate.
        img_width: Image width in pixels.
        img_height: Image height in pixels.

    Returns:
        Tuple of (l_px, t_px, r_px, b_px) as integers, or None if invalid.
    """
    # Clip coordinates to image bounds
    left = max(0, min(img_width - 1, left))
    top = max(0, min(img_height - 1, top))
    right = max(0, min(img_width - 1, right))
    bottom = max(0, min(img_height - 1, bottom))

    # Validate bbox (right > left, bottom > top)
    if right <= left or bottom <= top:
        return None

    return int(round(left)), int(round(top)), int(round(right)), int(round(bottom))


def draw_bbox_with_annotations(
    draw: ImageDraw.ImageDraw,
    l_px: int,
    t_px: int,
    r_px: int,
    b_px: int,
    ocr_text: str,
    field_name: str | None = None,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None,
    tag_font: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None,
) -> None:
    """Draw a bounding box with optional field tag and OCR text.

    Args:
        draw: PIL ImageDraw object.
        l_px: Left pixel coordinate.
        t_px: Top pixel coordinate.
        r_px: Right pixel coordinate.
        b_px: Bottom pixel coordinate.
        ocr_text: OCR text to display inside the box.
        field_name: Optional field name to display as a tag above the box.
        font: Font for OCR text (defaults to get_font(9)).
        tag_font: Font for field tag (defaults to get_font(8)).
    """
    if font is None:
        font = get_font(9)
    if tag_font is None:
        tag_font = get_font(8)

    # Draw bounding box
    draw.rectangle([l_px, t_px, r_px, b_px], outline=(0, 200, 0), width=2)

    # Draw field tag if provided
    if field_name:
        tag_text = field_name
        tag_bbox = tag_font.getbbox(tag_text)
        tag_width = tag_bbox[2] - tag_bbox[0]
        tag_height = tag_bbox[3] - tag_bbox[1]

        # Position tag above the bounding box
        tag_x = l_px
        tag_y = max(0, t_px - tag_height - 4)

        # Draw tag background
        tag_bg = [
            tag_x - 2,
            tag_y - 2,
            tag_x + tag_width + 4,
            tag_y + tag_height + 2,
        ]
        draw.rectangle(tag_bg, fill=(255, 200, 0))  # Yellow/orange background
        draw.rectangle(tag_bg, outline=(200, 150, 0), width=1)

        # Draw tag text
        draw.text((tag_x, tag_y), tag_text, fill=(0, 0, 0), font=tag_font)

    # Draw OCR text inside bounding box
    text_bbox = font.getbbox(ocr_text[:30])
    text_bg = [
        l_px + 2,
        t_px + 2,
        l_px + text_bbox[2] + 4,
        t_px + text_bbox[3] + 4,
    ]
    draw.rectangle(text_bg, fill=(255, 255, 255))
    draw.text((l_px + 3, t_px + 3), ocr_text[:30], fill=(0, 0, 0), font=font)
