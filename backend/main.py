"""Entrypoint for running the API with `python -m backend.main`."""

import uvicorn

from backend.app.server import app
from backend.app.config import get_settings


def run() -> None:
    """Run application with uvicorn development server."""

    settings = get_settings()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()

