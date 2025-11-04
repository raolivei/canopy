"""FastAPI application factory."""

from fastapi import FastAPI

from backend.api.v1.routes import router as v1_router
from backend.app.config import get_settings


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )
    app.include_router(v1_router)
    return app


app = create_app()

