"""Application settings and configuration.

This module provides centralized configuration management using Pydantic Settings.
All settings can be overridden via environment variables with the DOCUMENT_LLM_ prefix.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables prefixed with DOCUMENT_LLM_.
    For example, DOCUMENT_LLM_MODEL=gpt-4 will override the model setting.

    Attributes:
        openai_api_key: OpenAI API key (also reads OPENAI_API_KEY env var).
        openai_base_url: Custom OpenAI-compatible API base URL (also reads OPENAI_BASE_URL env var).
        model: LLM model name to use for extraction.
        temperature: LLM temperature (0.0 for deterministic output).
        max_output_tokens: Maximum tokens in LLM response.
        json_strict: Whether to use OpenAI strict JSON mode (falls back if unavailable).
        seed: Random seed for LLM (for reproducibility).
        docling_gpu: Whether to use GPU acceleration for Docling OCR.
        ocr_langs: Comma-separated list of OCR languages (e.g., "spa,eng,cat").
        images_scale: Image scaling factor for OCR (4.17 ≈ 300 DPI).
        max_pages: Maximum number of pages to process (None for all pages).
        deskew: Whether to apply deskew correction to scanned pages.
        binarize: Whether to apply binarization to scanned pages.
        dpi: DPI for PDF rendering and visualization.
        redact_output: Whether to redact sensitive information by default.
        outputs_dir: Default directory for output files.
    """

    # LLM
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_output_tokens: int = 2000
    json_strict: bool = True
    seed: int | None = 7

    # OCR
    docling_gpu: bool = False
    ocr_langs: str = "spa,eng,cat"
    images_scale: float = 4.17  # 4.17 ≈ 300 DPI (72 * 4.17)
    max_pages: int | None = None
    deskew: bool = True
    binarize: bool = True
    dpi: int = 300

    # Output
    redact_output: bool = False
    outputs_dir: str = "outputs"

    model_config = SettingsConfigDict(env_prefix="DOCUMENT_LLM_")


SETTINGS = Settings()
