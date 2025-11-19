from __future__ import annotations

import io

import pytest
from PIL import Image

from llumdocs.llm import LLMConfigurationError
from llumdocs.services.image_description_service import (
    ImageDescriptionError,
    describe_image,
)


def test_describe_image_calls_vision_completion(monkeypatch):
    captured = {}

    def fake_vision_completion(prompt, image_bytes, model_hint=None):
        captured["prompt"] = prompt
        captured["image_bytes"] = image_bytes
        captured["model_hint"] = model_hint
        return "A beautiful landscape with mountains"

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    result = describe_image(
        image_bytes, detail_level="short", max_size=512, model_hint="test-model"
    )

    assert result == "A beautiful landscape with mountains"
    assert captured["model_hint"] == "test-model"
    assert "concise" in captured["prompt"].lower()
    assert captured["image_bytes"] is not None


def test_describe_image_detailed_prompt(monkeypatch):
    captured = {}

    def fake_vision_completion(prompt, image_bytes, model_hint=None):
        captured["prompt"] = prompt
        return "Detailed description"

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    describe_image(image_bytes, detail_level="detailed")

    assert "detailed" in captured["prompt"].lower()
    assert "background" in captured["prompt"].lower()
    assert "colors" in captured["prompt"].lower()


def test_describe_image_rejects_empty_bytes():
    with pytest.raises(ImageDescriptionError, match="cannot be empty"):
        describe_image(b"")


def test_describe_image_validates_detail_level():
    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    with pytest.raises(ImageDescriptionError, match="detail_level must be"):
        describe_image(image_bytes, detail_level="invalid")  # type: ignore[arg-type]


def test_describe_image_validates_max_size():
    img = Image.new("RGB", (100, 100), color="yellow")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    with pytest.raises(ImageDescriptionError, match="max_size must be greater than 0"):
        describe_image(image_bytes, max_size=0)

    with pytest.raises(ImageDescriptionError, match="max_size must be greater than 0"):
        describe_image(image_bytes, max_size=-1)


def test_describe_image_resizes_large_image(monkeypatch):
    captured = {}

    def fake_vision_completion(prompt, image_bytes, model_hint=None):
        captured["image_bytes"] = image_bytes
        # Verify the image was resized by checking size
        img = Image.open(io.BytesIO(image_bytes))
        captured["size"] = img.size
        return "Description"

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    # Create a large image (2000x2000)
    img = Image.new("RGB", (2000, 2000), color="purple")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    describe_image(image_bytes, max_size=512)

    # Verify the image was resized to max 512 on longest side
    assert captured["size"][0] <= 512 or captured["size"][1] <= 512
    assert max(captured["size"]) == 512


def test_describe_image_converts_non_rgb(monkeypatch):
    captured = {}

    def fake_vision_completion(prompt, image_bytes, model_hint=None):
        captured["image_bytes"] = image_bytes
        img = Image.open(io.BytesIO(image_bytes))
        captured["mode"] = img.mode
        return "Description"

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    # Create an RGBA image
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    image_bytes = img_bytes.getvalue()

    describe_image(image_bytes)

    # Should be converted to RGB
    assert captured["mode"] == "RGB"


def test_describe_image_wraps_llm_errors(monkeypatch):
    def fake_vision_completion(*_, **__):
        raise LLMConfigurationError("no provider")

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    with pytest.raises(ImageDescriptionError) as exc:
        describe_image(image_bytes)

    assert "no provider" in str(exc.value)


def test_describe_image_wraps_generic_errors(monkeypatch):
    def fake_vision_completion(*_, **__):
        raise ValueError("unexpected error")

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    with pytest.raises(ImageDescriptionError) as exc:
        describe_image(image_bytes)

    assert "Image description failed" in str(exc.value)
    assert "unexpected error" in str(exc.value)


@pytest.mark.parametrize("detail_level", ["short", "detailed"])
def test_describe_image_accepts_valid_detail_levels(detail_level, monkeypatch):
    def fake_vision_completion(*_, **__):
        return "Description"

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    image_bytes = img_bytes.getvalue()

    result = describe_image(image_bytes, detail_level=detail_level)
    assert result == "Description"
