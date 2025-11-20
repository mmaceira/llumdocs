"""
Image description service implementation using LiteLLM vision models.
"""

from __future__ import annotations

import io
from typing import Literal

from PIL import Image

from llumdocs.llm import LLMConfigurationError, vision_completion

DetailLevel = Literal["short", "detailed"]


class ImageDescriptionError(Exception):
    """Raised when an image description cannot be completed."""


def _validate_detail_level(detail_level: str) -> DetailLevel:
    """Validate and normalize detail level."""
    if detail_level not in {"short", "detailed"}:
        raise ImageDescriptionError(
            f"detail_level must be 'short' or 'detailed' (received {detail_level!r})."
        )
    return detail_level  # type: ignore[return-value]


def _resize_image(image_bytes: bytes, max_size: int) -> bytes:
    """
    Resize an image to a maximum dimension while maintaining aspect ratio.

    Args:
        image_bytes: Original image data as bytes.
        max_size: Maximum size for the longest side in pixels.

    Returns:
        Resized image data as bytes in JPEG format.
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary (handles RGBA, P, etc.)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Calculate new dimensions maintaining aspect ratio
    width, height = img.size
    if width > height:
        if width > max_size:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_width, new_height = width, height
    else:
        if height > max_size:
            new_height = max_size
            new_width = int(width * (max_size / height))
        else:
            new_width, new_height = width, height

    # Resize if needed
    if (new_width, new_height) != (width, height):
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save to bytes as JPEG
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85)
    return output.getvalue()


def _build_prompt(detail_level: DetailLevel) -> str:
    """Build the prompt for image description based on detail level."""
    if detail_level == "short":
        return (
            "Describe this image concisely in English. "
            "Focus on the main subject, key objects, and overall scene. "
            "Keep the description brief and to the point."
        )
    else:  # detailed
        return (
            "Provide a detailed description of this image in English. "
            "Include information about: "
            "- The main subject and its characteristics\n"
            "- Secondary objects and their relationships\n"
            "- Background elements and context\n"
            "- Colors, lighting, and composition\n"
            "- Any text visible in the image\n"
            "- The overall mood or atmosphere"
        )


def describe_image(
    image_bytes: bytes,
    detail_level: DetailLevel = "short",
    *,
    max_size: int = 128,
    model_hint: str | None = None,
) -> str:
    """
    Generate a textual description of an image using a vision model.

    Args:
        image_bytes: Image data as bytes.
        detail_level: Level of detail for the description ("short" or "detailed").
        max_size: Maximum size for the longest side in pixels (default: 128).
        model_hint: Optional explicit vision model id (e.g., "o4-mini", "ollama/qwen3-vl:8b").

    Returns:
        The generated description text.

    Raises:
        ImageDescriptionError: For validation or backend failures.
    """
    if not image_bytes:
        raise ImageDescriptionError("image_bytes cannot be empty.")

    if max_size <= 0:
        raise ImageDescriptionError("max_size must be greater than 0.")

    validated_level = _validate_detail_level(detail_level)
    prompt = _build_prompt(validated_level)

    try:
        # Resize image before sending to model
        resized_bytes = _resize_image(image_bytes, max_size)
        return vision_completion(prompt, resized_bytes, model_hint=model_hint)
    except LLMConfigurationError as exc:
        raise ImageDescriptionError(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise ImageDescriptionError(f"Image description failed: {exc}") from exc


__all__ = ["DetailLevel", "ImageDescriptionError", "describe_image"]
