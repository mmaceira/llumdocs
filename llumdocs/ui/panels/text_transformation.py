"""Text transformation panel with technical, simplify, and company tone options."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.services.text_transform_service import (
    CALM_PROFESSIONAL,
    SERIOUS_IMPORTANT,
    TextTransformError,
    apply_company_tone,
    make_text_more_technical,
    simplify_text,
)
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import (
    _resolve_model_id,
    create_error_display,
    create_llm_dropdown,
    create_processing_status,
)


def create_text_transformation_panel(
    model_map: dict[str, str], model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the unified text transformation panel with subcategories."""
    with gr.Column(visible=False) as transform_panel:
        gr.Markdown("Transform text with different styles and tones.")
        model_dropdown = create_llm_dropdown(model_choices)

        # Main transformation type selector
        transform_type = gr.Radio(
            label="Transformation type",
            choices=[
                "Make text more technical",
                "Simplify text",
                "Give text a tone aligned with the company",
            ],
            value="Make text more technical",
            elem_id="transform-type-radio",
        )

        # Technical transformation options (only visible when technical is selected)
        technical_domain = gr.Dropdown(
            label="Domain",
            choices=["tech", "legal", "medical", "finance", "general"],
            value="general",
            visible=True,
            elem_id="technical-domain-dropdown",
        )
        technical_level = gr.Dropdown(
            label="Target level",
            choices=["expert", "intermediate", "beginner"],
            value="intermediate",
            visible=True,
            elem_id="technical-level-dropdown",
        )

        # Simplify transformation options (only visible when simplify is selected)
        simplify_level = gr.Dropdown(
            label="Reading level",
            choices=["child", "teen", "adult_general"],
            value="adult_general",
            visible=False,
            elem_id="simplify-level-dropdown",
        )

        # Company tone subcategory (only visible when company tone is selected)
        company_tone_type = gr.Dropdown(
            label="Company tone style",
            choices=[
                "Company serious, important mail",
                "Company with calm tone, professional but casual",
            ],
            value="Company serious, important mail",
            visible=False,
            elem_id="company-tone-dropdown",
        )
        # Language selector for company tone (only visible when company tone is selected)
        company_tone_language = gr.Dropdown(
            label="Email language",
            choices=[
                ("Catalan", "ca"),
                ("Spanish", "es"),
                ("English", "en"),
            ],
            value="en",
            visible=False,
            elem_id="company-tone-language-dropdown",
        )
        company_tone_note = gr.Markdown(
            "*Note: Company tone transformation generates a complete email ready to send, "
            "including subject, greeting, body, closing, and signature.*",
            visible=False,
            elem_id="company-tone-note",
        )

        def update_visibility(transform_type_value: str):
            is_technical = transform_type_value == "Make text more technical"
            is_simplify = transform_type_value == "Simplify text"
            is_company_tone = transform_type_value == "Give text a tone aligned with the company"

            return [
                gr.update(visible=is_technical),  # technical_domain
                gr.update(visible=is_technical),  # technical_level
                gr.update(visible=is_simplify),  # simplify_level
                gr.update(visible=is_company_tone),  # company_tone_type
                gr.update(visible=is_company_tone),  # company_tone_language
                gr.update(visible=is_company_tone),  # company_tone_note
            ]

        transform_type.change(
            fn=update_visibility,
            inputs=[transform_type],
            outputs=[
                technical_domain,
                technical_level,
                simplify_level,
                company_tone_type,
                company_tone_language,
                company_tone_note,
            ],
            api_name=None,
        )

        transform_textbox = gr.Textbox(
            label="Text to transform",
            placeholder="Paste or write your text here…",
            lines=8,
            elem_id="transform-textbox",
        )
        transform_button = gr.Button("Transform", variant="primary")
        transform_status = create_processing_status()
        transform_output = gr.Textbox(
            label="Transformed text", lines=8, interactive=False, elem_id="transform-output"
        )
        transform_error = create_error_display()

        def run_transform(
            text: str,
            transform_type_value: str,
            domain: str,
            level: str,
            reading_level: str,
            tone_type: str,
            tone_language: str,
            model_label: str,
        ) -> tuple[str, str, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", ""
            try:
                if transform_type_value == "Make text more technical":
                    result = make_text_more_technical(
                        text, domain=domain, target_level=level, model_hint=model_id
                    )
                elif transform_type_value == "Simplify text":
                    result = simplify_text(
                        text, target_reading_level=reading_level, model_hint=model_id
                    )
                else:  # "Give text a tone aligned with the company"
                    tone_map = {
                        "Company serious, important mail": SERIOUS_IMPORTANT,
                        "Company with calm tone, professional but casual": CALM_PROFESSIONAL,
                    }
                    result = apply_company_tone(
                        text,
                        tone_type=tone_map[tone_type],
                        language=tone_language,
                        model_hint=model_id,  # type: ignore[arg-type]
                    )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except TextTransformError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        transform_button.click(
            fn=run_transform,
            inputs=[
                transform_textbox,
                transform_type,
                technical_domain,
                technical_level,
                simplify_level,
                company_tone_type,
                company_tone_language,
                model_dropdown,
            ],
            outputs=[transform_output, transform_status, transform_error],
            api_name=None,
        )

    return transform_panel, transform_button
