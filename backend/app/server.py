"""FastAPI application factory."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import (
    accounts,
    admin,
    assistant,
    cashflow,
    contextual_insights,
    csv_import,
    fx,
    insights,
    integrations,
    monarch_import,
    portfolio,
    portfolio_reviews,
    transactions,
    wealthsimple_import,
)
from backend.api.v1.routes import router as v1_router
from backend.app.config import get_settings

# Every router is imported unconditionally: a broken module must fail the
# application at start-up, not silently drop its routes.
# `backend/api/budgets.py` is mounted in #114 once its routes are repaired.
ROUTERS = [
    v1_router,
    transactions.router,
    csv_import.router,
    portfolio.router,
    portfolio_reviews.router,
    wealthsimple_import.router,
    monarch_import.router,
    admin.router,
    accounts.router,
    fx.router,
    integrations.router,
    insights.router,
    assistant.router,
    contextual_insights.router,
    cashflow.router,
]


def _cors_allow_origins() -> list[str]:
    """Origins allowed for browser clients (dev + optional CORS_ALLOW_ORIGINS)."""
    base = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    extra = os.environ.get("CORS_ALLOW_ORIGINS", "").strip()
    if not extra:
        return base
    for o in extra.split(","):
        u = o.strip()
        if u and u not in base:
            base.append(u)
    return base


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title="Canopy API",
        description="Self-hosted personal finance, investment, and budgeting dashboard",
        debug=settings.debug,
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROUTERS:
        app.include_router(router)

    return app


app = create_app()
