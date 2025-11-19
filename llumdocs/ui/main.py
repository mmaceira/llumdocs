"""Gradio UI for the initial LlumDocs experience."""

from __future__ import annotations

import gradio as gr

from llumdocs.llm import LLMConfigurationError, available_models, available_vision_models
from llumdocs.services.image_description_service import (
    ImageDescriptionError,
    describe_image,
)
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

FEATURES = [
    {"label": "Translate text", "available": True, "description": "Catalan ⇄ Spanish ⇄ English"},
    {"label": "Make text more technical", "available": True, "description": "Formal rewrite"},
    {
        "label": "Simplify text (plain language)",
        "available": True,
        "description": "Plain-language rewrite",
    },
    {
        "label": "Document summaries",
        "available": True,
        "description": "Short, detailed, or executive",
    },
    {"label": "Keyword extraction", "available": True, "description": "Top key concepts"},
    {"label": "Image description", "available": True, "description": "Describe images with AI"},
    {"label": "Invoice data extraction", "available": False, "description": "Coming soon"},
    {"label": "Document classification", "available": False, "description": "Coming soon"},
]


FEATURE_BUTTON_CSS = """
/* Base styles for all feature buttons */
.feature-button {
    width: 100%;
    text-align: left;
    border-radius: 0.75rem;
    padding: 0.95rem 1.1rem;
    font-weight: 600;
    border: none;
    transition: background 0.2s ease;
    white-space: normal;
}

/* Available → BLUE */
.feature-button.feature-available {
    background: #6c63ff !important;
    color: #fff !important;
}

/* Selected → GREEN */
.feature-button.feature-active {
    background: #1fb978 !important;
    color: #fff !important;
    font-weight: 700;
}

/* Disabled → GREY */
.feature-button.feature-disabled {
    background: #e7e7e7 !important;
    color: #9a9a9a !important;
}

/* Grey description text */
.feature-description {
    margin-top: -0.35rem;
    margin-bottom: 1rem;
    font-style: italic;
    color: #6f6f6f;
}
"""


def _translate(
    text: str, source_lang: str, target_lang: str, model_id: str | None
) -> tuple[str, str]:
    try:
        translated = translate_text(
            text,
            source_lang=source_lang,
            target_lang=target_lang,
            model_hint=model_id,
        )
        return translated, ""
    except TranslationError as exc:
        return "", str(exc)
    except LLMConfigurationError as exc:
        return "", str(exc)


