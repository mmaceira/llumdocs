"""Document summary panel for LlumDocs Gradio interface."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.services.text_transform_service import TextTransformError, summarize_document
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import (
    _resolve_model_id,
    create_error_display,
    create_llm_dropdown,
    create_processing_status,
)


def create_summary_panel(
    model_map: dict[str, str], model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the document summary panel."""
    with gr.Column(visible=False) as summary_panel:
        gr.Markdown("Summarize documents as short, detailed, or executive briefs.")
        model_dropdown = create_llm_dropdown(model_choices)
        summary_textbox = gr.Textbox(
            label="Text to summarize",
            placeholder="Paste or write your text here…",
            lines=8,
            elem_id="summary-textbox",
        )
        summary_type = gr.Radio(
            label="Summary type",
            choices=["short", "detailed", "executive"],
            value="short",
        )
        gr.Markdown(
            """
            **Summary type explanations:**

            - **Short**: 3-5 concise sentences (~50-100 words). We ask the model
              to provide a brief, condensed overview of the main points.

            - **Detailed**: A thorough summary with logical sections or bullet
              points (~200-500+ words). We ask the model to provide a
              comprehensive breakdown covering all major topics and details.

            - **Executive**: A summary for decision-makers covering goals, key
              points, risks, and recommendations (~150-300 words). We ask the
              model to focus on actionable insights, strategic implications, and
              what decision-makers need to know.
            """,
            elem_classes=["caption"],
        )
        summary_button = gr.Button("Summarize", variant="primary")
        summary_status = create_processing_status()
        summary_output = gr.Textbox(
            label="Summary", lines=8, interactive=False, elem_id="summary-output"
        )
        summary_error = create_error_display()

        def run_summary(
            text: str, summary_type_value: str, model_label: str
        ) -> tuple[str, str, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", ""
            try:
                result = summarize_document(
                    text,
                    summary_type=summary_type_value,  # type: ignore[arg-type]
                    model_hint=model_id,
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except TextTransformError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        summary_button.click(
            fn=run_summary,
            inputs=[summary_textbox, summary_type, model_dropdown],
            outputs=[summary_output, summary_status, summary_error],
            api_name=None,
        )

    return summary_panel, summary_button
