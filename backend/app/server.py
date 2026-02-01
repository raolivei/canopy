"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.routes import router as v1_router
from backend.app.config import get_settings

# Import transaction and currency routers if they exist
try:
    from backend.api import transactions, currency, csv_import
    HAS_TRANSACTION_ROUTERS = True
except ImportError:
    HAS_TRANSACTION_ROUTERS = False

# Import portfolio router
try:
    from backend.api import portfolio
    HAS_PORTFOLIO_ROUTER = True
except ImportError:
    HAS_PORTFOLIO_ROUTER = False

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
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include v1 router (health, summary endpoints)
    app.include_router(v1_router)
    
    # Include transaction and currency routers if available
    if HAS_TRANSACTION_ROUTERS:
        app.include_router(transactions.router)
        app.include_router(currency.router)
        app.include_router(csv_import.router)
    
    # Include portfolio router if available
    if HAS_PORTFOLIO_ROUTER:
        app.include_router(portfolio.router)
    
    # Include integrations router if available
    if HAS_INTEGRATIONS_ROUTER:
        app.include_router(integrations.router)
    
    # Include insights router if available
    if HAS_INSIGHTS_ROUTER:
        app.include_router(insights.router)
    
    return app


app = create_app()
