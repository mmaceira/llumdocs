"""FastAPI router exposing text transformation utilities."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from llumdocs.api.error_handling import handle_service_error
from llumdocs.services.text_transform_service import (
    TextTransformError,
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
)


class KeywordsRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Text to analyze",
        examples=["Machine learning is a subset of artificial intelligence"],
    )
    max_keywords: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of keywords to return (1-50)",
        examples=[10, 5, 20],
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
                "text": "Machine learning is a subset of artificial intelligence",
                "max_keywords": 10,
                "model": None,
            }
        }
    )


class KeywordsResponse(BaseModel):
    keywords: list[str]


class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=1, examples=["Your long document text here..."])
    summary_type: str = Field(
        default="short",
        pattern="^(short|detailed|executive)$",
        description="Summary style. Accepted values: 'short', 'detailed', 'executive'",
        examples=["short", "detailed", "executive"],
    )
    model: str | None = Field(
        default=None,
        description=(
            "Optional LiteLLM model identifier override "
            "(e.g., 'gpt-4o-mini', 'ollama/llama3.1:8b'). "
            "Set to null or omit to use default."
        ),
        examples=[None, "gpt-4o-mini"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Your long document text here...",
                "summary_type": "short",
                "model": None,
            }
        }
    )


class SummaryResponse(BaseModel):
    summary: str


class TechnicalRequest(BaseModel):
    text: str = Field(..., min_length=1, examples=["Make this more technical"])
    domain: str | None = Field(
        default=None,
        description="Domain focus (e.g., 'tech', 'legal', 'medical'). Optional.",
        examples=[None, "tech", "legal", "medical"],
    )
    target_level: str | None = Field(
        default=None,
        description="Expertise level (e.g., 'expert', 'intermediate'). Optional.",
        examples=[None, "expert", "intermediate"],
    )
    model: str | None = Field(
        default=None,
        description=(
            "Optional LiteLLM model identifier override "
            "(e.g., 'gpt-4o-mini', 'ollama/llama3.1:8b'). "
            "Set to null or omit to use default."
        ),
        examples=[None, "gpt-4o-mini"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Make this more technical",
                "domain": None,
                "target_level": None,
                "model": None,
            }
        }
    )


class TechnicalResponse(BaseModel):
    technical_text: str


class PlainLanguageRequest(BaseModel):
    text: str = Field(..., min_length=1, examples=["Complex technical jargon here"])
    target_reading_level: str | None = Field(
        default=None,
        description=(
            "Target audience reading level. "
            "Examples: 'child', 'teen', 'adult_general'. Optional."
        ),
        examples=[None, "child", "teen", "adult_general"],
    )
    model: str | None = Field(
        default=None,
        description=(
            "Optional LiteLLM model identifier override "
            "(e.g., 'gpt-4o-mini', 'ollama/llama3.1:8b'). "
            "Set to null or omit to use default."
        ),
        examples=[None, "gpt-4o-mini"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Complex technical jargon here",
                "target_reading_level": None,
                "model": None,
            }
        }
    )


class PlainLanguageResponse(BaseModel):
    plain_text: str


router = APIRouter(prefix="/api", tags=["text-tools"])


@router.post(
    "/text/keywords",
    response_model=KeywordsResponse,
    summary="Extract keywords from text",
)
async def keywords(payload: KeywordsRequest) -> KeywordsResponse:
    """
    Extract keywords from text.

    **Example curl command:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/api/text/keywords' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
        "text": "Machine learning is a subset of artificial intelligence",
        "max_keywords": 10,
        "model": null
      }'
    ```
    """
    try:
        result = extract_keywords(
            payload.text,
            max_keywords=payload.max_keywords,
            model_hint=payload.model,
        )
    except TextTransformError as exc:
        raise handle_service_error(exc) from exc
    return KeywordsResponse(keywords=result)


@router.post(
    "/documents/summarize",
    response_model=SummaryResponse,
    summary="Summarize a document",
)
async def summarize(payload: SummaryRequest) -> SummaryResponse:
    """
    Summarize a document.

    **Example curl command:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/api/documents/summarize' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
        "text": "Your long document text here...",
        "summary_type": "short",
        "model": null
      }'
    ```
    """
    try:
        summary_text = summarize_document(
            payload.text,
            summary_type=payload.summary_type,  # type: ignore[arg-type]
            model_hint=payload.model,
        )
    except TextTransformError as exc:
        raise handle_service_error(exc) from exc
    return SummaryResponse(summary=summary_text)


@router.post(
    "/text/technical",
    response_model=TechnicalResponse,
    summary="Make text more technical",
)
async def make_technical(payload: TechnicalRequest) -> TechnicalResponse:
    """
    Make text more technical.

    **Example curl command:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/api/text/technical' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
        "text": "Make this more technical",
        "domain": null,
        "target_level": null,
        "model": null
      }'
    ```
    """
    try:
        technical_text = make_text_more_technical(
            payload.text,
            domain=payload.domain,
            target_level=payload.target_level,
            model_hint=payload.model,
        )
    except TextTransformError as exc:
        raise handle_service_error(exc) from exc
    return TechnicalResponse(technical_text=technical_text)


@router.post(
    "/text/plain",
    response_model=PlainLanguageResponse,
    summary="Simplify text into plain language",
)
async def simplify(payload: PlainLanguageRequest) -> PlainLanguageResponse:
    """
    Simplify text into plain language.

    **Example curl command:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/api/text/plain' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
        "text": "Complex technical jargon here",
        "target_reading_level": null,
        "model": null
      }'
    ```
    """
    try:
        plain_text = simplify_text(
            payload.text,
            target_reading_level=payload.target_reading_level,
            model_hint=payload.model,
        )
    except TextTransformError as exc:
        raise handle_service_error(exc) from exc
    return PlainLanguageResponse(plain_text=plain_text)
