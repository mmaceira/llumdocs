"""Keyword extraction panel for LlumDocs Gradio interface."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.services.text_transform_service import TextTransformError, extract_keywords
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import (
    _resolve_model_id,
    create_error_display,
    create_llm_dropdown,
    create_processing_status,
)


def create_keywords_panel(
    model_map: dict[str, str], model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the keyword extraction panel."""
    with gr.Column(visible=False) as keyword_panel:
        gr.Markdown("Extract the most relevant keywords for quick indexing.")
        model_dropdown = create_llm_dropdown(model_choices)
        keyword_textbox = gr.Textbox(
            label="Text to analyze",
            placeholder="Paste or write your text here…",
            lines=8,
            elem_id="keyword-textbox",
        )
        keyword_slider = gr.Slider(
            label="Maximum keywords",
            minimum=3,
            maximum=30,
            step=1,
            value=10,
        )
        keyword_button = gr.Button("Extract keywords", variant="primary")
        keyword_status = create_processing_status()
        keyword_output = gr.Textbox(
            label="Keywords (one per line)", lines=8, interactive=False, elem_id="keyword-output"
        )
        keyword_error = create_error_display()

        def run_keywords(text: str, max_keywords: float, model_label: str) -> tuple[str, str, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", ""
            try:
                keywords = extract_keywords(
                    text, max_keywords=int(max_keywords), model_hint=model_id
                )
                result = "\n".join(keywords)
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except TextTransformError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        keyword_button.click(
            fn=run_keywords,
            inputs=[keyword_textbox, keyword_slider, model_dropdown],
            outputs=[keyword_output, keyword_status, keyword_error],
            api_name=None,
        )

    return keyword_panel, keyword_button
