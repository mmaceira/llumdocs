"""UI component builders for LlumDocs Gradio interface."""

from __future__ import annotations

import gradio as gr

from llumdocs.llm import LLMConfigurationError
from llumdocs.services.image_description_service import ImageDescriptionError, describe_image
from llumdocs.services.text_transform_service import (
    TextTransformError,
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
)
from llumdocs.services.translation_service import TranslationError, translate_text

LANGUAGE_OPTIONS = [
    ("Auto detect (Catalan/Spanish/English)", "auto"),
    ("Catalan", "ca"),
    ("Spanish", "es"),
    ("English", "en"),
]


def create_model_dropdown(
    model_choices: list[tuple[str, str]], vision_model_choices: list[tuple[str, str]]
) -> tuple[gr.Dropdown, gr.Dropdown]:
    """Create model selection dropdowns for text and vision models."""
    model_labels = [label for label, _ in model_choices] or ["No providers available"]
    vision_model_labels = [label for label, _ in vision_model_choices] or ["No providers available"]

    model_dropdown = gr.Dropdown(
        label="Select provider",
        choices=model_labels,
        value=model_labels[0],
        interactive=bool(model_choices),
    )

    vision_model_dropdown = gr.Dropdown(
        label="Vision model",
        choices=vision_model_labels,
        value=vision_model_labels[0] if vision_model_labels else None,
        interactive=bool(vision_model_choices),
    )

    return model_dropdown, vision_model_dropdown


def create_translation_panel(
    model_map: dict[str, str], source_map: dict[str, str], model_dropdown: gr.Dropdown
) -> tuple[gr.Column, callable]:
    """Create the translation panel with inputs and outputs."""
    with gr.Column(visible=True) as translate_panel:
        gr.Markdown(
            "Translate text between Catalan, Spanish, and English " "while preserving tone."
        )
        translate_textbox = gr.Textbox(
            label="Text to translate",
            placeholder="Paste or write your text here…",
            lines=8,
        )
        source_dropdown = gr.Dropdown(
            label="Source language",
            choices=[label for label, _ in LANGUAGE_OPTIONS],
            value=LANGUAGE_OPTIONS[0][0],
        )
        target_dropdown = gr.Dropdown(
            label="Target language",
            choices=[option for option, code in LANGUAGE_OPTIONS if code != "auto"],
            value="Catalan",
        )
        translate_button = gr.Button("Translate", variant="primary")
        translation_output = gr.Textbox(label="Translated text", lines=8, interactive=False)
        translation_error = gr.Markdown("")

        def _resolve_model_id(model_label: str) -> tuple[str | None, str]:
            model_id = model_map.get(model_label)
            if not model_id:
                return None, "Invalid model selection."
            return model_id, ""

        def run_translation(
            text: str,
            source_label: str,
            target_label: str,
            model_label: str,
        ) -> tuple[str, str]:
            source_code = source_map[source_label]
            target_code = source_map[target_label]
            model_id, err = _resolve_model_id(model_label)
            if err:
                return "", err
            try:
                translated = translate_text(
                    text,
                    source_lang=source_code,
                    target_lang=target_code,
                    model_hint=model_id,
                )
                return translated, ""
            except (TranslationError, LLMConfigurationError) as exc:
                return "", str(exc)

        translate_button.click(
            fn=run_translation,
            inputs=[translate_textbox, source_dropdown, target_dropdown, model_dropdown],
            outputs=[translation_output, translation_error],
        )

    return translate_panel, translate_button


