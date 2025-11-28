"""Email intelligence panel for LlumDocs Gradio interface."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.services import (
    EMAIL_INTEL_AVAILABLE,
    EmailIntelligenceError,
    EmailIntelligenceService,
)
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import create_error_display, create_processing_status


def _format_routing_results(routing) -> str:
    """Format routing classification results for display."""
    if not routing.labels or not routing.scores:
        return "No classification results available."

    # Format text output with all probabilities
    lines = ["**Email Routing Classification**\n"]
    lines.append("\n**All Categories:**")

    # Find the highest score to bold it
    max_score = max(routing.scores) if routing.scores else 0.0

    for label, score in zip(routing.labels, routing.scores, strict=False):
        # Zero-shot classification returns probabilities (0-1), convert to percentages
        # Always convert to percentage for display
        score_pct = score * 100  # Convert probability (0-1) to percentage (0-100)
        is_max = score == max_score
        if is_max:
            lines.append(f"- **{label}: {score_pct:.1f}%**")
        else:
            lines.append(f"- {label}: {score_pct:.1f}%")

    return "\n".join(lines)


def _format_phishing_results(phishing) -> str:
    """Format phishing detection results for display."""
    # Format text output
    lines = ["**Phishing Detection**\n"]
    lines.append(
        f"**Result:** {'🚨 PHISHING DETECTED' if phishing.label == 'phishing' else '✅ Safe Email'}"
    )
    lines.append(f"**Confidence:** {phishing.score:.1%}\n")
    lines.append("**Detailed Scores:**")

    # Find the highest score to bold it
    max_score = max(phishing.scores_by_label.values()) if phishing.scores_by_label else 0.0

    for label, score in sorted(phishing.scores_by_label.items(), key=lambda x: x[1], reverse=True):
        is_max = score == max_score
        if is_max:
            lines.append(f"- **{label}: {score:.1%}**")
        else:
            lines.append(f"- {label}: {score:.1%}")

    return "\n".join(lines)


def _format_sentiment_results(sentiment) -> str:
    """Format sentiment analysis results for display."""
    # Format text output
    sentiment_emoji = {
        "positive": "😊",
        "neutral": "😐",
        "negative": "😞",
    }
    emoji = sentiment_emoji.get(sentiment.label.lower(), "📊")

    lines = ["**Sentiment Analysis**\n"]
    lines.append(f"**Result:** {emoji} {sentiment.label.title()}")
    lines.append(f"**Confidence:** {sentiment.score:.1%}\n")
    lines.append("**All Sentiment Scores:**")

    # Find the highest score to bold it
    max_score = max(sentiment.scores_by_label.values()) if sentiment.scores_by_label else 0.0

    for label, score in sorted(sentiment.scores_by_label.items(), key=lambda x: x[1], reverse=True):
        is_max = score == max_score
        if is_max:
            lines.append(f"- **{label}: {score:.1%}**")
        else:
            lines.append(f"- {label}: {score:.1%}")

    return "\n".join(lines)


def create_email_intelligence_panel() -> tuple[gr.Column, callable]:
    """Create the email intelligence panel."""
    with gr.Column(visible=False) as email_panel:
        if not EMAIL_INTEL_AVAILABLE:
            gr.Markdown(
                "⚠️ Email intelligence is not available. "
                "Install with: `pip install 'llumdocs[email]'`"
            )
            return email_panel, None

        gr.Markdown("### Email Intelligence Analysis")
        gr.Markdown(
            "Analyze emails using AI-powered models to route to categories, detect phishing, "
            "and analyze sentiment across multiple languages."
        )

        email_textbox = gr.Textbox(
            label="Email text",
            placeholder="Paste email content here…",
            lines=8,
            elem_id="email-textbox",
        )
        email_button = gr.Button("Analyze email", variant="primary")
        email_status = create_processing_status()

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📧 Email Routing Classification")
                gr.Markdown(
                    "**What it does:** Classifies emails into predefined categories (support, "
                    "billing, sales, HR, IT incident) using zero-shot classification. This helps "
                    "automatically route emails to the appropriate department or team.\n\n"
                    "**How it works:** Uses a multilingual BGE model that can classify text into "
                    "any set of labels you provide, without requiring training data."
                )
                routing_output = gr.Markdown(label="Routing Results", elem_id="routing-output")

            with gr.Column():
                gr.Markdown("### 🛡️ Phishing Detection")
                gr.Markdown(
                    "**What it does:** Detects whether an email is phishing or spam using a "
                    "specialized DistilBERT model trained on phishing email datasets.\n\n"
                    "**How it works:** Analyzes email content for patterns commonly found in "
                    "phishing attempts, such as suspicious URLs, urgency tactics, and "
                    "impersonation attempts."
                )
                phishing_output = gr.Markdown(label="Phishing Results", elem_id="phishing-output")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 😊 Sentiment Analysis")
                gr.Markdown(
                    "**What it does:** Analyzes the emotional tone of the email (positive, "
                    "neutral, or negative) using a multilingual XLM-RoBERTa model.\n\n"
                    "**How it works:** Supports 100+ languages and can detect sentiment even in "
                    "multilingual contexts, helping you understand customer satisfaction and "
                    "communication tone."
                )
                sentiment_output = gr.Markdown(
                    label="Sentiment Results", elem_id="sentiment-output"
                )

        email_error = create_error_display()

        def run_email_analysis(text: str) -> tuple[str, str, str, str, str]:
            start_time = time.time()
            if not EMAIL_INTEL_AVAILABLE:
                return "", "", "", "Email intelligence is not available.", ""
            if not text or not text.strip():
                return "", "", "", "Please enter email text to analyze.", ""
            try:
                service = EmailIntelligenceService()
                routing = service.classify(text)
                phishing = service.phishing(text)
                sentiment = service.sentiment(text)

                routing_text = _format_routing_results(routing)
                phishing_text = _format_phishing_results(phishing)
                sentiment_text = _format_sentiment_results(sentiment)

                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return (
                    routing_text,
                    phishing_text,
                    sentiment_text,
                    status_msg,
                    "",
                )
            except EmailIntelligenceError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", "", "", status_msg, format_error_message(exc)

        email_button.click(
            fn=run_email_analysis,
            inputs=[email_textbox],
            outputs=[
                routing_output,
                phishing_output,
                sentiment_output,
                email_status,
                email_error,
            ],
        )

    return email_panel, email_button
