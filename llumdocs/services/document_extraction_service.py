"""Document extraction service for structured data extraction from documents."""

from __future__ import annotations

import tempfile
from pathlib import Path

from llumdocs.document_extraction.core.ocr import extract_ocr
from llumdocs.document_extraction.unified_extractor import extract_document
from llumdocs.document_extraction.unified_visualizer import annotate_document_pdf
from llumdocs.llm import LLMConfigurationError


class DocumentExtractionError(Exception):
    """Raised when document extraction cannot be completed."""


def extract_document_data(
    doc_type: str,
    file_path: Path,
    model_hint: str | None = None,
    ocr_engine: str | None = None,
) -> tuple[dict, bytes]:
    """Extract structured data from a document file (PDF or image) and return annotated PDF.

    Args:
        doc_type: Document type identifier ("deliverynote", "bank", or "payroll").
        file_path: Path to the input PDF or image file.
        model_hint: Optional LiteLLM model identifier override. Only OpenAI models are supported.
        ocr_engine: Optional OCR engine name ("rapidocr", "tesseract", or "docling").
            Defaults to "rapidocr" if not specified.

    Returns:
        Tuple of (extracted_data_dict, annotated_pdf_bytes).

    Raises:
        DocumentExtractionError: If extraction fails or doc_type is invalid.
    """
    if not file_path or not file_path.exists():
        raise DocumentExtractionError("File does not exist or is invalid.")

    if not doc_type or not doc_type.strip():
        raise DocumentExtractionError("doc_type cannot be empty.")

    # Reject Ollama models - only OpenAI models are supported for document extraction
    if model_hint and model_hint.startswith("ollama/"):
        raise DocumentExtractionError(
            "Ollama models are not available for document extraction. "
            "Please use an OpenAI model (e.g., 'gpt-4o-mini', 'gpt-4o')."
        )

    try:
        # Step 1: Extract OCR text and bounding boxes
        ocr_result = extract_ocr(file_path, ocr_engine=ocr_engine)
        text = ocr_result["text"]
        ocr_items = ocr_result["ocr_items"]
        ocr_metadata = ocr_result.get("metadata")

        if not text or not text.strip():
            raise DocumentExtractionError("No text could be extracted from the document.")

        # Step 2: Extract structured data using LLM
        result = extract_document(
            doc_type=doc_type.strip(),
            text=text.strip(),
            model=model_hint,
        )

        # Step 3: Create annotated PDF
        with tempfile.TemporaryDirectory() as tmpdir:
            output_pdf = Path(tmpdir) / "annotated.pdf"
            annotate_document_pdf(
                doc_type=doc_type.strip(),
                input_pdf=file_path,
                report=result,
                ocr_items=ocr_items,
                output_pdf=output_pdf,
                ocr_metadata=ocr_metadata,
            )
            annotated_pdf_bytes = output_pdf.read_bytes()

        return result.model_dump(), annotated_pdf_bytes

    except ValueError as exc:
        # Invalid doc_type
        raise DocumentExtractionError(str(exc)) from exc
    except LLMConfigurationError as exc:
        raise DocumentExtractionError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise DocumentExtractionError(f"Extraction failed: {exc}") from exc


def extract_document_from_text(
    doc_type: str,
    text: str,
    model_hint: str | None = None,
) -> dict:
    """Extract structured data from text (no file, no PDF annotation).

    Args:
        doc_type: Document type identifier ("deliverynote", "bank", or "payroll").
        text: Text content to extract data from.
        model_hint: Optional LiteLLM model identifier override. Only OpenAI models are supported.

    Returns:
        Dictionary with extracted data.

    Raises:
        DocumentExtractionError: If extraction fails or doc_type is invalid.
    """
    if not text or not text.strip():
        raise DocumentExtractionError("Text cannot be empty.")

    if not doc_type or not doc_type.strip():
        raise DocumentExtractionError("doc_type cannot be empty.")

    # Reject Ollama models - only OpenAI models are supported for document extraction
    if model_hint and model_hint.startswith("ollama/"):
        raise DocumentExtractionError(
            "Ollama models are not available for document extraction. "
            "Please use an OpenAI model (e.g., 'gpt-4o-mini', 'gpt-4o')."
        )

    try:
        # Extract structured data using LLM
        result = extract_document(
            doc_type=doc_type.strip(),
            text=text.strip(),
            model=model_hint,
        )

        return result.model_dump()

    except ValueError as exc:
        # Invalid doc_type
        raise DocumentExtractionError(str(exc)) from exc
    except LLMConfigurationError as exc:
        raise DocumentExtractionError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise DocumentExtractionError(f"Extraction failed: {exc}") from exc
