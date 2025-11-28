"""FastAPI router for translation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from llumdocs.api.error_handling import handle_service_error
from llumdocs.services.translation_service import TranslationError, translate_text


class TranslationRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Text to translate",
        examples=["Hello, how are you?", "Bon dia, com estàs?"],
    )
    source_lang: str = Field(
        "auto",
        pattern="^(auto|ca|es|en)$",
        description=(
            "Source language code. Accepted values: "
            "'auto' (auto-detect), 'ca' (Catalan), 'es' (Spanish), 'en' (English)"
        ),
        examples=["auto", "ca", "es", "en"],
    )
    target_lang: str = Field(
        "ca",
        pattern="^(ca|es|en)$",
        description=(
            "Target language code. Accepted values: "
            "'ca' (Catalan), 'es' (Spanish), 'en' (English)"
        ),
        examples=["ca", "es", "en"],
    )
    model: str | None = Field(
        default=None,
        description=(
            "Optional LiteLLM model identifier override "
            "(e.g., 'gpt-4o-mini', 'ollama/llama3.1:8b'). "
            "Set to null or omit to use default."
        ),
        examples=[None, "gpt-4o-mini", "ollama/llama3.1:8b"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Hello, how are you?",
                "source_lang": "auto",
                "target_lang": "ca",
                "model": None,
            }
        }
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

    **Example curl command:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/api/translate' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
        "text": "Hello, how are you?",
        "source_lang": "auto",
        "target_lang": "ca",
        "model": null
      }'
    ```
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
