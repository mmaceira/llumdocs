"""FastAPI router for image description endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from llumdocs.services.image_description_service import (
    ImageDescriptionError,
    describe_image,
)


class ImageDescriptionResponse(BaseModel):
    description: str


router = APIRouter(prefix="/api", tags=["images"])


@router.post(
    "/images/describe",
    response_model=ImageDescriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Describe an image",
)
async def describe(
    image: Annotated[UploadFile, File(description="Image file to describe")],
    detail_level: Annotated[
        str, Form(description="Level of detail: 'short' or 'detailed'")
    ] = "short",
    max_size: Annotated[
        int, Form(description="Maximum size for the longest side in pixels (default: 512)")
    ] = 512,
    model: Annotated[
        str | None,
        Form(
            description=(
                "Optional LiteLLM vision model identifier override "
                "(e.g., 'o4-mini', 'ollama/qwen3-vl:8b')"
            )
        ),
    ] = None,
) -> ImageDescriptionResponse:
    """
    Generate a textual description of an uploaded image.

    Supported image formats: JPEG, PNG, GIF, WebP
    """
    # Validate max_size
    if max_size < 1 or max_size > 2048:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_size must be between 1 and 2048 pixels.",
        )

    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG, PNG, GIF, or WebP).",
        )

    try:
        # Read image bytes
        image_bytes = await image.read()

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is empty.",
            )

        # Generate description
        description = describe_image(
            image_bytes,
            detail_level=detail_level,  # type: ignore[arg-type]
            max_size=max_size,
            model_hint=model,
        )

        return ImageDescriptionResponse(description=description)

    except ImageDescriptionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
