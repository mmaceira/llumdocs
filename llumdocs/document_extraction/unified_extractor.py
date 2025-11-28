"""Unified document extraction for all document types via configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .core.extractor import extract_structured_data
from .document_config import get_config

T = BaseModel


def extract_document(
    doc_type: str,
    text: str,
    model: str | None = None,
    debug_dir: Path | None = None,
) -> BaseModel:
    """Extract structured data from text using document-specific configuration."""
    config = get_config(doc_type)

    # Apply text limit if configured
    text_to_use = text
    if config.text_limit and len(text) > config.text_limit:
        text_to_use = text[: config.text_limit]

    return extract_structured_data(
        text=text_to_use,
        model_class=config.model_class,
        system_prompt=config.system_prompt,
        user_prompt_template=config.user_prompt_template,
        model=model,
        debug_dir=debug_dir,
    )
