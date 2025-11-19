from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from llumdocs.api.app import create_app
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