def create_summary_panel(
    model_map: dict[str, str], model_dropdown: gr.Dropdown
) -> tuple[gr.Column, callable]:
    """Create the document summary panel."""
    with gr.Column(visible=False) as summary_panel:
        gr.Markdown("Summarize documents as short, detailed, or executive briefs.")
        summary_textbox = gr.Textbox(
            label="Text to summarize",
            placeholder="Paste or write your text here…",
            lines=8,
        )
        summary_type = gr.Radio(
            label="Summary type",
            choices=["short", "detailed", "executive"],
            value="short",
        )
        summary_button = gr.Button("Summarize", variant="primary")
        summary_output = gr.Textbox(label="Summary", lines=8, interactive=False)
        summary_error = gr.Markdown("")

        def _resolve_model_id(model_label: str) -> tuple[str | None, str]:
            model_id = model_map.get(model_label)
            if not model_id:
                return None, "Invalid model selection."
            return model_id, ""

        def run_summary(text: str, summary_type_value: str, model_label: str) -> tuple[str, str]:
            model_id, err = _resolve_model_id(model_label)
            if err:
                return "", err
            try:
                result = summarize_document(
                    text,
                    summary_type=summary_type_value,  # type: ignore[arg-type]
                    model_hint=model_id,
                )
                return result, ""
            except TextTransformError as exc:
                return "", str(exc)

        summary_button.click(
            fn=run_summary,
            inputs=[summary_textbox, summary_type, model_dropdown],
            outputs=[summary_output, summary_error],
        )

    return summary_panel, summary_button


def create_keywords_panel(
    model_map: dict[str, str], model_dropdown: gr.Dropdown
) -> tuple[gr.Column, callable]:
    """Create the keyword extraction panel."""
    with gr.Column(visible=False) as keyword_panel:
        gr.Markdown("Extract the most relevant keywords for quick indexing.")
        keyword_textbox = gr.Textbox(
            label="Text to analyze",
            placeholder="Paste or write your text here…",
            lines=8,
        )
        keyword_slider = gr.Slider(
            label="Maximum keywords",
            minimum=3,
            maximum=30,
            step=1,
            value=10,
        )
        keyword_button = gr.Button("Extract keywords", variant="primary")
        keyword_output = gr.Textbox(label="Keywords (one per line)", lines=8, interactive=False)
        keyword_error = gr.Markdown("")

        def _resolve_model_id(model_label: str) -> tuple[str | None, str]:
            model_id = model_map.get(model_label)
            if not model_id:
                return None, "Invalid model selection."
            return model_id, ""

        def run_keywords(text: str, max_keywords: float, model_label: str) -> tuple[str, str]:
            model_id, err = _resolve_model_id(model_label)
            if err:
                return "", err
            try:
                keywords = extract_keywords(
                    text,
                    max_keywords=int(max_keywords),
                    model_hint=model_id,
                )
            except TextTransformError as exc:
                return "", str(exc)
            return "\n".join(keywords), ""

        keyword_button.click(
            fn=run_keywords,
            inputs=[keyword_textbox, keyword_slider, model_dropdown],
            outputs=[keyword_output, keyword_error],
        )

    return keyword_panel, keyword_button


def create_technical_panel(
    model_map: dict[str, str], model_dropdown: gr.Dropdown
) -> tuple[gr.Column, callable]:
    """Create the technical rewrite panel."""
    with gr.Column(visible=False) as technical_panel:
        gr.Markdown("Rewrite text with a more formal and technical tone.")
        technical_textbox = gr.Textbox(
            label="Text to rewrite",
            placeholder="Paste or write your text here…",
            lines=8,
        )
        domain_dropdown = gr.Dropdown(
            label="Domain (optional)",
            choices=["", "tech", "medical", "legal", "finance"],
            value="",
        )
        level_dropdown = gr.Dropdown(
            label="Target expertise level (optional)",
            choices=["", "intermediate", "advanced", "expert"],
            value="",
        )
        technical_button = gr.Button("Make technical", variant="primary")
        technical_output = gr.Textbox(label="Technical version", lines=8, interactive=False)
        technical_error = gr.Markdown("")

        def _resolve_model_id(model_label: str) -> tuple[str | None, str]:
            model_id = model_map.get(model_label)
            if not model_id:
                return None, "Invalid model selection."
            return model_id, ""

        def run_technical(
            text: str,
            domain_value: str,
            level_value: str,
            model_label: str,
        ) -> tuple[str, str]:
            model_id, err = _resolve_model_id(model_label)
            if err:
                return "", err
            domain_arg = domain_value or None
            level_arg = level_value or None
            try:
                result = make_text_more_technical(
                    text,
                    domain=domain_arg,
                    target_level=level_arg,
                    model_hint=model_id,
                )
            except TextTransformError as exc:
                return "", str(exc)
            return result, ""

        technical_button.click(
            fn=run_technical,
            inputs=[technical_textbox, domain_dropdown, level_dropdown, model_dropdown],
            outputs=[technical_output, technical_error],
        )

    return technical_panel, technical_button


