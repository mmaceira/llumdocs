from __future__ import annotations

import os
from pathlib import Path

import pytest

from llumdocs.services.translation_service import translate_text

LIVE_MODELS = [
    model.strip()
    for model in os.getenv("LLUMDOCS_LIVE_TEST_MODELS", "").split(",")
    if model.strip()
]

if not LIVE_MODELS:
    pytest.skip(
        "Set LLUMDOCS_LIVE_TEST_MODELS to run live translation tests.",
        allow_module_level=True,
    )


def _load_sample(name: str) -> str:
    base_dir = Path(__file__).resolve().parents[1] / "sample_texts" / "translation"
    return (base_dir / name).read_text(encoding="utf-8").strip()


@pytest.fixture(scope="session")
def translation_samples() -> dict[str, str]:
    return {
        "en": _load_sample("customer_email_en.txt"),
        "ca": _load_sample("project_update_ca.txt"),
        "es": _load_sample("lab_report_es.txt"),
    }


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_MODELS)
def test_live_translation_en_to_ca(translation_samples: dict[str, str], model_hint: str) -> None:
    result = translate_text(
        translation_samples["en"],
        source_lang="en",
        target_lang="ca",
        model_hint=model_hint,
    )

    assert isinstance(result, str)
    assert result.strip()
    assert result.strip() != translation_samples["en"].strip()


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_MODELS)
def test_live_translation_ca_to_es(translation_samples: dict[str, str], model_hint: str) -> None:
    result = translate_text(
        translation_samples["ca"],
        source_lang="ca",
        target_lang="es",
        model_hint=model_hint,
    )

    assert isinstance(result, str)
    assert result.strip()
    assert result.strip() != translation_samples["ca"].strip()


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_MODELS)
def test_live_translation_auto_to_en(translation_samples: dict[str, str], model_hint: str) -> None:
    result = translate_text(
        translation_samples["es"],
        source_lang="auto",
        target_lang="en",
        model_hint=model_hint,
    )

    assert isinstance(result, str)
    assert result.strip()
    assert result.strip() != translation_samples["es"].strip()
