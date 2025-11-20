"""FastAPI router exposing text transformation utilities."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from llumdocs.api.error_handling import handle_service_error
from llumdocs.services.text_transform_service import (
    TextTransformError,
    extract_keywords,
    make_text_more_technical,
    simplify_text,
    summarize_document,
)


class KeywordsRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to analyze")
    max_keywords: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of keywords to return",
    )
    model: str | None = Field(
        default=None,
        description="Optional LiteLLM model identifier override",
    )


class KeywordsResponse(BaseModel):
    keywords: list[str]


class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=1)
    summary_type: str = Field(
        default="short",
        pattern="^(short|detailed|executive)$",
        description="Summary style",
    )
    model: str | None = Field(default=None)


class SummaryResponse(BaseModel):
    summary: str


class TechnicalRequest(BaseModel):
    text: str = Field(..., min_length=1)
    domain: str | None = Field(default=None, description="Domain focus (e.g., tech, legal)")
    target_level: str | None = Field(default=None, description="Expertise level (e.g., expert)")
    model: str | None = Field(default=None)


class TechnicalResponse(BaseModel):
    technical_text: str


class PlainLanguageRequest(BaseModel):
    text: str = Field(..., min_length=1)
    target_reading_level: str | None = Field(
        default=None,
        description="Audience (e.g., child, teen, adult_general)",
    )
    model: str | None = Field(default=None)


class PlainLanguageResponse(BaseModel):
    plain_text: str


router = APIRouter(prefix="/api", tags=["text-tools"])


@router.post(
    "/text/keywords",
    response_model=KeywordsResponse,
    summary="Extract keywords from text",
)
async def keywords(payload: KeywordsRequest) -> KeywordsResponse:
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
    try:
        plain_text = simplify_text(
            payload.text,
            target_reading_level=payload.target_reading_level,
            model_hint=payload.model,
        )
    except TextTransformError as exc:
        raise handle_service_error(exc) from exc
    return PlainLanguageResponse(plain_text=plain_text)
