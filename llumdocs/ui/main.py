"""Gradio UI for the initial LlumDocs experience."""

from __future__ import annotations

import gradio as gr

from llumdocs.llm import available_models, available_vision_models
from llumdocs.ui.components import (
    LANGUAGE_OPTIONS,
    create_email_intelligence_panel,
    create_image_panel,
    create_keywords_panel,
    create_plain_panel,
    create_summary_panel,
    create_technical_panel,
    create_translation_panel,
)
from llumdocs.ui.layout import (
    FEATURE_BUTTON_CSS,
    FEATURES,
    create_feature_sidebar,
    create_panel_switcher,
)


def create_interface() -> gr.Blocks:
    """Create and return the Gradio interface for LlumDocs."""
    model_choices = available_models()
    model_map = dict(model_choices)

    vision_model_choices = available_vision_models()
    vision_model_map = dict(vision_model_choices)

    source_map = {label: code for label, code in LANGUAGE_OPTIONS}
    default_feature = next(
        (feature["label"] for feature in FEATURES if feature["available"]), FEATURES[0]["label"]
    )

    with gr.Blocks(title="LlumDocs", theme=gr.themes.Soft(), css=FEATURE_BUTTON_CSS) as demo:
        gr.Markdown(
            """
            # 🌟 LlumDocs
            Smart document transformations powered by LLMs.
            Available today: translation, summaries, keyword extraction, rewrites,
            and email intelligence.
            """
        )

        with gr.Row():
            # Left sidebar with feature buttons
            with gr.Column(scale=1):
                # Feature buttons (utilities roadmap)
                feature_button_refs = create_feature_sidebar(default_feature)

                if not model_choices and not vision_model_choices:
                    gr.Markdown(
                        "⚠️ No models detected. Configure Ollama locally or set "
                        "`OPENAI_API_KEY` before using the tools.",
                        elem_classes=["warning"],
                    )

            # Right panel with feature-specific interfaces
            with gr.Column(scale=3):
                panel_map: dict[str, gr.Column] = {}

                # Translation panel
                translate_panel, _ = create_translation_panel(model_map, source_map, model_choices)
                panel_map["Translate text"] = translate_panel

                # Summary panel
                summary_panel, _ = create_summary_panel(model_map, model_choices)
                panel_map["Document summaries"] = summary_panel

                # Keywords panel (no model dropdown - uses default)
                keyword_panel, _ = create_keywords_panel(model_map, model_choices)
                panel_map["Keyword extraction"] = keyword_panel

                # Technical panel
                technical_panel, _ = create_technical_panel(model_map, model_choices)
                panel_map["Make text more technical"] = technical_panel

                # Plain language panel
                plain_panel, _ = create_plain_panel(model_map, model_choices)
                panel_map["Simplify text (plain language)"] = plain_panel

                # Image description panel
                image_panel, _ = create_image_panel(vision_model_map, vision_model_choices)
                panel_map["Image description"] = image_panel

                # Email intelligence panel
                email_panel, _ = create_email_intelligence_panel()
                panel_map["Email intelligence"] = email_panel

        # Wire up panel switching
        switch_panel, panel_outputs, button_outputs, clickable_buttons = create_panel_switcher(
            panel_map, feature_button_refs
        )

        for label, button, available, _elem_id in feature_button_refs:
            if available and label in panel_map:
                button.click(
                    fn=lambda lab=label: switch_panel(lab),
                    inputs=None,
                    outputs=panel_outputs + button_outputs,
                )

    return demo


def main() -> None:
    """CLI entrypoint for running the LlumDocs Gradio UI."""
    import os

    demo = create_interface()
    share = os.getenv("LLUMDOCS_UI_SHARE", "false").lower() in ("true", "1", "yes")
    server_name = os.getenv("LLUMDOCS_UI_HOST", "0.0.0.0")
    server_port = int(os.getenv("LLUMDOCS_UI_PORT", "7860"))
    demo.launch(share=share, server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    main()
