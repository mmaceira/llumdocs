from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from llumdocs.api.app import create_app
from llumdocs.services.image_description_service import ImageDescriptionError
from llumdocs.services.text_transform_service import TextTransformError
from llumdocs.services.translation_service import TranslationError


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_keywords_endpoint_success(monkeypatch, client):
    monkeypatch.setattr(
        "llumdocs.api.text_tools_endpoints.extract_keywords",
        lambda *_, **__: ["alpha", "beta"],
    )

    response = client.post(
        "/api/text/keywords",
        json={"text": "Example", "max_keywords": 5, "model": None},
    )

    assert response.status_code == 200
    assert response.json() == {"keywords": ["alpha", "beta"]}


def test_keywords_endpoint_error(monkeypatch, client):
    def fake_extract(*_, **__):
        raise TextTransformError("bad input")

    monkeypatch.setattr("llumdocs.api.text_tools_endpoints.extract_keywords", fake_extract)

    response = client.post("/api/text/keywords", json={"text": "Example"})

    assert response.status_code == 400
    assert response.json()["detail"] == "bad input"


def test_summarize_endpoint_success(monkeypatch, client):
    monkeypatch.setattr(
        "llumdocs.api.text_tools_endpoints.summarize_document",
        lambda *_, **__: "Summary text",
    )

    response = client.post(
        "/api/documents/summarize",
        json={"text": "Long text", "summary_type": "short", "model": None},
    )

    assert response.status_code == 200
    assert response.json() == {"summary": "Summary text"}


def test_make_technical_endpoint_success(monkeypatch, client):
    monkeypatch.setattr(
        "llumdocs.api.text_tools_endpoints.make_text_more_technical",
        lambda *_, **__: "Technical version",
    )

    response = client.post(
        "/api/text/technical",
        json={"text": "Plain", "domain": "legal", "target_level": "expert", "model": None},
    )

    assert response.status_code == 200
    assert response.json() == {"technical_text": "Technical version"}


def test_plain_language_endpoint_success(monkeypatch, client):
    monkeypatch.setattr(
        "llumdocs.api.text_tools_endpoints.simplify_text",
        lambda *_, **__: "Simple text",
    )

    response = client.post(
        "/api/text/plain",
        json={"text": "Complex", "target_reading_level": "teen", "model": None},
    )

    assert response.status_code == 200
    assert response.json() == {"plain_text": "Simple text"}


def test_translation_endpoint_success(monkeypatch, client):
    monkeypatch.setattr(
        "llumdocs.api.translation_endpoints.translate_text",
        lambda *_, **__: "Hola món",
    )

    response = client.post(
        "/api/translate",
        json={"text": "Hello", "source_lang": "en", "target_lang": "ca", "model": None},
    )

    assert response.status_code == 200
    assert response.json() == {"translated_text": "Hola món"}


def test_translation_endpoint_error(monkeypatch, client):
    def fake_translate(*_, **__):
        raise TranslationError("unsupported language")

    monkeypatch.setattr("llumdocs.api.translation_endpoints.translate_text", fake_translate)

    response = client.post(
        "/api/translate",
        json={"text": "Hello", "source_lang": "en", "target_lang": "ca"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "unsupported language"


def test_image_describe_endpoint_success(monkeypatch, client):
    monkeypatch.setattr(
        "llumdocs.api.image_endpoints.describe_image",
        lambda *_, **__: "A beautiful landscape with mountains and trees",
    )

    # Create a simple test image
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    response = client.post(
        "/api/images/describe",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")},
        data={"detail_level": "short", "max_size": 512, "model": None},
    )

    assert response.status_code == 200
    assert response.json() == {"description": "A beautiful landscape with mountains and trees"}


def test_image_describe_endpoint_detailed(monkeypatch, client):
    monkeypatch.setattr(
        "llumdocs.api.image_endpoints.describe_image",
        lambda *_, **__: "Detailed description of the image",
    )

    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="blue")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    response = client.post(
        "/api/images/describe",
        files={"image": ("test.png", img_bytes, "image/png")},
        data={"detail_level": "detailed", "max_size": 1024},
    )

    assert response.status_code == 200
    assert response.json() == {"description": "Detailed description of the image"}


def test_image_describe_endpoint_rejects_non_image(monkeypatch, client):
    from io import BytesIO

    # Send a text file instead of an image
    text_file = BytesIO(b"This is not an image")

    response = client.post(
        "/api/images/describe",
        files={"image": ("test.txt", text_file, "text/plain")},
        data={"detail_level": "short"},
    )

    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


def test_image_describe_endpoint_rejects_empty_file(client):
    from io import BytesIO

    empty_file = BytesIO(b"")

    response = client.post(
        "/api/images/describe",
        files={"image": ("empty.jpg", empty_file, "image/jpeg")},
        data={"detail_level": "short"},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_image_describe_endpoint_error(monkeypatch, client):
    def fake_describe(*_, **__):
        raise ImageDescriptionError("invalid detail level")

    monkeypatch.setattr("llumdocs.api.image_endpoints.describe_image", fake_describe)

    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="green")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    response = client.post(
        "/api/images/describe",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")},
        data={"detail_level": "short"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid detail level"


def test_image_description_endpoint_calls_full_stack(monkeypatch, client):
    calls = {"vision": 0}

    def fake_vision_completion(prompt, image_bytes, model_hint=None):
        calls["vision"] += 1
        assert prompt
        assert image_bytes  # resized bytes should be non-empty
        return "Mock description from fake vision model"

    monkeypatch.setattr(
        "llumdocs.services.image_description_service.vision_completion",
        fake_vision_completion,
    )

    sample_path = Path(__file__).parent / "sample_images" / "pexels-lluis-ab-13142337-34793094.jpg"
    assert sample_path.exists(), "Sample image for tests is missing"

    with sample_path.open("rb") as image_file:
        response = client.post(
            "/api/images/describe",
            files={"image": (sample_path.name, image_file, "image/jpeg")},
            data={"detail_level": "short", "max_size": 256, "model": None},
        )

    assert response.status_code == 200
    assert response.json() == {"description": "Mock description from fake vision model"}
    assert calls["vision"] == 1
