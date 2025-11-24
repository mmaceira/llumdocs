"""FastAPI router for image description endpoints."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from llumdocs.api.error_handling import handle_service_error
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
        str,
        Form(
            description="Level of detail. Accepted values: 'short' or 'detailed'",
            examples=["short", "detailed"],
        ),
    ] = "short",
    max_size: Annotated[
        int,
        Form(
            description="Maximum size for the longest side in pixels (1-2048, default: 512)",
            examples=[512, 1024, 2048],
        ),
    ] = 512,
    model: Annotated[
        str | None,
        Form(
            description=(
                "Optional LiteLLM vision model identifier override "
                "(e.g., 'o4-mini', 'ollama/qwen3-vl:8b'). Set to empty or omit to use default."
            ),
            examples=[None, "o4-mini", "ollama/qwen3-vl:8b"],
        ),
    ] = None,
) -> ImageDescriptionResponse:
    """
    Generate a textual description of an uploaded image.

    Supported image formats: JPEG, PNG, GIF, WebP

    **Example curl command:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/api/images/describe' \
      -H 'accept: application/json' \
      -F 'image=@/path/to/image.jpg' \
      -F 'detail_level=short' \
      -F 'max_size=512' \
      -F 'model='
    ```
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

        # Check file size limit (default 10MB, configurable via env)
        max_file_size = int(os.getenv("LLUMDOCS_MAX_IMAGE_SIZE_BYTES", str(10 * 1024 * 1024)))
        if len(image_bytes) > max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image file exceeds maximum size of {max_file_size / (1024 * 1024):.1f}MB.",
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
        raise handle_service_error(exc) from exc
