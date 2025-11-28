"""Document extraction panel for LlumDocs Gradio interface."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import gradio as gr

from llumdocs.services.document_extraction_service import (
    DocumentExtractionError,
    extract_document_data,
)
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import (
    _resolve_model_id,
    create_error_display,
    create_llm_dropdown,
    create_processing_status,
)


def create_document_extraction_panel(
    model_map: dict[str, str], model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the document extraction panel."""
    # Filter out Ollama models - only OpenAI models are supported for document extraction
    filtered_choices = [
        (label, model_id) for label, model_id in model_choices if not model_id.startswith("ollama/")
    ]
    filtered_model_map = {
        label: model_id
        for label, model_id in model_map.items()
        if not model_id.startswith("ollama/")
    }

    with gr.Column(visible=False) as extraction_panel:
        gr.Markdown(
            "Extract structured data from documents (delivery note, bank statements, payroll). "
            "Upload a PDF or image file to extract data and view an annotated PDF with OCR "
            "bounding boxes. "
            "**Note:** Only OpenAI models are supported for document extraction."
        )
        model_dropdown = create_llm_dropdown(filtered_choices)
        doc_type_dropdown = gr.Dropdown(
            label="Document type",
            choices=["deliverynote", "bank", "payroll"],
            value="deliverynote",
            elem_id="doc-type-dropdown",
        )
        ocr_engine_dropdown = gr.Dropdown(
            label="OCR engine",
            choices=["rapidocr", "tesseract", "docling"],
            value="rapidocr",
            elem_id="ocr-engine-dropdown",
        )
        extraction_file = gr.File(
            label="Document file (PDF or image)",
            file_types=[".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"],
            elem_id="extraction-file",
        )
        extraction_button = gr.Button("Extract data", variant="primary")
        extraction_status = create_processing_status()
        extraction_output = gr.JSON(
            label="Extracted data",
            elem_id="extraction-output",
        )
        extraction_pdf = gr.File(
            label="Annotated PDF",
            elem_id="extraction-pdf",
            visible=True,
        )
        extraction_error = create_error_display()

        def run_extraction(
            file: str | None, doc_type: str, model_label: str, ocr_engine: str
        ) -> tuple[dict, str, str | None, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, filtered_model_map)
            if err:
                return {}, "", None, ""
            if not file:
                return {}, "", None, "Please upload a document file."
            try:
                file_path = Path(file)
                result, annotated_pdf_bytes = extract_document_data(
                    doc_type=doc_type,
                    file_path=file_path,
                    model_hint=model_id,
                    ocr_engine=ocr_engine,
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"

                # Save annotated PDF to temporary file for Gradio to display
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(annotated_pdf_bytes)
                    tmp_path = tmp_file.name

                return result, status_msg, tmp_path, ""
            except DocumentExtractionError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return {}, status_msg, None, format_error_message(exc)

        extraction_button.click(
            fn=run_extraction,
            inputs=[extraction_file, doc_type_dropdown, model_dropdown, ocr_engine_dropdown],
            outputs=[extraction_output, extraction_status, extraction_pdf, extraction_error],
        )

    return extraction_panel, extraction_button
