"""Tesseract OCR engine implementation.

This module provides a Tesseract-based OCR engine using pytesseract.
"""

from __future__ import annotations

import warnings

import pytesseract
from PIL import Image
from pytesseract import Output

from .base import OcrEngine, OcrPage, OcrWord, now, validate_bbox


class TesseractEngine(OcrEngine):
    """Tesseract OCR engine.

    Uses pytesseract to perform OCR with configurable language support,
    OEM (OCR Engine Mode), and PSM (Page Segmentation Mode).
    """

    name = "tesseract"

    def __init__(
        self,
        langs: list[str],
        oem: int = 1,
        psm: int = 6,
        extra_cfg: str = "",
        **kwargs,
    ):
        """Initialize Tesseract OCR engine.

        Args:
            langs: List of language codes (e.g., ["spa", "eng", "cat"]).
            oem: OCR Engine Mode (0-3, default: 1 for LSTM).
            psm: Page Segmentation Mode (0-13, default: 6 for uniform block).
            extra_cfg: Additional Tesseract configuration string.
            **kwargs: Additional arguments (ignored).
        """
        super().__init__(langs, **kwargs)
        # Filter out empty strings and build language string
        valid_langs = [lang.strip() for lang in langs if lang and lang.strip()]
        if not valid_langs:
            valid_langs = ["eng"]
        self.lang_str = "+".join(valid_langs)
        self.oem = oem
        self.psm = psm
        self.extra_cfg = extra_cfg

        # Check if Tesseract is available and warn if languages might not be available
        try:
            available_langs = pytesseract.get_languages()
            missing = [lang for lang in valid_langs if lang not in available_langs]
            if missing:
                warnings.warn(
                    f"Tesseract languages not found: {missing}. "
                    f"Available: {available_langs}. "
                    "Engine will continue with available languages.",
                    UserWarning,
                    stacklevel=2,
                )
        except pytesseract.TesseractNotFoundError:
            # Tesseract binary not found - this will be caught when trying to use it
            # Just proceed with initialization, error will occur during recognize_page
            pass
        except Exception:
            # If we can't check for other reasons, proceed anyway
            pass

    def _cfg(self) -> str:
        """Build Tesseract configuration string.

        Returns:
            Configuration string for pytesseract.
        """
        cfg = f"--oem {self.oem} --psm {self.psm}"
        if self.extra_cfg:
            cfg += f" {self.extra_cfg}"
        return cfg

    def recognize_page(self, img: Image.Image, page_index: int) -> OcrPage:
        """Recognize text in an image using Tesseract.

        Args:
            img: PIL Image to process.
            page_index: Zero-based page index.

        Returns:
            OcrPage containing text, words, and metadata.
        """
        t0 = now()
        width, height = img.size

        # Get word-level data with bounding boxes
        data = pytesseract.image_to_data(
            img, lang=self.lang_str, config=self._cfg(), output_type=Output.DICT
        )

        words: list[OcrWord] = []
        n = len(data["text"])

        for i in range(n):
            txt = data["text"][i].strip()
            if not txt:
                continue

            x = data["left"][i]
            y = data["top"][i]
            w = data["width"][i]
            h = data["height"][i]

            # Convert to canonical format: (x0, y0, x1, y1) as integers
            x0 = int(x)
            y0 = int(y)
            x1 = int(x + w)
            y1 = int(y + h)
            bbox = (x0, y0, x1, y1)

            # Validate bbox before creating OcrWord
            validate_bbox(bbox, width, height)

            # Confidence can be missing, default to 0
            conf = float(data.get("conf", [0] * n)[i])

            words.append(OcrWord(text=txt, bbox=bbox, conf=conf))

        # Get full text (more robust than joining words)
        full_text = pytesseract.image_to_string(img, lang=self.lang_str, config=self._cfg())

        dt = now() - t0

        return OcrPage(
            page_index=page_index,
            text=full_text,
            words=words,
            width=width,
            height=height,
            runtime_sec=dt,
        )
