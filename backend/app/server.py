"""FastAPI application factory."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.routes import router as v1_router
from backend.app.config import get_settings

# Import transaction and CSV import routers if they exist
try:
    from backend.api import csv_import, transactions

    HAS_TRANSACTION_ROUTERS = True
except ImportError:
    HAS_TRANSACTION_ROUTERS = False

# Import portfolio router
try:
    from backend.api import portfolio

    HAS_PORTFOLIO_ROUTER = True
except ImportError:
    HAS_PORTFOLIO_ROUTER = False

try:
    from backend.api import portfolio_reviews

    HAS_PORTFOLIO_REVIEWS_ROUTER = True
except ImportError:
    HAS_PORTFOLIO_REVIEWS_ROUTER = False

try:
    from backend.api import wealthsimple_import

    HAS_WEALTHSIMPLE_IMPORT_ROUTER = True
except ImportError:
    HAS_WEALTHSIMPLE_IMPORT_ROUTER = False

try:
    from backend.api import monarch_import

    HAS_MONARCH_IMPORT_ROUTER = True
except ImportError:
    HAS_MONARCH_IMPORT_ROUTER = False

try:
    from backend.api import admin as admin_api

    HAS_ADMIN_ROUTER = True
except ImportError:
    HAS_ADMIN_ROUTER = False

try:
    from backend.api import accounts as accounts_api

    HAS_ACCOUNTS_ROUTER = True
except ImportError:
    HAS_ACCOUNTS_ROUTER = False

try:
    from backend.api import fx as fx_api

    HAS_FX_ROUTER = True
except ImportError:
    HAS_FX_ROUTER = False

# Import integrations router
try:
    from backend.api import integrations

    HAS_INTEGRATIONS_ROUTER = True
except ImportError:
    HAS_INTEGRATIONS_ROUTER = False

# Import insights router
try:
    from backend.api import insights

    HAS_INSIGHTS_ROUTER = True
except ImportError:
    HAS_INSIGHTS_ROUTER = False

# Import assistant router
try:
    from backend.api import assistant

    HAS_ASSISTANT_ROUTER = True
except ImportError:
    HAS_ASSISTANT_ROUTER = False

try:
    from backend.api import budgets as budgets_api

    HAS_BUDGETS_ROUTER = True
except ImportError:
    HAS_BUDGETS_ROUTER = False

try:
    from backend.api import cashflow as cashflow_api

    HAS_CASHFLOW_ROUTER = True
except ImportError:
    HAS_CASHFLOW_ROUTER = False

try:
    from backend.api import recurring_patterns as recurring_patterns_api

    HAS_RECURRING_PATTERNS_ROUTER = True
except ImportError:
    HAS_RECURRING_PATTERNS_ROUTER = False

try:
    from backend.api import rules as rules_api

    HAS_RULES_ROUTER = True
except ImportError:
    HAS_RULES_ROUTER = False


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

    # Add CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include v1 router (health, summary endpoints)
    app.include_router(v1_router)

    # Include transaction + CSV import routers if available
    if HAS_TRANSACTION_ROUTERS:
        app.include_router(transactions.router)
        app.include_router(csv_import.router)

    # Include portfolio router if available
    if HAS_PORTFOLIO_ROUTER:
        app.include_router(portfolio.router)

    if HAS_PORTFOLIO_REVIEWS_ROUTER:
        app.include_router(portfolio_reviews.router)

    if HAS_WEALTHSIMPLE_IMPORT_ROUTER:
        app.include_router(wealthsimple_import.router)

    if HAS_MONARCH_IMPORT_ROUTER:
        app.include_router(monarch_import.router)

    if HAS_ADMIN_ROUTER:
        app.include_router(admin_api.router)

    if HAS_ACCOUNTS_ROUTER:
        app.include_router(accounts_api.router)

    if HAS_FX_ROUTER:
        app.include_router(fx_api.router)

    # Include integrations router if available
    if HAS_INTEGRATIONS_ROUTER:
        app.include_router(integrations.router)

    # Include insights router if available
    if HAS_INSIGHTS_ROUTER:
        app.include_router(insights.router)

    # Include assistant router if available
    if HAS_ASSISTANT_ROUTER:
        app.include_router(assistant.router)

    # Include budgets router if available
    if HAS_BUDGETS_ROUTER:
        app.include_router(budgets_api.router)

    # Include cashflow router if available
    if HAS_CASHFLOW_ROUTER:
        app.include_router(cashflow_api.router)

    # Include recurring patterns router if available
    if HAS_RECURRING_PATTERNS_ROUTER:
        app.include_router(recurring_patterns_api.router)

    # Include rules router if available
    if HAS_RULES_ROUTER:
        app.include_router(rules_api.router)

    return app


app = create_app()
