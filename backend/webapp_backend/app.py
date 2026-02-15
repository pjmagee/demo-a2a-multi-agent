"""FastAPI application exposing the BFF endpoints."""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.otel_config import configure_telemetry

from webapp_backend.api.routes import router
from webapp_backend.config import Settings, get_settings
from webapp_backend.logging import configure_logging

# Initialize logging and telemetry at module import time
configure_logging()
configure_telemetry("backend")

PORT = int(os.getenv(key="PORT", default="8100"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings: Settings = get_settings()
    app = FastAPI(title="Webapp Backend", version="0.1.0")
    app.include_router(router=router)

    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    return app


app: FastAPI = create_app()


@app.get("/health")
async def health() -> dict[str, bool]:
    """Health check endpoint."""
    return {"ok": True}


def main() -> None:
    """Run the development server."""
    uvicorn.run(
        app="webapp_backend.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
