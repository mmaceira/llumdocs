"""Email intelligence panel for LlumDocs Gradio interface."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.services import (
    DEFAULT_EMAIL_ROUTING_LABELS,
    EMAIL_INTEL_AVAILABLE,
    EmailIntelligenceError,
    EmailIntelligenceService,
    analyze_sentiment,
    classify_email,
    detect_phishing,
)
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import create_error_display, create_processing_status


def create_email_intelligence_panel() -> tuple[gr.Column, callable]:
    """Create the email intelligence panel."""
    with gr.Column(visible=False) as email_panel:
        if not EMAIL_INTEL_AVAILABLE:
            gr.Markdown(
                "⚠️ Email intelligence is not available. "
                "Install with: `pip install 'llumdocs[email]'`"
            )
            return email_panel, None

        gr.Markdown("Analyze emails: route to categories, detect phishing, and analyze sentiment.")
        email_textbox = gr.Textbox(
            label="Email text",
            placeholder="Paste email content here…",
            lines=8,
            elem_id="email-textbox",
        )
        email_button = gr.Button("Analyze email", variant="primary")
        email_status = create_processing_status()

        routing_output = gr.Textbox(
            label="Routing category", lines=2, interactive=False, elem_id="routing-output"
        )
        phishing_output = gr.Textbox(
            label="Phishing detection", lines=2, interactive=False, elem_id="phishing-output"
        )
        sentiment_output = gr.Textbox(
            label="Sentiment analysis", lines=2, interactive=False, elem_id="sentiment-output"
        )
        email_error = create_error_display()

        def run_email_analysis(text: str) -> tuple[str, str, str, str, str]:
            start_time = time.time()
            if not EMAIL_INTEL_AVAILABLE:
                return "", "", "", "", "Email intelligence is not available."
            try:
                service = EmailIntelligenceService()
                routing = classify_email(text, service, DEFAULT_EMAIL_ROUTING_LABELS)
                phishing = detect_phishing(text, service)
                sentiment = analyze_sentiment(text, service)

                routing_text = f"Category: {routing.category}\nConfidence: {routing.confidence:.2%}"
                phishing_text = (
                    f"Phishing: {'Yes' if phishing.is_phishing else 'No'}\n"
                    f"Confidence: {phishing.confidence:.2%}"
                )
                sentiment_text = (
                    f"Sentiment: {sentiment.sentiment}\nConfidence: {sentiment.confidence:.2%}"
                )

                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return routing_text, phishing_text, sentiment_text, status_msg, ""
            except EmailIntelligenceError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", "", "", status_msg, format_error_message(exc)

        email_button.click(
            fn=run_email_analysis,
            inputs=[email_textbox],
            outputs=[routing_output, phishing_output, sentiment_output, email_status, email_error],
        )

    return email_panel, email_button
