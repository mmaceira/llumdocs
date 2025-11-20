"""FastAPI application for LlumDocs."""

from __future__ import annotations

import os

import uvicorn
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

    @app.get("/health", summary="Simple healthcheck")
    async def health():
        """Lightweight liveness probe used by deployment platforms."""
        return {"status": "ok"}

    return app


app = create_app()


def main() -> None:
    """CLI entrypoint for running the LlumDocs API server."""
    host = os.getenv("LLUMDOCS_HOST", "0.0.0.0")
    port = int(os.getenv("LLUMDOCS_PORT", "8000"))
    reload = os.getenv("LLUMDOCS_RELOAD", "false").lower() in ("true", "1", "yes")

    uvicorn.run(
        "llumdocs.api.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
