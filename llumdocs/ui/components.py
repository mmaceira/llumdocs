"""UI component builders for LlumDocs Gradio interface."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.llm import LLMConfigurationError
from llumdocs.services import (
    DEFAULT_EMAIL_ROUTING_LABELS,
    EMAIL_INTEL_AVAILABLE,
    EmailIntelligenceError,
    EmailIntelligenceService,
)
from llumdocs.services.image_description_service import ImageDescriptionError, describe_image
from llumdocs.services.text_transform_service import (
    CALM_PROFESSIONAL,
    SERIOUS_IMPORTANT,
    TextTransformError,
    apply_company_tone,
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
)
from llumdocs.services.translation_service import TranslationError, translate_text
from llumdocs.ui.error_messages import format_error_message

LANGUAGE_OPTIONS = [
    ("Auto detect (Catalan/Spanish/English)", "auto"),
    ("Catalan", "ca"),
    ("Spanish", "es"),
    ("English", "en"),
]


def _resolve_model_id(
    model_label: str | None,
    model_map: dict[str, str],
) -> tuple[str | None, str]:
    """
    Map a human-friendly dropdown label to an actual LiteLLM model id.

    Returns:
        (model_id, error_message)
        - model_id: resolved id or None if not found
        - error_message: empty string if ok, otherwise human-readable explanation
    """
    if not model_label:
        return None, "No model selected. Please choose a model from the dropdown."
    model_id = model_map.get(model_label)
    if not model_id:
        return None, f"Unknown model label: {model_label!r}."
    return model_id, ""


def create_error_display() -> gr.Markdown:
    """Create a consistent error display component for panels.

    Returns:
        A Markdown component configured for error display with consistent styling.
    """
    return gr.Markdown("", elem_id="error-display", elem_classes=["error-display"])


def create_processing_status() -> gr.Markdown:
    """Create a processing status message component.

    Returns:
        A Markdown component for displaying processing status with elapsed time.
    """
    return gr.Markdown(
        "", elem_id="processing-status", elem_classes=["processing-status"], visible=True
    )


def create_model_dropdown(
    model_choices: list[tuple[str, str]], vision_model_choices: list[tuple[str, str]]
) -> tuple[gr.Dropdown, gr.Dropdown]:
    """Create model selection dropdowns for text and vision models.

    DEPRECATED: Use create_llm_dropdown and create_vision_dropdown instead.
    """
    model_labels = [label for label, _ in model_choices] or ["No providers available"]
    vision_model_labels = [label for label, _ in vision_model_choices] or ["No providers available"]

    model_dropdown = gr.Dropdown(
        label="Select provider",
        choices=model_labels,
        value=model_labels[0],
        interactive=bool(model_choices),
        elem_id="model-dropdown",
    )

    vision_model_dropdown = gr.Dropdown(
        label="Vision model",
        choices=vision_model_labels,
        value=vision_model_labels[0] if vision_model_labels else None,
        interactive=bool(vision_model_choices),
        elem_id="vision-model-dropdown",
    )

    return model_dropdown, vision_model_dropdown


def create_llm_dropdown(model_choices: list[tuple[str, str]]) -> gr.Dropdown:
    """Create a single LLM model selection dropdown."""
    model_labels = [label for label, _ in model_choices] or ["No providers available"]
    return gr.Dropdown(
        label="LLM provider",
        choices=model_labels,
        value=model_labels[0] if model_labels else None,
        interactive=bool(model_choices),
        elem_id="llm-provider-dropdown",
    )


def create_vision_dropdown(vision_model_choices: list[tuple[str, str]]) -> gr.Dropdown:
    """Create a single vision model selection dropdown."""
    vision_model_labels = [label for label, _ in vision_model_choices] or ["No providers available"]
    return gr.Dropdown(
        label="Vision model",
        choices=vision_model_labels,
        value=vision_model_labels[0] if vision_model_labels else None,
        interactive=bool(vision_model_choices),
        elem_id="vision-model-dropdown",
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
            choices=[option for option, code in LANGUAGE_OPTIONS if code != "auto"],
            value="Catalan",
            elem_id="target-language-dropdown",
        )
        translate_button = gr.Button("Translate", variant="primary")
        translation_status = create_processing_status()
        translation_output = gr.Textbox(
            label="Translated text", lines=8, interactive=False, elem_id="translation-output"
        )
        translation_error = create_error_display()

        def run_translation(
            text: str,
            source_label: str,
            target_label: str,
            model_label: str,
        ) -> tuple[str, str, str]:
            start_time = time.time()
            source_code = source_map[source_label]
            target_code = source_map[target_label]
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", ""
            try:
                translated = translate_text(
                    text,
                    source_lang=source_code,
                    target_lang=target_code,
                    model_hint=model_id,
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return translated, status_msg, ""
            except (TranslationError, LLMConfigurationError) as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        translate_button.click(
            fn=run_translation,
            inputs=[translate_textbox, source_dropdown, target_dropdown, model_dropdown],
            outputs=[translation_output, translation_status, translation_error],
        )

    return translate_panel, translate_button


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
        )

    return summary_panel, summary_button


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
                    text,
                    max_keywords=int(max_keywords),
                    model_hint=model_id,
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return "\n".join(keywords), status_msg, ""
            except TextTransformError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        keyword_button.click(
            fn=run_keywords,
            inputs=[keyword_textbox, keyword_slider, model_dropdown],
            outputs=[keyword_output, keyword_status, keyword_error],
        )

    return keyword_panel, keyword_button


def create_technical_panel(
    model_map: dict[str, str], model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the technical rewrite panel."""
    with gr.Column(visible=False) as technical_panel:
        gr.Markdown("Rewrite text with a more formal and technical tone.")
        model_dropdown = create_llm_dropdown(model_choices)
        technical_textbox = gr.Textbox(
            label="Text to rewrite",
            placeholder="Paste or write your text here…",
            lines=8,
            elem_id="technical-textbox",
        )
        domain_dropdown = gr.Dropdown(
            label="Domain (optional)",
            choices=["", "tech", "medical", "legal", "finance"],
            value="",
            elem_id="domain-dropdown",
        )
        level_dropdown = gr.Dropdown(
            label="Target expertise level (optional)",
            choices=["", "intermediate", "advanced", "expert"],
            value="",
            elem_id="expertise-level-dropdown",
        )
        technical_button = gr.Button("Make technical", variant="primary")
        technical_status = create_processing_status()
        technical_output = gr.Textbox(
            label="Technical version", lines=8, interactive=False, elem_id="technical-output"
        )
        technical_error = create_error_display()

        def run_technical(
            text: str,
            domain_value: str,
            level_value: str,
            model_label: str,
        ) -> tuple[str, str, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", ""
            domain_arg = domain_value or None
            level_arg = level_value or None
            try:
                result = make_text_more_technical(
                    text,
                    domain=domain_arg,
                    target_level=level_arg,
                    model_hint=model_id,
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except TextTransformError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        technical_button.click(
            fn=run_technical,
            inputs=[technical_textbox, domain_dropdown, level_dropdown, model_dropdown],
            outputs=[technical_output, technical_status, technical_error],
        )

    return technical_panel, technical_button


def create_plain_panel(
    model_map: dict[str, str], model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the plain language simplification panel."""
    with gr.Column(visible=False) as plain_panel:
        gr.Markdown("Simplify complex passages into clear plain language.")
        model_dropdown = create_llm_dropdown(model_choices)
        plain_textbox = gr.Textbox(
            label="Text to simplify",
            placeholder="Paste or write your text here…",
            lines=8,
            elem_id="plain-textbox",
        )
        reading_level = gr.Dropdown(
            label="Target reading level (optional)",
            choices=["", "child", "teen", "adult_general"],
            value="",
            elem_id="reading-level-dropdown",
        )
        plain_button = gr.Button("Simplify", variant="primary")
        plain_status = create_processing_status()
        plain_output = gr.Textbox(
            label="Plain-language version", lines=8, interactive=False, elem_id="plain-output"
        )
        plain_error = create_error_display()

        def run_plain(text: str, level_value: str, model_label: str) -> tuple[str, str, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", ""
            target_level = level_value or None
            try:
                result = simplify_text(
                    text,
                    target_reading_level=target_level,
                    model_hint=model_id,
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except TextTransformError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        plain_button.click(
            fn=run_plain,
            inputs=[plain_textbox, reading_level, model_dropdown],
            outputs=[plain_output, plain_status, plain_error],
        )

    return plain_panel, plain_button


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

        # Text input
        transform_textbox = gr.Textbox(
            label="Text to transform",
            placeholder="Paste or write your text here…",
            lines=8,
            elem_id="transform-textbox",
        )
        transform_textbox_language_note = gr.Markdown(
            "",
            visible=False,
            elem_id="transform-textbox-language-note",
        )

        # Conditional fields for technical transformation
        domain_dropdown = gr.Dropdown(
            label="Domain (optional)",
            choices=["", "tech", "medical", "legal", "finance"],
            value="",
            visible=True,  # Visible by default since "Make text more technical" is the default
            elem_id="domain-dropdown",
        )
        level_dropdown = gr.Dropdown(
            label="Target expertise level (optional)",
            choices=["", "intermediate", "advanced", "expert"],
            value="",
            visible=True,  # Visible by default since "Make text more technical" is the default
            elem_id="expertise-level-dropdown",
        )

        # Conditional field for simplify transformation
        reading_level = gr.Dropdown(
            label="Target reading level (optional)",
            choices=["", "child", "teen", "adult_general"],
            value="",
            visible=False,
            elem_id="reading-level-dropdown",
        )

        transform_button = gr.Button("Transform", variant="primary")
        transform_status = create_processing_status()
        transform_output = gr.Textbox(
            label="Transformed text",
            lines=12,
            interactive=False,
            elem_id="transform-output",
            placeholder="The transformed text or complete email will appear here...",
        )
        transform_output_language = gr.Markdown(
            "",
            visible=True,
            elem_id="transform-output-language",
        )
        transform_error = create_error_display()

        def update_ui_visibility(
            transform_type_value: str,
        ) -> tuple[dict, dict, dict, dict, dict, dict, dict]:
            """Update visibility of conditional fields based on transformation type."""
            if transform_type_value == "Make text more technical":
                return (
                    gr.update(visible=False),  # company_tone_type
                    gr.update(visible=False),  # company_tone_language
                    gr.update(visible=False),  # company_tone_note
                    gr.update(visible=False),  # transform_textbox_language_note
                    gr.update(visible=True),  # domain_dropdown
                    gr.update(visible=True),  # level_dropdown
                    gr.update(visible=False),  # reading_level
                )
            elif transform_type_value == "Simplify text":
                return (
                    gr.update(visible=False),  # company_tone_type
                    gr.update(visible=False),  # company_tone_language
                    gr.update(visible=False),  # company_tone_note
                    gr.update(visible=False),  # transform_textbox_language_note
                    gr.update(visible=False),  # domain_dropdown
                    gr.update(visible=False),  # level_dropdown
                    gr.update(visible=True),  # reading_level
                )
            else:  # Company tone
                return (
                    gr.update(visible=True),  # company_tone_type
                    gr.update(visible=True),  # company_tone_language
                    gr.update(visible=True),  # company_tone_note
                    gr.update(
                        visible=True
                    ),  # transform_textbox_language_note (will be updated by language change)
                    gr.update(visible=False),  # domain_dropdown
                    gr.update(visible=False),  # level_dropdown
                    gr.update(visible=False),  # reading_level
                )

        def update_language_note(transform_type_value: str, selected_language: str) -> dict:
            """Update the language note when language changes."""
            if transform_type_value == "Give text a tone aligned with the company":
                language_map = {"ca": "Catalan", "es": "Spanish", "en": "English"}
                language_label = language_map.get(selected_language, "English")
                return gr.update(visible=True, value=f"*Input text language: {language_label}*")
            return gr.update(visible=False, value="")

        transform_type.change(
            fn=update_ui_visibility,
            inputs=[transform_type],
            outputs=[
                company_tone_type,
                company_tone_language,
                company_tone_note,
                transform_textbox_language_note,
                domain_dropdown,
                level_dropdown,
                reading_level,
            ],
        ).then(
            fn=update_language_note,
            inputs=[transform_type, company_tone_language],
            outputs=[transform_textbox_language_note],
        )

        company_tone_language.change(
            fn=update_language_note,
            inputs=[transform_type, company_tone_language],
            outputs=[transform_textbox_language_note],
        )

        def run_transformation(
            text: str,
            transform_type_value: str,
            company_tone_value: str,
            company_tone_lang: str,
            domain_value: str,
            level_value: str,
            reading_level_value: str,
            model_label: str,
        ) -> tuple[str, str, str, str]:
            start_time = time.time()
            model_id, err = _resolve_model_id(model_label, model_map)
            if err:
                return "", "", "", ""

            language_note = ""

            try:
                if transform_type_value == "Make text more technical":
                    domain_arg = domain_value or None
                    level_arg = level_value or None
                    result = make_text_more_technical(
                        text,
                        domain=domain_arg,
                        target_level=level_arg,
                        model_hint=model_id,
                    )
                    language_note = ""  # No language note for technical transformation
                elif transform_type_value == "Simplify text":
                    target_level = reading_level_value or None
                    result = simplify_text(
                        text,
                        target_reading_level=target_level,
                        model_hint=model_id,
                    )
                    language_note = ""  # No language note for simplify transformation
                else:  # Company tone
                    if company_tone_value == "Company serious, important mail":
                        tone_type = SERIOUS_IMPORTANT
                    else:  # "Company with calm tone, professional but casual"
                        tone_type = CALM_PROFESSIONAL

                    # Get language label
                    language_map = {"ca": "Catalan", "es": "Spanish", "en": "English"}
                    language_label = language_map.get(company_tone_lang, "English")
                    language_note = f"**Email language:** {language_label}"

                    result = apply_company_tone(
                        text,
                        tone_type=tone_type,
                        language=company_tone_lang,  # type: ignore[arg-type]
                        model_hint=model_id,
                    )

                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, "", language_note
            except TextTransformError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc), ""
            except Exception as exc:  # noqa: BLE001
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc), ""

        transform_button.click(
            fn=run_transformation,
            inputs=[
                transform_textbox,
                transform_type,
                company_tone_type,
                company_tone_language,
                domain_dropdown,
                level_dropdown,
                reading_level,
                model_dropdown,
            ],
            outputs=[
                transform_output,
                transform_status,
                transform_error,
                transform_output_language,
            ],
        )

    return transform_panel, transform_button


def create_image_panel(
    vision_model_map: dict[str, str], vision_model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the image description panel."""
    with gr.Column(visible=False) as image_panel:
        gr.Markdown("Generate detailed descriptions of images using AI vision models.")
        vision_model_dropdown = create_vision_dropdown(vision_model_choices)
        # Show which model is selected (will be updated dynamically)
        default_vision_model_label = vision_model_choices[0][0] if vision_model_choices else None
        if default_vision_model_label:
            gr.Markdown(f"Using model: **{default_vision_model_label}**")
        image_upload = gr.Image(
            label="Upload image",
            type="filepath",
            height=400,
            elem_id="image-upload",
        )
        image_detail_level = gr.Radio(
            label="Detail level",
            choices=["short", "detailed"],
            value="short",
        )
        image_max_size = gr.Dropdown(
            label="Max image size (longest side)",
            choices=["128", "256", "512", "1024"],
            value="128",
            info="Larger sizes provide more detail but use more tokens",
            elem_id="image-max-size-dropdown",
        )
        image_button = gr.Button("Describe image", variant="primary")
        image_status = create_processing_status()
        image_output = gr.Textbox(
            label="Description", lines=8, interactive=False, elem_id="image-output"
        )
        image_error = create_error_display()

        def run_image_description(
            image_path: str | None,
            detail_level: str,
            max_size_str: str,
            model_label: str,
        ) -> tuple[str, str, str]:
            start_time = time.time()
            if not image_path:
                return (
                    "",
                    "",
                    format_error_message(
                        ValueError("Please upload an image."), "Please upload an image."
                    ),
                )
            model_id, err = _resolve_model_id(model_label, vision_model_map)
            if err:
                return "", "", ""
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
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except ImageDescriptionError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)
            except Exception as exc:  # noqa: BLE001
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        image_button.click(
            fn=run_image_description,
            inputs=[image_upload, image_detail_level, image_max_size, vision_model_dropdown],
            outputs=[image_output, image_status, image_error],
        )

    return image_panel, image_button


def create_email_intelligence_panel() -> tuple[gr.Column, callable]:
    """Create the email routing + phishing + sentiment panel."""
    with gr.Column(visible=False) as email_panel:
        gr.Markdown(
            "Analyze multilingual emails to route them, flag phishing, and capture sentiment."
        )
        routing_labels = (
            DEFAULT_EMAIL_ROUTING_LABELS
            if DEFAULT_EMAIL_ROUTING_LABELS
            else ["support", "billing", "sales", "HR", "IT incident"]
        )
        gr.Markdown(
            f"**Routing categories:** {', '.join(routing_labels)}",
            elem_classes=["caption"],
        )
        gr.Markdown("Using Hugging Face models for email intelligence.")
        message_text = gr.Textbox(
            label="Email or ticket content",
            placeholder="Bon dia, tinc un problema amb la factura de novembre…",
            lines=8,
            elem_id="email-message-textbox",
        )
        allow_multi = gr.Checkbox(
            label="Allow multiple labels per message",
            value=True,
        )
        template_text = gr.Textbox(
            label="Hypothesis template (optional)",
            placeholder="This message is about {}.",
            elem_id="email-template-textbox",
        )
        analyze_button = gr.Button("Analyze email", variant="primary")
        email_status = create_processing_status()
        classification_output = gr.Markdown(label="Classification", elem_id="classification-output")
        phishing_output = gr.Markdown(label="Phishing detection", elem_id="phishing-output")
        sentiment_output = gr.Markdown(label="Sentiment analysis", elem_id="sentiment-output")
        email_error = create_error_display()

        def run_email_analysis(
            text: str,
            multi_label_enabled: bool,
            template_value: str,
        ) -> tuple[str, str, str, str, str]:
            start_time = time.time()
            if not EMAIL_INTEL_AVAILABLE or EmailIntelligenceService is None:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return (
                    "",
                    "",
                    "",
                    "",
                    format_error_message(
                        EmailIntelligenceError(
                            "Email intelligence is not available. "
                            "Install the [email] extra: pip install 'llumdocs[email]'"
                        )
                    ),
                )
            template_arg = template_value.strip() or None
            routing_labels = (
                DEFAULT_EMAIL_ROUTING_LABELS
                if DEFAULT_EMAIL_ROUTING_LABELS
                else ["support", "billing", "sales", "HR", "IT incident"]
            )
            try:
                service = EmailIntelligenceService(
                    routing_labels,
                    multi_label=multi_label_enabled,
                    hypothesis_template=template_arg,
                )
                insights = service.analyze_email(text)
            except EmailIntelligenceError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", "", "", status_msg, format_error_message(exc)

            # Format classification output - sorted by score (highest first)
            classification_items = list(
                zip(
                    insights.classification.labels,
                    insights.classification.scores,
                    strict=False,
                )
            )
            classification_items.sort(key=lambda x: x[1], reverse=True)

            classification_lines = [
                "### 📋 Email Categorization",
                "",
                (
                    "This analysis categorizes the email into predefined routing categories "
                    "to help direct it to the appropriate department or team."
                ),
                "",
            ]
            for label, score in classification_items:
                percentage = score * 100
                classification_lines.append(f"- **{label}**: {percentage:.2f}% ({score:.4f})")
            if not classification_items:
                classification_lines.append("No classifications found.")
            classification_text = "\n".join(classification_lines)

            # Format phishing output
            phishing_label = insights.phishing.label
            phishing_score = insights.phishing.score
            phishing_percentage = phishing_score * 100

            # Extract aggregated scores (safe/phishing) and individual label scores
            aggregated_scores = {}
            individual_scores = {}
            for label, score in insights.phishing.scores_by_label.items():
                if label in ("safe", "phishing"):
                    aggregated_scores[label] = score
                elif score > 0.0001 and not label.startswith("class_"):
                    individual_scores[label] = score

            phishing_lines = [
                "### 🛡️ Spam & Phishing Detection",
                "",
                (
                    "This analysis detects whether the email is safe or potentially "
                    "a phishing attempt or spam message."
                ),
                "",
                f"**Result:** {phishing_label} ({phishing_percentage:.2f}%)",
            ]

            # Show aggregated scores if available
            if aggregated_scores:
                phishing_lines.append("\n**Category scores:**")
                for label in ["safe", "phishing"]:
                    if label in aggregated_scores:
                        score = aggregated_scores[label]
                        pct = score * 100
                        phishing_lines.append(f"- {label}: {pct:.2f}% ({score:.4f})")

            # Show all individual label scores (the 4 model categories)
            if individual_scores:
                phishing_lines.append("\n**Individual category scores:**")
                phishing_lines.append(
                    "*(Note: Category names reference training data structure and don't "
                    "necessarily indicate URL detection)*"
                )
                # Show in a consistent order: legitimate_email, phishing_url,
                # legitimate_url, phishing_url_alt
                label_order = [
                    "legitimate_email",
                    "phishing_url",
                    "legitimate_url",
                    "phishing_url_alt",
                ]
                for label in label_order:
                    if label in individual_scores:
                        score = individual_scores[label]
                        pct = score * 100
                        # Make labels more readable
                        readable_label = label.replace("_", " ").title()
                        phishing_lines.append(f"- {readable_label}: {pct:.2f}% ({score:.4f})")
                # Also show any other labels that might exist
                for label, score in sorted(
                    individual_scores.items(), key=lambda x: x[1], reverse=True
                ):
                    if label not in label_order:
                        pct = score * 100
                        readable_label = label.replace("_", " ").title()
                        phishing_lines.append(f"- {readable_label}: {pct:.2f}% ({score:.4f})")

            phishing_text = "\n".join(phishing_lines)

            # Format sentiment output
            sentiment_lines = [
                "### 😊 Sentiment Analysis",
                "",
                (
                    "This analysis determines the emotional tone of the email, "
                    "classifying it as positive, neutral, or negative."
                ),
                "",
            ]

            # Show all sentiment categories with their scores
            if insights.sentiment.scores_by_label:
                # Sort by score descending
                sorted_scores = sorted(
                    insights.sentiment.scores_by_label.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                for label, score in sorted_scores:
                    percentage = score * 100
                    sentiment_lines.append(f"- **{label.capitalize()}**: {percentage:.2f}%")
            else:
                # Fallback to old format if scores_by_label is not available
                sentiment_label = insights.sentiment.label
                sentiment_percentage = insights.sentiment.score * 100
                sentiment_lines.append(
                    f"**{sentiment_label.capitalize()}** ({sentiment_percentage:.2f}%)"
                )

            sentiment_text = "\n".join(sentiment_lines)

            elapsed = time.time() - start_time
            status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
            return classification_text, phishing_text, sentiment_text, status_msg, ""

        analyze_button.click(
            fn=run_email_analysis,
            inputs=[message_text, allow_multi, template_text],
            outputs=[
                classification_output,
                phishing_output,
                sentiment_output,
                email_status,
                email_error,
            ],
        )

    return email_panel, analyze_button
