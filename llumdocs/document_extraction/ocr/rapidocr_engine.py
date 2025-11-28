"""RapidOCR engine implementation.

This module provides a RapidOCR-based OCR engine using rapidocr-onnxruntime.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from .base import OcrEngine, OcrPage, OcrWord, now, validate_bbox


class RapidOCREngine(OcrEngine):
    """RapidOCR engine.

    Uses rapidocr-onnxruntime for fast OCR with ONNX Runtime backend.
    RapidOCR has strong performance on Latin scripts and doesn't require
    language-specific models like Tesseract.
    """

    name = "rapidocr"

    def __init__(self, langs: list[str], **kwargs):
        """Initialize RapidOCR engine.

        Args:
            langs: List of language codes (ignored for RapidOCR).
            **kwargs: Additional arguments passed to RapidOCR constructor
                (e.g., det_model_path, rec_model_path, use_gpu).
        """
        super().__init__(langs, **kwargs)
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as e:
            raise ImportError(
                "rapidocr-onnxruntime is not installed. "
                "Install it with: pip install rapidocr-onnxruntime"
            ) from e

        # RapidOCR doesn't use language tags like Tesseract
        # It's optimized for Latin scripts by default
        # Allow kwargs passthrough for model paths, GPU, etc.
        self.ocr = RapidOCR(**kwargs)

    @staticmethod
    def _poly_to_bbox(poly: list[list[int]]) -> tuple[int, int, int, int]:
        """Convert polygon coordinates to axis-aligned bounding box.

        RapidOCR returns quadrilateral polygons, but we convert them to
        axis-aligned boxes for consistency with Tesseract output.

        Args:
            poly: List of 4 points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]].

        Returns:
            Bounding box as (x0, y0, x1, y1).
        """
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))

    def recognize_page(self, img: Image.Image, page_index: int) -> OcrPage:
        """Recognize text in an image using RapidOCR.

        Args:
            img: PIL Image to process.
            page_index: Zero-based page index.

        Returns:
            OcrPage containing text, words, and metadata.
        """
        t0 = now()
        width, height = img.size

        # Convert PIL Image to numpy array (RGB)
        np_img = np.array(img.convert("RGB"))

        # RapidOCR returns (result, elapsed_time)
        # result is a list of [polygon, text, score] tuples
        result, _ = self.ocr(np_img)

        words: list[OcrWord] = []
        texts: list[str] = []

        if result:
            for poly, txt, score in result:
                bbox = self._poly_to_bbox(poly)
                txt_clean = txt.strip()
                if txt_clean:
                    # Validate bbox before creating OcrWord
                    validate_bbox(bbox, width, height)
                    words.append(OcrWord(text=txt_clean, bbox=bbox, conf=float(score)))
                    texts.append(txt_clean)

        # Join texts with newlines (RapidOCR typically returns line-by-line)
        full_text = "\n".join(texts)

        dt = now() - t0

        return OcrPage(
            page_index=page_index,
            text=full_text,
            words=words,
            width=width,
            height=height,
            runtime_sec=dt,
        )
