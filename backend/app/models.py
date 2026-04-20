"""SQLAlchemy ORM models.

Three tables back the application:

- `users`              : registered accounts (email + bcrypt hash).
- `saved_articles`     : per-user snapshots of NewsAPI articles. We persist the
                         full article payload (title, description, content,
                         source, image, etc.) so downloads keep working even if
                         the original URL later 404s.
- `reading_activity`   : one row per (user, calendar day) the user opened the
                         news feed - drives the daily-streak gamification.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    """Timezone-aware UTC "now" used as a column default.

    Declared as a module-level function (rather than `datetime.utcnow`) so the
    stored values are timezone-aware and so SQLAlchemy calls it per-insert
    instead of freezing a single import-time value.
    """
    return datetime.now(timezone.utc)


class User(Base):
    """A registered end user who can save articles."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    saved_articles: Mapped[List["SavedArticle"]] = relationship(
        "SavedArticle",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reading_activity: Mapped[List["ReadingActivity"]] = relationship(
        "ReadingActivity",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return f"<User id={self.id} email={self.email!r}>"


class SavedArticle(Base):
    """A snapshot of a NewsAPI article that a user chose to keep.

    The full payload is stored (not just the URL) so that PDF/TXT exports
    remain reproducible even if the upstream article disappears.
    """

    __tablename__ = "saved_articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Lazily populated on first PDF/TXT download via the trafilatura-based
    # article fetcher. NewsData.io's free tier returns very short snippets in
    # `content`, so without this the downloaded PDF is mostly just metadata.
    full_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_content_fetched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    starred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="saved_articles")

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return (
            f"<SavedArticle id={self.id} user_id={self.user_id} "
            f"title={self.title!r}>"
        )


class ReadingActivity(Base):
    """One row per calendar day a user opened the news feed.

    The `(user_id, day)` uniqueness lets us idempotently `INSERT OR IGNORE`
    on every visit without bloating the table or needing a transaction-y
    upsert. `day` is stored as a plain DATE so streak/heatmap queries are
    trivial timezone-free comparisons.
    """

    __tablename__ = "reading_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_reading_activity_user_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="reading_activity")

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return f"<ReadingActivity user_id={self.user_id} day={self.day}>"
