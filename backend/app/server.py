"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.routes import router as v1_router
from backend.app.config import get_settings

# Import transaction and currency routers if they exist
try:
    from backend.api import transactions, currency
    HAS_TRANSACTION_ROUTERS = True
except ImportError:
    HAS_TRANSACTION_ROUTERS = False


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version="0.1.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
    
    return app


app = create_app()

