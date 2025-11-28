"""Base classes for OCR engines.

This module defines the common interface and data structures for OCR engines.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from PIL import Image


@dataclass
class OcrWord:
    """Represents a single word detected by OCR.

    Attributes:
        text: The text content of the word.
        bbox: Bounding box coordinates as (x0, y0, x1, y1).
        conf: Confidence score (0.0 to 100.0).
    """

    text: str
    bbox: tuple[int, int, int, int]  # x0, y0, x1, y1
    conf: float


@dataclass
class OcrPage:
    """Represents OCR results for a single page.

    Attributes:
        page_index: Zero-based page index.
        text: Full text content of the page.
        words: List of detected words with bounding boxes.
        width: Page width in pixels.
        height: Page height in pixels.
        runtime_sec: Time taken to process this page in seconds.
    """

    page_index: int
    text: str
    words: list[OcrWord]
    width: int
    height: int
    runtime_sec: float


class OcrEngine:
    """Base class for OCR engines.

    All OCR engines must implement the recognize_page method.
    """

    name: str = "base"

    def __init__(self, langs: list[str], **kwargs):
        """Initialize the OCR engine.

        Args:
            langs: List of language codes (e.g., ["spa", "eng", "cat"]).
            **kwargs: Engine-specific configuration options.
        """
        self.langs = langs

    def recognize_page(self, img: Image.Image, page_index: int) -> OcrPage:
        """Recognize text in an image.

        Args:
            img: PIL Image to process.
            page_index: Zero-based page index.

        Returns:
            OcrPage containing text, words, and metadata.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError


def now() -> float:
    """Get current time in seconds (high precision).

    Returns:
        Current time as float (from time.perf_counter()).
    """
    return time.perf_counter()


def validate_bbox(bbox: tuple[int, int, int, int], width: int, height: int) -> None:
    """Validate bounding box format and bounds.

    Ensures the bounding box conforms to the canonical format:
    - Tuple of 4 integers: (x0, y0, x1, y1)
    - x0, y0: top-left pixel coordinates
    - x1, y1: bottom-right pixel coordinates
    - All coordinates must be within image bounds
    - x0 <= x1 and y0 <= y1

    Args:
        bbox: Bounding box tuple (x0, y0, x1, y1).
        width: Image width in pixels.
        height: Image height in pixels.

    Raises:
        ValueError: If bbox format is invalid or out of bounds.
    """
    # Validate tuple type
    if not isinstance(bbox, tuple):
        raise ValueError(f"bbox must be a tuple, got {type(bbox).__name__}: {bbox}")

    # Validate length
    if len(bbox) != 4:
        raise ValueError(f"bbox must have 4 elements, got {len(bbox)}: {bbox}")

    x0, y0, x1, y1 = bbox

    # Validate all elements are integers
    if not all(isinstance(coord, int) for coord in bbox):
        raise ValueError(
            f"bbox coordinates must be integers, got {bbox} "
            f"(types: {[type(c).__name__ for c in bbox]})"
        )

    # Validate coordinate ordering
    if x0 > x1:
        raise ValueError(f"bbox x0 ({x0}) must be <= x1 ({x1}), got {bbox}")

    if y0 > y1:
        raise ValueError(f"bbox y0 ({y0}) must be <= y1 ({y1}), got {bbox}")

    # Validate bounds
    if x0 < 0:
        raise ValueError(f"bbox x0 ({x0}) must be >= 0, got {bbox}")

    if y0 < 0:
        raise ValueError(f"bbox y0 ({y0}) must be >= 0, got {bbox}")

    if x1 > width:
        raise ValueError(f"bbox x1 ({x1}) must be <= image width ({width}), got {bbox}")

    if y1 > height:
        raise ValueError(f"bbox y1 ({y1}) must be <= image height ({height}), got {bbox}")
