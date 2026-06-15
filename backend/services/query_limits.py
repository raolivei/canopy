"""Query safety limits to prevent OOM on large datasets."""

import logging
from functools import wraps
from time import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Safety limits
DEFAULT_QUERY_LIMIT = 1000
WARN_THRESHOLD_MS = 100
ERROR_THRESHOLD_MS = 5000


def warn_unbounded_query(method_name: str, row_count: int) -> None:
    """Log warning for queries that return large result sets."""
    if row_count > DEFAULT_QUERY_LIMIT:
        logger.warning(
            f"⚠️  PERFORMANCE: {method_name} returned {row_count} rows (limit: {DEFAULT_QUERY_LIMIT}). "
            f"Consider adding pagination or date filters."
        )


def log_slow_query(method_name: str, duration_ms: float) -> None:
    """Log warning for slow queries."""
    if duration_ms > WARN_THRESHOLD_MS:
        level = logger.error if duration_ms > ERROR_THRESHOLD_MS else logger.warning
        level(
            f"🐢 SLOW QUERY: {method_name} took {duration_ms:.0f}ms "
            f"(threshold: {WARN_THRESHOLD_MS}ms)"
        )


def monitored_query(func: Callable) -> Callable:
    """Decorator to monitor query performance and log warnings."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time()
        result = func(*args, **kwargs)
        duration_ms = (time() - start) * 1000

        # Log slow queries
        log_slow_query(func.__name__, duration_ms)

        # Warn on large result sets
        if isinstance(result, list):
            warn_unbounded_query(func.__name__, len(result))
        elif isinstance(result, dict) and "data" in result and isinstance(result["data"], list):
            warn_unbounded_query(func.__name__, len(result["data"]))

        return result

    return wrapper


def apply_safety_limit(query, limit: int = DEFAULT_QUERY_LIMIT):
    """Apply safety LIMIT to SQLAlchemy query if not already set."""
    if not hasattr(query, '_limit_clause') or query._limit_clause is None:
        logger.debug(f"Applying safety limit: {limit} rows")
        return query.limit(limit)
    return query
