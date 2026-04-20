"""Pydantic v2 request/response schemas.

These models form the public I/O contract of the FastAPI app. They are
intentionally split into three families:

1. **Auth schemas**      - signup/login payloads and the JWT token response.
2. **News schemas**      - shapes returned by the live NewsAPI-backed endpoints,
                           in both the detailed and the "formatted" (bulleted)
                           views.
3. **Saved schemas**     - CRUD + download shapes for articles the user has
                           chosen to persist.

All ORM-facing response models set `from_attributes=True` so they can be built
directly from SQLAlchemy instances via `Model.model_validate(obj)`.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl



class UserCreate(BaseModel):
    """Payload accepted by `POST /auth/signup`."""

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plain-text password; hashed server-side with bcrypt.",
    )


class UserRead(BaseModel):
    """Public view of a user. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    """JWT bearer token returned by `/auth/login`."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(
        description="Seconds until the access token expires.",
    )


class TokenPayload(BaseModel):
    """Decoded JWT claims. Used internally by `deps.get_current_user`."""

    sub: str
    exp: Optional[int] = None


# ---------------------------------------------------------------------------
# News (live, NewsAPI-backed)
# ---------------------------------------------------------------------------


class Article(BaseModel):
    """A single article in the detailed view.

    Mirrors the fields NewsAPI.org returns from `/top-headlines` and
    `/everything`, normalized to our preferred field names.
    """

    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = Field(
        default=None,
        description="Flattened source name (e.g. 'BBC News').",
    )
    author: Optional[str] = None
    url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = Field(
        default=None,
        description="NewsAPI `urlToImage`, renamed for clarity.",
    )
    published_at: Optional[datetime] = None
    category: Optional[str] = None


class FormattedArticle(BaseModel):
    """Condensed, bullet-style view built by `services.formatter`.

    This is what `GET /news/formatted` returns per article. The frontend
    renders `bullets` directly as a list.
    """

    title: str
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = Field(
        default=None,
        description="Lead image, mirrored from the underlying Article.image_url.",
    )
    summary: Optional[str] = Field(
        default=None,
        description="One-sentence summary (first sentence of description).",
    )
    keyphrases: List[str] = Field(
        default_factory=list,
        description="Top keyphrases extracted via YAKE.",
    )
    bullets: List[str] = Field(
        default_factory=list,
        description="Fully-rendered bullet lines, ready to display or export.",
    )


class NewsResponse(BaseModel):
    """Envelope returned by `GET /news`."""

    total_results: int = 0
    page: int = 1
    page_size: int = 20
    articles: List[Article] = Field(default_factory=list)


class FormattedNewsResponse(BaseModel):
    """Envelope returned by `GET /news/formatted`."""

    total_results: int = 0
    page: int = 1
    page_size: int = 20
    articles: List[FormattedArticle] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Saved articles
# ---------------------------------------------------------------------------


class SavedArticleBase(BaseModel):
    """Fields shared by create and read shapes for saved articles."""

    title: str = Field(min_length=1, max_length=512)
    description: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = Field(default=None, max_length=255)
    url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = Field(default=None, max_length=64)


class SavedArticleCreate(SavedArticleBase):
    """Payload for `POST /saved` - a snapshot of an article to persist."""

    starred: bool = False


class SavedArticleUpdate(BaseModel):
    """Payload for `PATCH /saved/{id}`. Currently only `starred` is mutable."""

    starred: Optional[bool] = None


class SavedArticleRead(SavedArticleBase):
    """Response shape for saved-article endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    starred: bool
    saved_at: datetime


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


class Message(BaseModel):
    """Simple `{"detail": "..."}` style response used for ad-hoc messages."""

    detail: str


DownloadFormat = Literal["txt", "pdf"]
DownloadStyle = Literal["detailed", "formatted"]


# ---------------------------------------------------------------------------
# Reading-activity / streaks
# ---------------------------------------------------------------------------


class ActivityPingResponse(BaseModel):
    """Returned by `POST /activity/ping` after a (possibly idempotent) record."""

    today: date
    recorded: bool = Field(
        description="True if this is the first ping today, False if the day was already counted."
    )
    current_streak: int
    longest_streak: int


class ActivityStats(BaseModel):
    """Returned by `GET /activity/stats` - drives the dashboard widgets."""

    today: date
    read_today: bool
    current_streak: int
    longest_streak: int
    days_this_month: int = Field(
        description="Distinct days the user opened the news this calendar month."
    )
    total_days: int = Field(description="Lifetime distinct days the user has opened the news.")
    last_30_days: List[date] = Field(
        description="The dates (within the last 30 days, today inclusive) on which the user read."
    )
