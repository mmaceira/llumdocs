"""Common utilities shared across UI panels."""

from __future__ import annotations

import gradio as gr

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
