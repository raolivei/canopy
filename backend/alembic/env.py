"""Alembic environment configuration."""

from logging.config import fileConfig

# Register every table on Base.metadata. ``alembic check`` and autogenerate
# compare against this metadata, so a model that is not imported here looks
# like a table to drop.
import backend.db.models  # noqa: F401
import backend.db.models.assistant  # noqa: F401
import backend.db.models.category  # noqa: F401

# Import the app config to get the database URL
from backend.app.config import get_settings

# Declarative base whose metadata autogenerate compares against
from backend.db.base import Base
from sqlalchemy import engine_from_config, pool, text

from alembic import context

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from app settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Target metadata for autogenerate support
target_metadata = Base.metadata

# Session-level PostgreSQL advisory lock key ("canopy" as an int64). Every
# migration run holds it, so API pods that start together migrate one at a
# time; the later ones find the schema already at head and do nothing.
MIGRATION_LOCK_KEY = 0x63616E6F7079


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.  By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        use_lock = connection.dialect.name == "postgresql"
        if use_lock:
            # Blocks until no other migration run holds the lock. The lock
            # belongs to the session, so it outlives the commit below and is
            # released on unlock or when the connection closes (pod crash).
            connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": MIGRATION_LOCK_KEY})
            connection.commit()

        try:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )

            with context.begin_transaction():
                context.run_migrations()
        finally:
            if use_lock:
                connection.rollback()
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": MIGRATION_LOCK_KEY})
                connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