def create_plain_panel(
    model_map: dict[str, str], model_dropdown: gr.Dropdown
) -> tuple[gr.Column, callable]:
    """Create the plain language simplification panel."""
    with gr.Column(visible=False) as plain_panel:
        gr.Markdown("Simplify complex passages into clear plain language.")
        plain_textbox = gr.Textbox(
            label="Text to simplify",
            placeholder="Paste or write your text here…",
            lines=8,
        )
        reading_level = gr.Dropdown(
            label="Target reading level (optional)",
            choices=["", "child", "teen", "adult_general"],
            value="",
        )
        plain_button = gr.Button("Simplify", variant="primary")
        plain_output = gr.Textbox(label="Plain-language version", lines=8, interactive=False)
        plain_error = gr.Markdown("")

        def _resolve_model_id(model_label: str) -> tuple[str | None, str]:
            model_id = model_map.get(model_label)
            if not model_id:
                return None, "Invalid model selection."
            return model_id, ""

        def run_plain(text: str, level_value: str, model_label: str) -> tuple[str, str]:
            model_id, err = _resolve_model_id(model_label)
            if err:
                return "", err
            target_level = level_value or None
            try:
                result = simplify_text(
                    text,
                    target_reading_level=target_level,
                    model_hint=model_id,
                )
            except TextTransformError as exc:
                return "", str(exc)
            return result, ""

        plain_button.click(
            fn=run_plain,
            inputs=[plain_textbox, reading_level, model_dropdown],
            outputs=[plain_output, plain_error],
        )

    return plain_panel, plain_button


def create_image_panel(
    vision_model_map: dict[str, str], vision_model_dropdown: gr.Dropdown
) -> tuple[gr.Column, callable]:
    """Create the image description panel."""
    with gr.Column(visible=False) as image_panel:
        gr.Markdown("Generate detailed descriptions of images using AI vision models.")
        image_upload = gr.Image(
            label="Upload image",
            type="filepath",
            height=400,
        )
        image_detail_level = gr.Radio(
            label="Detail level",
            choices=["short", "detailed"],
            value="short",
        )
        image_max_size = gr.Dropdown(
            label="Max image size (longest side)",
            choices=["128", "256", "512", "1024"],
            value="512",
            info="Larger sizes provide more detail but use more tokens",
        )
        image_button = gr.Button("Describe image", variant="primary")
        image_output = gr.Textbox(label="Description", lines=8, interactive=False)
        image_error = gr.Markdown("")

        def _resolve_vision_model_id(model_label: str) -> tuple[str | None, str]:
            model_id = vision_model_map.get(model_label)
            if not model_id:
                return None, "Invalid vision model selection."
            return model_id, ""

        def run_image_description(
            image_path: str | None,
            detail_level: str,
            max_size_str: str,
            model_label: str,
        ) -> tuple[str, str]:
            if not image_path:
                return "", "Please upload an image."
            model_id, err = _resolve_vision_model_id(model_label)
            if err:
                return "", err
            try:
                max_size = int(max_size_str)
                # Read image file as bytes
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                result = describe_image(
                    image_bytes,
                    detail_level=detail_level,  # type: ignore[arg-type]
                    max_size=max_size,
                    model_hint=model_id,
                )
                return result, ""
            except ImageDescriptionError as exc:
                return "", str(exc)
            except Exception as exc:  # noqa: BLE001
                return "", f"Error: {exc}"

        image_button.click(
            fn=run_image_description,
            inputs=[image_upload, image_detail_level, image_max_size, vision_model_dropdown],
            outputs=[image_output, image_error],
        )

    return image_panel, image_button
