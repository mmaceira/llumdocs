"""FastAPI router for document extraction endpoints."""

from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from llumdocs.api.error_handling import handle_service_error
from llumdocs.services.document_extraction_service import (
    DocumentExtractionError,
    extract_document_data,
)

router = APIRouter(prefix="/api", tags=["document-extraction"])


@router.post(
    "/documents/extract",
    summary="Extract structured data from documents",
    description=(
        "Extract structured data from PDF or image documents. "
        "Returns JSON with extracted data and an annotated PDF showing OCR bounding boxes."
    ),
)
async def extract_document(
    file: Annotated[UploadFile, File(description="PDF or image file to extract data from")],
    doc_type: str = Form(
        ...,
        pattern="^(deliverynote|bank|payroll)$",
        description="Document type. Accepted values: 'deliverynote', 'bank', 'payroll'",
    ),
    model: str | None = Form(
        default=None,
        description=(
            "Optional LiteLLM model identifier override "
            "(e.g., 'gpt-4o-mini', 'gpt-4o'). "
            "Only OpenAI models are supported for document extraction. "
            "Ollama models are not available. "
            "Set to null or omit to use default."
        ),
    ),
    ocr_engine: str = Form(
        default="rapidocr",
        description="OCR engine to use. Accepted values: 'rapidocr', 'tesseract', 'docling'",
    ),
) -> Response:
    """
    Extract structured data from a document file (PDF or image).

    Supports three document types:
    - **deliverynote**: Delivery notes/invoices
    - **bank**: Bank statements
    - **payroll**: Spanish payroll documents (nóminas)

    The response is a JSON object containing:
    - `extracted_data`: The structured data extracted from the document
    - `annotated_pdf`: Base64-encoded annotated PDF with OCR bounding boxes

    **Example curl command:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/api/documents/extract' \
      -H 'accept: application/json' \
      -F 'file=@document.pdf' \
      -F 'doc_type=deliverynote' \
      -F 'model='
    ```
    """
    # Validate file type
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"}
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)

        try:
            # Extract data and create annotated PDF
            extracted_data, annotated_pdf_bytes = extract_document_data(
                doc_type=doc_type,
                file_path=tmp_path,
                model_hint=model if model else None,
                ocr_engine=ocr_engine,
            )

            # Return JSON response with base64-encoded PDF
            pdf_base64 = base64.b64encode(annotated_pdf_bytes).decode("utf-8")

            response_data = {
                "extracted_data": extracted_data,
                "annotated_pdf": pdf_base64,
            }

            return Response(
                content=json.dumps(response_data),
                media_type="application/json",
                status_code=status.HTTP_200_OK,
            )

        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()

    except DocumentExtractionError as exc:
        raise handle_service_error(exc) from exc