def create_interface() -> gr.Blocks:
    model_choices = available_models()
    model_labels = [label for label, _ in model_choices] or ["No providers available"]
    model_map = dict(model_choices)

    vision_model_choices = available_vision_models()
    vision_model_labels = [label for label, _ in vision_model_choices] or ["No providers available"]
    vision_model_map = dict(vision_model_choices)

    source_map = {label: code for label, code in LANGUAGE_OPTIONS}
    default_feature = next(
        (feature["label"] for feature in FEATURES if feature["available"]), FEATURES[0]["label"]
    )
    feature_button_refs: list[tuple[str, gr.Button, bool, str]] = []

    def _resolve_model_id(model_label: str) -> tuple[str | None, str]:
        if not model_choices:
            return None, "No LLM providers configured. Set up Ollama or OpenAI."
        model_id = model_map.get(model_label)
        if not model_id:
            return None, "Invalid model selection."
        return model_id, ""

    def _resolve_vision_model_id(model_label: str) -> tuple[str | None, str]:
        if not vision_model_choices:
            return None, "No vision LLM providers configured. Set up Ollama or OpenAI."
        model_id = vision_model_map.get(model_label)
        if not model_id:
            return None, "Invalid vision model selection."
        return model_id, ""

    with gr.Blocks(title="LlumDocs", theme=gr.themes.Soft(), css=FEATURE_BUTTON_CSS) as demo:
        gr.Markdown(
            """
            # 🌟 LlumDocs
            Smart document transformations powered by LLMs.
            Available today: translation, summaries, keyword extraction, and bilingual rewrites.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### LLM provider")
                if not model_choices:
                    gr.Markdown(
                        "⚠️ No models detected. Configure Ollama locally or set "
                        "`OPENAI_API_KEY` before using the tools.",
                        elem_classes=["warning"],
                    )

                model_dropdown = gr.Dropdown(
                    label="Select provider",
                    choices=model_labels,
                    value=model_labels[0],
                    interactive=bool(model_choices),
                )

                gr.Markdown("### Utilities roadmap")
                for idx, feature in enumerate(FEATURES):
                    if feature["available"]:
                        if feature["label"] == default_feature:
                            classes = ["feature-button", "feature-active"]
                        else:
                            classes = ["feature-button", "feature-available"]
                    else:
                        classes = ["feature-button", "feature-disabled"]
                    elem_id = f"feature-btn-{idx}"
                    btn = gr.Button(
                        feature["label"],
                        interactive=feature["available"],
                        elem_classes=classes,
                        elem_id=elem_id,
                    )
                    gr.Markdown(f"*{feature['description']}*", elem_classes=["feature-description"])
                    feature_button_refs.append(
                        (feature["label"], btn, feature["available"], elem_id)
                    )

            with gr.Column(scale=3):
                panel_map: dict[str, gr.Column] = {}

                with gr.Column(visible=True) as translate_panel:
                    gr.Markdown(
                        "Translate text between Catalan, Spanish, and English "
                        "while preserving tone."
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
                    translation_output = gr.Textbox(
                        label="Translated text", lines=8, interactive=False
                    )
                    translation_error = gr.Markdown("")

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
                        return _translate(text, source_code, target_code, model_id)

                    translate_button.click(
                        fn=run_translation,
                        inputs=[
                            translate_textbox,
                            source_dropdown,
                            target_dropdown,
                            model_dropdown,
                        ],
                        outputs=[translation_output, translation_error],
                    )

                panel_map["Translate text"] = translate_panel

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

                    def run_summary(
                        text: str, summary_type_value: str, model_label: str
                    ) -> tuple[str, str]:
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

                panel_map["Document summaries"] = summary_panel

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
                    keyword_output = gr.Textbox(
                        label="Keywords (one per line)", lines=8, interactive=False
                    )
                    keyword_error = gr.Markdown("")

                    def run_keywords(
                        text: str, max_keywords: float, model_label: str
                    ) -> tuple[str, str]:
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

                panel_map["Keyword extraction"] = keyword_panel

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
                    technical_output = gr.Textbox(
                        label="Technical version", lines=8, interactive=False
                    )
                    technical_error = gr.Markdown("")

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

                panel_map["Make text more technical"] = technical_panel

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
                    plain_output = gr.Textbox(
                        label="Plain-language version", lines=8, interactive=False
                    )
                    plain_error = gr.Markdown("")

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

                panel_map["Simplify text (plain language)"] = plain_panel

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
                    vision_model_dropdown = gr.Dropdown(
                        label="Vision model",
                        choices=vision_model_labels,
                        value=vision_model_labels[0] if vision_model_labels else None,
                        interactive=bool(vision_model_choices),
                    )
                    image_button = gr.Button("Describe image", variant="primary")
                    image_output = gr.Textbox(label="Description", lines=8, interactive=False)
                    image_error = gr.Markdown("")

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
                        inputs=[
                            image_upload,
                            image_detail_level,
                            image_max_size,
                            vision_model_dropdown,
                        ],
                        outputs=[image_output, image_error],
                    )

                panel_map["Image description"] = image_panel

        panel_labels = list(panel_map.keys())
        panel_outputs = [panel_map[label] for label in panel_labels]

        clickable_buttons = [
            (label, btn)
            for label, btn, available, _ in feature_button_refs
            if available and label in panel_map
        ]

        button_outputs = [btn for _, btn in clickable_buttons]

        def switch_panel(target_label: str):
            panel_updates = [
                gr.update(visible=(label_name == target_label)) for label_name in panel_labels
            ]

            button_updates = []
            for label_name, _ in clickable_buttons:
                if label_name == target_label:
                    button_updates.append(
                        gr.update(elem_classes=["feature-button", "feature-active"])
                    )
                else:
                    button_updates.append(
                        gr.update(elem_classes=["feature-button", "feature-available"])
                    )

            return panel_updates + button_updates

        for label, button, available, _elem_id in feature_button_refs:
            if available and label in panel_map:
                button.click(
                    fn=lambda lab=label: switch_panel(lab),
                    inputs=None,
                    outputs=panel_outputs + button_outputs,
                )

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
