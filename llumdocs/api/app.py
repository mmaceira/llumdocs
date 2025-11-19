"""FastAPI application for LlumDocs."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llumdocs.api.image_endpoints import router as image_router
from llumdocs.api.text_tools_endpoints import router as text_tools_router
from llumdocs.api.translation_endpoints import router as translation_router


def create_app() -> FastAPI:
    app = FastAPI(title="LlumDocs API", version="0.1.0")

    allow_origins = os.getenv("LLUMDOCS_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in allow_origins],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    app.include_router(translation_router)
    app.include_router(text_tools_router)
    app.include_router(image_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
