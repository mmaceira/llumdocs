"""Email intelligence panel for LlumDocs Gradio interface."""

from __future__ import annotations

import time

import gradio as gr

from llumdocs.services import (
    DEFAULT_EMAIL_ROUTING_LABELS,
    EMAIL_INTEL_AVAILABLE,
    EmailIntelligenceError,
    EmailIntelligenceService,
)
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import create_error_display, create_processing_status


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

        analyze_button = gr.Button("Analyze email", variant="primary")
        email_status = create_processing_status()

        classification_output = gr.Markdown(label="Classification", elem_id="classification-output")
        phishing_output = gr.Markdown(label="Phishing detection", elem_id="phishing-output")
        sentiment_output = gr.Markdown(label="Sentiment analysis", elem_id="sentiment-output")

        email_error = create_error_display()

        def run_email_analysis(
            text: str,
            multi_label_enabled: bool,
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

            routing_labels = (
                DEFAULT_EMAIL_ROUTING_LABELS
                if DEFAULT_EMAIL_ROUTING_LABELS
                else ["support", "billing", "sales", "HR", "IT incident"]
            )

            try:
                service = EmailIntelligenceService(
                    routing_labels,
                    multi_label=multi_label_enabled,
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

            # Find the highest score to bold it
            max_classification_score = classification_items[0][1] if classification_items else 0.0

            classification_lines = [
                "### 📋 Email Categorization",
                "",
                (
                    "This analysis uses **BGE-M3 Zero-Shot Classification** "
                    "(MoritzLaurer/bge-m3-zeroshot-v2.0) to categorize emails into "
                    "predefined routing categories. The model uses semantic understanding "
                    "to match email content against category labels without requiring "
                    "training data. This helps automatically route emails to the "
                    "appropriate department or team."
                ),
                "",
            ]

            for label, score in classification_items:
                percentage = score * 100
                is_max = score == max_classification_score
                if is_max:
                    classification_lines.append(f"- **{label}**: **{percentage:.2f}%**")
                else:
                    classification_lines.append(f"- {label}: {percentage:.2f}%")

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

            # Find the highest aggregated score to bold it
            max_aggregated_score = max(aggregated_scores.values()) if aggregated_scores else 0.0

            phishing_lines = [
                "### 🛡️ Spam & Phishing Detection",
                "",
                (
                    "This analysis uses **DistilBERT Phishing Detection** "
                    "(cybersectony/phishing-email-detection-distilbert_v2.1) to detect "
                    "whether the email is safe or potentially a phishing attempt or spam "
                    "message. The model has been trained on phishing email datasets and "
                    "analyzes patterns such as suspicious URLs, urgency tactics, and "
                    "impersonation attempts."
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
                        is_max = score == max_aggregated_score
                        if is_max:
                            phishing_lines.append(f"- **{label}: {pct:.2f}%**")
                        else:
                            phishing_lines.append(f"- {label}: {pct:.2f}%")

            # Show all individual label scores (the 4 model categories)
            if individual_scores:
                # Find the highest individual score to bold it
                max_individual_score = max(individual_scores.values())
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
                        readable_label = label.replace("_", " ").title()
                        is_max = score == max_individual_score
                        if is_max:
                            phishing_lines.append(f"- **{readable_label}: {pct:.2f}%**")
                        else:
                            phishing_lines.append(f"- {readable_label}: {pct:.2f}%")

                # Also show any other labels that might exist
                for label, score in sorted(
                    individual_scores.items(), key=lambda x: x[1], reverse=True
                ):
                    if label not in label_order:
                        pct = score * 100
                        readable_label = label.replace("_", " ").title()
                        is_max = score == max_individual_score
                        if is_max:
                            phishing_lines.append(f"- **{readable_label}: {pct:.2f}%**")
                        else:
                            phishing_lines.append(f"- {readable_label}: {pct:.2f}%")

            phishing_text = "\n".join(phishing_lines)

            # Format sentiment output
            sentiment_lines = [
                "### 😊 Sentiment Analysis",
                "",
                (
                    "This analysis uses **XLM-RoBERTa Multilingual Sentiment** "
                    "(cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual) to "
                    "determine the emotional tone of the email, classifying it as "
                    "positive, neutral, or negative. The model supports 100+ languages "
                    "and can detect sentiment even in multilingual contexts, helping you "
                    "understand customer satisfaction and communication tone."
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

                # Find the highest score to bold it
                max_sentiment_score = sorted_scores[0][1] if sorted_scores else 0.0

                for label, score in sorted_scores:
                    percentage = score * 100
                    is_max = score == max_sentiment_score
                    if is_max:
                        sentiment_lines.append(f"- **{label.capitalize()}**: **{percentage:.2f}%**")
                    else:
                        sentiment_lines.append(f"- {label.capitalize()}: {percentage:.2f}%")
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
            inputs=[message_text, allow_multi],
            outputs=[
                classification_output,
                phishing_output,
                sentiment_output,
                email_status,
                email_error,
            ],
        )

    return email_panel, analyze_button
