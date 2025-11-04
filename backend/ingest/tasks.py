"""Background data ingestion tasks executed by Celery."""

from celery import Celery

from backend.app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ledgerlight_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task(name="ingest.import_csv")
def import_csv(file_path: str) -> str:
    """Placeholder CSV import task."""

    # TODO: replace with actual ingestion logic
    return f"CSV import queued for {file_path}"

