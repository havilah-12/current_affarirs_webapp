"""Database engine, session factory, and declarative base.

Provides the SQLAlchemy primitives that the rest of the backend uses:

- `engine`         : configured from `settings.DATABASE_URL` (SQLite by default).
- `SessionLocal`   : per-request session factory (used by `deps.get_db`).
- `Base`           : declarative base that ORM models inherit from.
- `init_db()`      : create all tables on startup (called from `main.py`).
"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


def _build_engine(database_url: str) -> Engine:
    """Create the SQLAlchemy engine with SQLite-friendly defaults.

    SQLite rejects cross-thread connection reuse by default, which breaks under
    FastAPI's thread pool. We relax that only for SQLite URLs so production
    databases (Postgres/MySQL) keep their stricter defaults.
    """
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        database_url,
        connect_args=connect_args,
        future=True,
    )


engine: Engine = _build_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def init_db() -> None:
    """Create any tables that do not yet exist and apply tiny additive migrations.

    Importing `.models` here (rather than at module top) avoids a circular
    import: `models` itself imports `Base` from this module.

    SQLite has no real migration story; rather than pull in Alembic for a
    single new column, we detect missing columns via the SQLAlchemy
    inspector and add them with a plain `ALTER TABLE`. This keeps existing
    user databases working across small schema bumps without forcing them
    to wipe the file.
    """
    from . import models  # noqa: F401  (import registers models on `Base.metadata`)

    Base.metadata.create_all(bind=engine)
    _apply_additive_migrations()


# Map of (table name) -> list of (column name, "ALTER TABLE ... ADD COLUMN ..." SQL).
# Only safe additive changes belong here.
_ADDITIVE_COLUMNS = {
    "saved_articles": [
        ("full_content", "ALTER TABLE saved_articles ADD COLUMN full_content TEXT"),
        (
            "full_content_fetched_at",
            "ALTER TABLE saved_articles ADD COLUMN full_content_fetched_at DATETIME",
        ),
    ],
    "reading_activity": [
        (
            "category",
            "ALTER TABLE reading_activity ADD COLUMN category VARCHAR(64)",
        ),
    ],
}


def _apply_additive_migrations() -> None:
    """Add any missing columns from `_ADDITIVE_COLUMNS` to existing tables."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in _ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                # `create_all` above already covers fresh databases.
                continue
            present = {col["name"] for col in inspector.get_columns(table)}
            for column_name, ddl in columns:
                if column_name not in present:
                    conn.execute(text(ddl))
