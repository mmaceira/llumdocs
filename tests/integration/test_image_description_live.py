from __future__ import annotations

import os
from pathlib import Path

import pytest

from llumdocs.services.image_description_service import describe_image

LIVE_VISION_MODELS = [
    model.strip()
    for model in os.getenv("LLUMDOCS_LIVE_TEST_VISION_MODELS", "").split(",")
    if model.strip()
]

if not LIVE_VISION_MODELS:
    pytest.skip(
        "Set LLUMDOCS_LIVE_TEST_VISION_MODELS to run live image description tests.",
        allow_module_level=True,
    )


def _load_sample_image(name: str) -> bytes:
    """Load a sample image from the sample_images directory."""
    base_dir = Path(__file__).resolve().parents[1] / "sample_images"
    return (base_dir / name).read_bytes()


@pytest.fixture(scope="session")
def sample_image() -> bytes:
    """Load the sample image for testing."""
    return _load_sample_image("pexels-lluis-ab-13142337-34793094.jpg")


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_VISION_MODELS)
def test_live_image_description_short(sample_image: bytes, model_hint: str) -> None:
    """Test short description of an image."""
    description = describe_image(
        sample_image,
        detail_level="short",
        max_size=64,
        model_hint=model_hint,
    )

    assert isinstance(description, str)
    assert len(description) > 0
    assert len(description.split()) >= 3  # At least a few words


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_VISION_MODELS)
def test_live_image_description_detailed(sample_image: bytes, model_hint: str) -> None:
    """Test detailed description of an image."""
    description = describe_image(
        sample_image,
        detail_level="detailed",
        max_size=64,
        model_hint=model_hint,
    )

    assert isinstance(description, str)
    assert len(description) > 0
    # Detailed descriptions should be longer
    assert len(description.split()) >= 10


@pytest.mark.integration
@pytest.mark.parametrize("model_hint", LIVE_VISION_MODELS)
def test_live_image_description_different_sizes(sample_image: bytes, model_hint: str) -> None:
    """Test that different max_size values work correctly."""
    for max_size in [64]:
        description = describe_image(
            sample_image,
            detail_level="short",
            max_size=max_size,
            model_hint=model_hint,
        )

        assert isinstance(description, str)
        assert len(description) > 0
