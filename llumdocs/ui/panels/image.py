"""Image description panel for LlumDocs Gradio interface."""

from __future__ import annotations

import io
import time

import gradio as gr

from llumdocs.services.image_description_service import ImageDescriptionError, describe_image
from llumdocs.ui.error_messages import format_error_message
from llumdocs.ui.panels.common import (
    create_error_display,
    create_processing_status,
    create_vision_dropdown,
)


def create_image_panel(
    vision_model_map: dict[str, str], vision_model_choices: list[tuple[str, str]]
) -> tuple[gr.Column, callable]:
    """Create the image description panel."""
    with gr.Column(visible=False) as image_panel:
        gr.Markdown("Describe images using vision models.")
        vision_model_dropdown = create_vision_dropdown(vision_model_choices)
        image_input = gr.Image(label="Image to describe", type="pil", elem_id="image-input")
        detail_level = gr.Radio(
            label="Detail level",
            choices=["short", "detailed"],
            value="short",
        )
        max_size = gr.Dropdown(
            label="Max size (longest axis)",
            choices=[128, 256, 512, 1024, 2048],
            value=512,
            info="Maximum size for the longest side in pixels",
        )
        image_button = gr.Button("Describe image", variant="primary")
        image_status = create_processing_status()
        image_output = gr.Textbox(
            label="Description", lines=8, interactive=False, elem_id="image-output"
        )
        image_error = create_error_display()

        def run_image_description(
            image, detail_level_value: str, max_size_value: int, vision_model_label: str
        ) -> tuple[str, str, str]:
            start_time = time.time()
            if image is None:
                return "", "", "Please upload an image."
            vision_model_id = vision_model_map.get(vision_model_label)
            if not vision_model_id:
                return "", "", f"Unknown vision model: {vision_model_label!r}."
            try:
                # Convert PIL image to bytes
                img_bytes = io.BytesIO()
                image.save(img_bytes, format="PNG")
                img_bytes = img_bytes.getvalue()

                result = describe_image(
                    img_bytes,
                    detail_level=detail_level_value,
                    max_size=int(max_size_value),
                    model_hint=vision_model_id,  # type: ignore[arg-type]
                )
                elapsed = time.time() - start_time
                status_msg = f"✓ Processing completed in {elapsed:.2f} seconds"
                return result, status_msg, ""
            except ImageDescriptionError as exc:
                elapsed = time.time() - start_time
                status_msg = f"✗ Processing failed after {elapsed:.2f} seconds"
                return "", status_msg, format_error_message(exc)

        image_button.click(
            fn=run_image_description,
            inputs=[image_input, detail_level, max_size, vision_model_dropdown],
            outputs=[image_output, image_status, image_error],
            api_name=None,
        )

    return image_panel, image_button
