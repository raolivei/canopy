"""Public API endpoints for version 1."""

from fastapi import APIRouter

from backend.app.config import get_settings

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/health", summary="Service health check")
def health() -> dict[str, str]:
    """Return basic health information for the service."""

    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/summary", summary="Readable status of core subsystems")
def summary() -> dict[str, dict[str, str]]:
    """Provide placeholder summary data until real integrations land."""

    return {
        "portfolio": {"status": "pending", "detail": "Awaiting data ingestion"},
        "budget": {"status": "pending", "detail": "No transactions ingested yet"},
        "ingest": {"status": "idle", "detail": "Celery workers not yet configured"},
    }

