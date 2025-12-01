"""Gradio UI for the initial LlumDocs experience."""

from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
# This makes development usage consistent with Docker, where env_file is used
load_dotenv()

from llumdocs.llm import available_models, available_vision_models  # noqa: E402
from llumdocs.ui.components import (  # noqa: E402
    LANGUAGE_OPTIONS,
    create_document_extraction_panel,
    create_email_intelligence_panel,
    create_image_panel,
    create_keywords_panel,
    create_summary_panel,
    create_text_transformation_panel,
    create_translation_panel,
)
from llumdocs.ui.layout import (  # noqa: E402
    FEATURE_BUTTON_CSS,
    FEATURES,
    create_panel_switcher,
)


def _check_email_intelligence_available() -> bool:
    """Check if email intelligence dependencies are available."""
    try:
        # Try importing the service - if this succeeds, email intelligence is available
        from llumdocs.services import EmailIntelligenceService  # noqa: F401

        # Also check if torch is available (required dependency)
        try:
            import torch  # noqa: F401

            return True
        except ImportError:
            return False
    except ImportError:
        return False


def create_interface() -> gr.Blocks:
    """Create and return the Gradio interface for LlumDocs."""
    model_choices = available_models()
    model_map = dict(model_choices)

    vision_model_choices = available_vision_models()
    vision_model_map = dict(vision_model_choices)

    source_map = {label: code for label, code in LANGUAGE_OPTIONS}

    # Check email intelligence availability at runtime
    email_intelligence_available = _check_email_intelligence_available()
    features_with_availability = []
    for feature in FEATURES:
        if feature["label"] == "Email intelligence":
            # Update availability based on runtime check
            feature = {**feature, "available": email_intelligence_available}
        features_with_availability.append(feature)

    default_feature = next(
        (feature["label"] for feature in features_with_availability if feature["available"]),
        features_with_availability[0]["label"],
    )

    with gr.Blocks(title="LlumDocs") as demo:
        # Inject custom CSS
        gr.HTML(f"<style>{FEATURE_BUTTON_CSS}</style>", visible=False)

        gr.Markdown(
            """
            # 🌟 LlumDocs

            **Transform documents, text, and images into structured knowledge with LLMs.**

            LlumDocs is a comprehensive toolkit that processes raw documents through OCR,
            extracts structured data, translates content, generates summaries, and analyzes text
            using Large Language Models. Built with FastAPI and Gradio, it provides both REST API
            and web UI interfaces, and uses LiteLLM to seamlessly switch between OpenAI cloud
            models and local Ollama models without changing your code.

            **Available capabilities:**
            - **Translation**: Translate between Catalan, Spanish, and English with auto-detection
            - **Text transformation**: Rewrite text in technical, simplified, or company tone
            - **Summarization**: Generate short, detailed, or executive summaries
            - **Keyword extraction**: Extract top key concepts and phrases
            - **Image description**: Generate captions and detailed descriptions of images
            - **Email intelligence**: Route emails, detect phishing, and analyze sentiment
            - **Document extraction**: Extract structured data from delivery notes, bank
              statements, and payroll documents with OCR
            """
        )

        with gr.Row():
            # Left sidebar with feature buttons
            with gr.Column(scale=1):
                # Feature buttons (utilities roadmap)
                # Create sidebar with updated availability
                feature_button_refs = []
                gr.Markdown("### Utilities roadmap")
                for idx, feature in enumerate(features_with_availability):
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

                # Keywords panel
                keyword_panel, _ = create_keywords_panel(model_map, model_choices)
                panel_map["Keyword extraction"] = keyword_panel

                # Text transformation panel (unified)
                transform_panel, _ = create_text_transformation_panel(model_map, model_choices)
                panel_map["Text transformation"] = transform_panel

                # Image description panel
                image_panel, _ = create_image_panel(vision_model_map, vision_model_choices)
                panel_map["Image description"] = image_panel

                # Email intelligence panel
                email_panel, _ = create_email_intelligence_panel()
                panel_map["Email intelligence"] = email_panel

                # Document extraction panel
                extraction_panel, _ = create_document_extraction_panel(model_map, model_choices)
                panel_map["Document extraction"] = extraction_panel

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

        # Add JavaScript to show "Processing..." with live timer for all buttons
        gr.HTML(
            value="""
            <script>
            (function() {
                function setupProcessingTimers() {
                    // Find all processing status elements
                    document.querySelectorAll('.processing-status').forEach(function(statusEl) {
                        // Skip if already set up
                        if (statusEl.dataset.timerSetup === 'true') return;
                        statusEl.dataset.timerSetup = 'true';

                        // Find the associated button (look in parent container)
                        const container = statusEl.closest('.gradio-column, .gradio-row, form');
                        if (!container) return;

                        const button = container.querySelector(
                            'button[class*="primary"], button.variant-primary'
                        );
                        if (!button) return;

                        let startTime = null;
                        let timerInterval = null;

                        button.addEventListener('click', function() {
                            startTime = Date.now();
                            statusEl.style.display = 'block';
                            statusEl.innerHTML = '⏳ Processing...';

                            // Update timer every 100ms
                            timerInterval = setInterval(function() {
                                if (startTime) {
                                    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                                    statusEl.innerHTML = `⏳ Processing... (${elapsed}s)`;
                                }
                            }, 100);
                        });

                        // Watch for when status message is updated (processing complete)
                        const observer = new MutationObserver(function(mutations) {
                            mutations.forEach(function(mutation) {
                                if (
                                    mutation.type === 'childList' ||
                                    mutation.type === 'characterData'
                                ) {
                                    const text = statusEl.textContent || statusEl.innerText || '';
                                    if (text.includes('✓') || text.includes('✗')) {
                                        // Processing complete, stop timer
                                        if (timerInterval) {
                                            clearInterval(timerInterval);
                                            timerInterval = null;
                                        }
                                        startTime = null;
                                    }
                                }
                            });
                        });

                        observer.observe(statusEl, {
                            childList: true,
                            characterData: true,
                            subtree: true
                        });
                    });
                }

                // Run on page load
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', setupProcessingTimers);
                } else {
                    setupProcessingTimers();
                }

                // Also run after Gradio updates the DOM
                const bodyObserver = new MutationObserver(function() {
                    setTimeout(setupProcessingTimers, 100);
                });
                bodyObserver.observe(document.body, { childList: true, subtree: true });
            })();
            </script>
            """,
            visible=False,
        )

    return demo


def main() -> None:
    """CLI entrypoint for running the LlumDocs Gradio UI."""

    demo = create_interface()
    share = os.getenv("LLUMDOCS_UI_SHARE", "false").lower() in ("true", "1", "yes")
    server_name = os.getenv("LLUMDOCS_UI_HOST", "0.0.0.0")
    server_port = int(os.getenv("LLUMDOCS_UI_PORT", "7860"))
    demo.launch(share=share, server_name=server_name, server_port=server_port)


if __name__ == "__main__":
    main()
