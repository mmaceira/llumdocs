from __future__ import annotations

import os
from pathlib import Path

import pytest

from llumdocs.services.text_transform_service import (
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
)

LIVE_MODELS = [
    model.strip()
    for model in os.getenv("LLUMDOCS_LIVE_TEST_MODELS", "").split(",")
    if model.strip()
]

if not LIVE_MODELS:
    pytest.skip(
        "Set LLUMDOCS_LIVE_TEST_MODELS to run live text-transform tests.",
        allow_module_level=True,
    )


def _load_sample(name: str) -> str:
    base_dir = Path(__file__).resolve().parents[1] / "sample_texts" / "text_transform"
    return (base_dir / name).read_text(encoding="utf-8").strip()


@pytest.fixture(scope="session")
def text_samples() -> dict[str, str]:
    return {
        "technical": _load_sample("technical_brief_en.txt"),
        "summary": _load_sample("summary_brief_en.txt"),
        "simplify": _load_sample("simplify_guidance_en.txt"),
    }


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_MODELS)
def test_live_keyword_extraction(text_samples: dict[str, str], model_hint: str) -> None:
    keywords = extract_keywords(
        text_samples["technical"],
        max_keywords=8,
        model_hint=model_hint,
    )

    assert isinstance(keywords, list)
    assert 1 <= len(keywords) <= 8
    assert all(isinstance(entry, str) and entry for entry in keywords)


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_MODELS)
def test_live_executive_summary(text_samples: dict[str, str], model_hint: str) -> None:
    summary = summarize_document(
        text_samples["summary"],
        summary_type="executive",
        model_hint=model_hint,
    )

    assert isinstance(summary, str)
    assert len(summary.split()) >= 25


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_MODELS)
def test_live_make_text_more_technical(text_samples: dict[str, str], model_hint: str) -> None:
    rewritten = make_text_more_technical(
        text_samples["technical"],
        domain="energy systems",
        target_level="expert",
        model_hint=model_hint,
    )

    assert isinstance(rewritten, str)
    assert rewritten.strip()
    assert rewritten.strip() != text_samples["technical"].strip()


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_MODELS)
def test_live_plain_language_conversion(
    text_samples: dict[str, str],
    model_hint: str,
) -> None:
    simplified = simplify_text(
        text_samples["simplify"],
        target_reading_level="teen",
        model_hint=model_hint,
    )

    assert isinstance(simplified, str)
    assert simplified.strip()
    assert simplified.strip() != text_samples["simplify"].strip()
