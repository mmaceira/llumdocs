"""UI layout helpers for LlumDocs Gradio interface."""

from __future__ import annotations

import gradio as gr

FEATURES = [
    {"label": "Translate text", "available": True, "description": "Catalan ⇄ Spanish ⇄ English"},
    {
        "label": "Text transformation",
        "available": True,
        "description": "Technical, simplify, or company tone",
    },
    {
        "label": "Document summaries",
        "available": True,
        "description": "Short, detailed, or executive",
    },
    {"label": "Keyword extraction", "available": True, "description": "Top key concepts"},
    {"label": "Image description", "available": True, "description": "Describe images with AI"},
    {
        "label": "Email intelligence",
        "available": True,
        "description": "Route + phishing + sentiment",
    },
    {"label": "Invoice data extraction", "available": False, "description": "Coming soon"},
    {"label": "Document classification", "available": False, "description": "Coming soon"},
]


"""
Feature Button CSS Convention

The UI uses a CSS class system for feature buttons with the following conventions:

- `.feature-button`: Base style for all feature buttons
  - Applied to all feature selection buttons
  - Provides consistent sizing, padding, and transitions

- `.feature-available`: Enabled but not currently selected
  - Blue background (#6c63ff)
  - Used for available features that are not active

- `.feature-active`: Currently selected feature
  - Green background (#1fb978)
  - Bold font weight
  - Applied to the feature panel currently visible

- `.feature-disabled`: Coming-soon or unavailable features
  - Grey background (#e7e7e7)
  - Grey text (#9a9a9a)
  - Non-interactive

The CSS is injected via `Blocks(..., css=FEATURE_BUTTON_CSS)` in the main interface.
Buttons are created with `elem_classes=["feature-button", "feature-available"]` etc.
"""

FEATURE_BUTTON_CSS = """
/* Base styles for all feature buttons */
.feature-button {
    width: 100%;
    text-align: left;
    border-radius: 0.75rem;
    padding: 0.75rem 1.1rem;
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
    margin-bottom: 0.5rem;
    font-style: italic;
    color: #6f6f6f;
}

/* Processing status message styling */
.processing-status {
    font-size: 0.9rem;
    color: #666;
    font-style: italic;
    margin-top: 0.5rem;
}
"""


def create_feature_sidebar(
    default_feature: str,
) -> list[tuple[str, gr.Button, bool, str]]:
    """Create the feature selection sidebar buttons.

    This function should be called within a sidebar Column context.

    Args:
        default_feature: The feature to mark as active by default

    Returns:
        List of (label, button, available, elem_id) tuples
    """
    feature_button_refs: list[tuple[str, gr.Button, bool, str]] = []

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
        feature_button_refs.append((feature["label"], btn, feature["available"], elem_id))

    return feature_button_refs


def create_panel_switcher(
    panel_map: dict[str, gr.Column],
    feature_button_refs: list[tuple[str, gr.Button, bool, str]],
) -> callable:
    """Create the panel switching logic."""
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
                button_updates.append(gr.update(elem_classes=["feature-button", "feature-active"]))
            else:
                button_updates.append(
                    gr.update(elem_classes=["feature-button", "feature-available"])
                )

        return panel_updates + button_updates

    return switch_panel, panel_outputs, button_outputs, clickable_buttons
