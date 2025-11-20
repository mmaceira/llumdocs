"""FastAPI router for translation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from llumdocs.api.error_handling import handle_service_error
from llumdocs.services.translation_service import TranslationError, translate_text


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to translate")
    source_lang: str = Field(
        "auto",
        pattern="^(auto|ca|es|en)$",
        description="Source language code or 'auto'",
    )
    target_lang: str = Field(
        "ca",
        pattern="^(ca|es|en)$",
        description="Target language code",
    )
    model: str | None = Field(
        default=None,
        description="Optional LiteLLM model identifier override",
    )


class TranslationResponse(BaseModel):
    translated_text: str


router = APIRouter(prefix="/api", tags=["translation"])


@router.post(
    "/translate",
    response_model=TranslationResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate text between Catalan, Spanish, and English",
)
async def translate(payload: TranslationRequest) -> TranslationResponse:
    """
    Translate text using the translation service.
    """

    try:
        translated = translate_text(
            payload.text,
            source_lang=payload.source_lang,
            target_lang=payload.target_lang,
            model_hint=payload.model,
        )
    except TranslationError as exc:
        raise handle_service_error(exc) from exc

    return TranslationResponse(translated_text=translated)
