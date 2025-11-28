"""Unit tests for document extraction service."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from llumdocs.services.document_extraction_service import (
    DocumentExtractionError,
    extract_document_data,
)


def test_extract_document_data_nonexistent_file():
    """Test that nonexistent file raises DocumentExtractionError."""
    with pytest.raises(DocumentExtractionError, match="File does not exist"):
        extract_document_data("albaran", Path("/nonexistent/file.pdf"))


def test_extract_document_data_empty_doc_type(monkeypatch):
    """Test that empty doc_type raises DocumentExtractionError."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:
        with pytest.raises(DocumentExtractionError, match="doc_type cannot be empty"):
            extract_document_data("", tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_extract_document_data_invalid_doc_type(monkeypatch):
    """Test that invalid doc_type raises DocumentExtractionError."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:
        # Mock OCR to return text, but extract_document will fail with invalid doc_type
        def mock_extract_ocr(file_path, **kwargs):
            return {"text": "test text", "ocr_items": []}

        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_ocr", mock_extract_ocr
        )

        with pytest.raises(DocumentExtractionError):
            extract_document_data("invalid_type", tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_extract_document_data_albaran_success(monkeypatch):
    """Test successful extraction for albaran document type."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:
        # Mock OCR result
        def mock_extract_ocr(file_path, **kwargs):
            return {"text": "test text", "ocr_items": [{"page_no": 1, "text": "test", "bbox": {}}]}

        # Mock extract_document
        mock_result = type(
            "MockResult", (), {"model_dump": lambda self: {"numero_albaran": "123"}}
        )()

        def mock_extract_document(doc_type, text, model):
            assert doc_type == "albaran"
            assert text == "test text"
            return mock_result

        # Mock annotate_document_pdf
        def mock_annotate_pdf(doc_type, input_pdf, report, ocr_items, output_pdf, **kwargs):
            output_pdf.write_bytes(b"fake annotated pdf")

        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_ocr", mock_extract_ocr
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_document", mock_extract_document
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.annotate_document_pdf", mock_annotate_pdf
        )

        result, pdf_bytes = extract_document_data("albaran", tmp_path)
        assert result == {"numero_albaran": "123"}
        assert pdf_bytes == b"fake annotated pdf"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_extract_document_data_bank_success(monkeypatch):
    """Test successful extraction for bank document type."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:

        def mock_extract_ocr(file_path, **kwargs):
            return {"text": "test text", "ocr_items": [{"page_no": 1, "text": "test", "bbox": {}}]}

        mock_result = type("MockResult", (), {"model_dump": lambda self: {"banco": "Test Bank"}})()

        def mock_extract_document(doc_type, text, model):
            assert doc_type == "bank"
            return mock_result

        def mock_annotate_pdf(doc_type, input_pdf, report, ocr_items, output_pdf, **kwargs):
            output_pdf.write_bytes(b"fake annotated pdf")

        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_ocr", mock_extract_ocr
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_document", mock_extract_document
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.annotate_document_pdf", mock_annotate_pdf
        )

        result, pdf_bytes = extract_document_data("bank", tmp_path)
        assert result == {"banco": "Test Bank"}
        assert pdf_bytes == b"fake annotated pdf"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_extract_document_data_payroll_success(monkeypatch):
    """Test successful extraction for payroll document type."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:

        def mock_extract_ocr(file_path, **kwargs):
            return {"text": "test text", "ocr_items": [{"page_no": 1, "text": "test", "bbox": {}}]}

        mock_result = type(
            "MockResult", (), {"model_dump": lambda self: {"empresa_nif": "12345678A"}}
        )()

        def mock_extract_document(doc_type, text, model):
            assert doc_type == "payroll"
            return mock_result

        def mock_annotate_pdf(doc_type, input_pdf, report, ocr_items, output_pdf, **kwargs):
            output_pdf.write_bytes(b"fake annotated pdf")

        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_ocr", mock_extract_ocr
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_document", mock_extract_document
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.annotate_document_pdf", mock_annotate_pdf
        )

        result, pdf_bytes = extract_document_data("payroll", tmp_path)
        assert result == {"empresa_nif": "12345678A"}
        assert pdf_bytes == b"fake annotated pdf"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_extract_document_data_with_model_override(monkeypatch):
    """Test that model_hint is passed through correctly."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:

        def mock_extract_ocr(file_path, **kwargs):
            return {"text": "test text", "ocr_items": [{"page_no": 1, "text": "test", "bbox": {}}]}

        mock_result = type("MockResult", (), {"model_dump": lambda self: {}})()

        def mock_extract_document(doc_type, text, model):
            assert model == "gpt-4o-mini"
            return mock_result

        def mock_annotate_pdf(doc_type, input_pdf, report, ocr_items, output_pdf, **kwargs):
            output_pdf.write_bytes(b"fake annotated pdf")

        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_ocr", mock_extract_ocr
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_document", mock_extract_document
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.annotate_document_pdf", mock_annotate_pdf
        )

        extract_document_data("albaran", tmp_path, model_hint="gpt-4o-mini")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_extract_document_data_no_text_extracted(monkeypatch):
    """Test that empty OCR text raises DocumentExtractionError."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:

        def mock_extract_ocr(file_path, **kwargs):
            return {"text": "", "ocr_items": []}

        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_ocr", mock_extract_ocr
        )

        with pytest.raises(DocumentExtractionError, match="No text could be extracted"):
            extract_document_data("albaran", tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_extract_document_data_handles_extraction_error(monkeypatch):
    """Test that extraction errors are wrapped in DocumentExtractionError."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(b"fake pdf content")

    try:

        def mock_extract_ocr(file_path, **kwargs):
            return {"text": "test text", "ocr_items": []}

        def mock_extract_document(doc_type, text, model):
            raise RuntimeError("Extraction failed")

        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_ocr", mock_extract_ocr
        )
        monkeypatch.setattr(
            "llumdocs.services.document_extraction_service.extract_document", mock_extract_document
        )

        with pytest.raises(DocumentExtractionError, match="Extraction failed"):
            extract_document_data("albaran", tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
