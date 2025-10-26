"""FastAPI application exposing the BFF endpoints."""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from webapp_backend.agent_router import copilot_router
from webapp_backend.api.routes import router
from webapp_backend.config import Settings, get_settings
from webapp_backend.logging import configure_logging

PORT = int(os.getenv(key="PORT", default="8100"))
HOST: str = os.getenv(key="HOST", default="127.0.0.1")


def create_app() -> FastAPI:
    settings: Settings = get_settings()
    app = FastAPI(title="Webapp Backend", version="0.1.0")
    app.include_router(router=router)
    app.include_router(router=copilot_router)

    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    return app


app: FastAPI = create_app()


def main() -> None:
    """Run the development server."""
    configure_logging()
    uvicorn.run(
        app="webapp_backend.app:app",
        host=HOST,
        port=PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
