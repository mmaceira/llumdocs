"""Translation panel for LlumDocs Gradio interface."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.services.translation_service import TranslationError, translate_text
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import (
    LANGUAGE_OPTIONS,
    _resolve_model_id,
    create_error_display,
    create_llm_dropdown,
    create_processing_status,
)


def create_translation_panel(
    model_map: dict[str, str], source_map: dict[str, str], model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the translation panel with inputs and outputs."""
    with gr.Column(visible=True) as translate_panel:
        gr.Markdown("Translate text between Catalan, Spanish, and English while preserving tone.")
        model_dropdown = create_llm_dropdown(model_choices)
        translate_textbox = gr.Textbox(
            label="Text to translate",
            placeholder="Paste or write your text here…",
            lines=8,
            elem_id="translate-textbox",
        )
        source_dropdown = gr.Dropdown(
            label="Source language",
            choices=[label for label, _ in LANGUAGE_OPTIONS],
            value=LANGUAGE_OPTIONS[0][0],
            elem_id="source-language-dropdown",
        )
        target_dropdown = gr.Dropdown(
            label="Target language",
            choices=[label for label, _ in LANGUAGE_OPTIONS[1:]],
            value=LANGUAGE_OPTIONS[1][0],
            elem_id="target-language-dropdown",
        )
        translate_button = gr.Button("Translate", variant="primary")
        translate_status = create_processing_status()
        translate_output = gr.Textbox(
            label="Translated text", lines=8, interactive=False, elem_id="translate-output"
        )
        translate_error = create_error_display()

        def run_translation(
            text: str, source_label: str, target_label: str, model_label: str
        ) -> tuple[str, str, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", ""
            source_code = source_map.get(source_label, "auto")
            target_code = source_map.get(target_label, "ca")
            try:
                result = translate_text(
                    text, source_lang=source_code, target_lang=target_code, model_hint=model_id
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except TranslationError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        translate_button.click(
            fn=run_translation,
            inputs=[translate_textbox, source_dropdown, target_dropdown, model_dropdown],
            outputs=[translate_output, translate_status, translate_error],
        )

    return translate_panel, translate_button
