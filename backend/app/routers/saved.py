"""CRUD + download endpoints for a user's saved articles.

Every endpoint here requires a valid JWT and is strictly scoped to the
calling user's rows - a user can never read or mutate another user's
saved articles.

Endpoints
---------
- `POST   /saved`                    : persist an article snapshot.
- `GET    /saved`                    : list the user's saved articles.
- `GET    /saved/{id}`               : read one saved article.
- `PATCH  /saved/{id}`               : toggle metadata (currently `starred`).
- `DELETE /saved/{id}`               : remove an entry.
- `GET    /saved/{id}/download`      : txt/pdf of one article (detailed/formatted).
- `GET    /saved/export`             : bulk txt/pdf of all saved articles.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import SavedArticle, User
from ..schemas import (
    DownloadFormat,
    DownloadStyle,
    Message,
    SavedArticleCreate,
    SavedArticleRead,
    SavedArticleUpdate,
)
from ..services import article_fetcher, exporter


router = APIRouter(prefix="/saved", tags=["saved"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_owned(
    db: Session,
    user: User,
    article_id: int,
) -> SavedArticle:
    """Fetch the article by id *and* verify the caller owns it."""
    article = db.get(SavedArticle, article_id)
    if article is None or article.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved article not found.",
        )
    return article


def _content_type_for(fmt: DownloadFormat) -> str:
    return "application/pdf" if fmt == "pdf" else "text/plain; charset=utf-8"


# Patterns that indicate a previously-cached `full_content` was stored
# *before* the boilerplate scrubber existed, and should be re-extracted so
# the user sees a clean download.
_DIRTY_CACHE_PATTERNS = (
    re.compile(r"\bAlso\s*Read\s*[:\-]", re.IGNORECASE),
    re.compile(r"^[\s\-\u2013\u2014\u2022|]*[Bb]y\s+[A-Z]"),
    re.compile(r"(?:[Bb]y\s+\w+,?\s+\d{4}-\d{2}-\d{2}[\s\d:]*\s*){2,}\Z"),
)


def _is_dirty_cached_content(body: Optional[str]) -> bool:
    if not body:
        return False
    return any(p.search(body) for p in _DIRTY_CACHE_PATTERNS)


def _ensure_full_content(
    db: Session,
    articles: Iterable[SavedArticle],
    *,
    style: DownloadStyle,
) -> None:
    """Lazily populate `SavedArticle.full_content` for download requests.

    For every article that has a URL but no cached `full_content`, fetch the
    source page and run trafilatura's article extractor over it. The result
    is committed back to the row so subsequent downloads are instant.

    Articles whose cached body still contains pre-scrubber boilerplate
    (byline + "Also Read" tail) are re-fetched so old downloads get the
    cleaned-up copy too.

    The "formatted" (quick-read) style only renders bullets, so we skip the
    network call there - it gains us nothing.
    """
    if style != "detailed":
        return

    dirty = False
    now = datetime.now(timezone.utc)
    for article in articles:
        cached = article.full_content
        cached_is_dirty = _is_dirty_cached_content(cached)
        needs_fetch = not cached or cached_is_dirty
        if not needs_fetch:
            continue

        body = (
            article_fetcher.fetch_full_article(article.url) if article.url else None
        )
        if body:
            article.full_content = body
            article.full_content_fetched_at = now
            dirty = True
        elif cached_is_dirty:
            # Re-fetch failed (publisher offline / blocked), but we still
            # don't want to render the old boilerplate-laden copy. Scrub
            # the cached body in place so the PDF is at least clean.
            scrubbed = article_fetcher.scrub_boilerplate(cached)
            if scrubbed and scrubbed != cached:
                article.full_content = scrubbed
                article.full_content_fetched_at = now
                dirty = True
    if dirty:
        db.commit()


def _build_download_response(
    *,
    payload: bytes,
    fmt: DownloadFormat,
    base_filename: str,
) -> Response:
    filename = exporter.safe_filename(base_filename, fmt)
    return Response(
        content=payload,
        media_type=_content_type_for(fmt),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SavedArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save an article snapshot for the current user",
)
def create_saved(
    payload: SavedArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedArticle:
    article = SavedArticle(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        content=payload.content,
        source=payload.source,
        url=str(payload.url) if payload.url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        published_at=payload.published_at,
        category=payload.category,
        starred=payload.starred,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.get(
    "",
    response_model=List[SavedArticleRead],
    summary="List all saved articles for the current user",
)
def list_saved(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    starred_only: bool = Query(
        default=False,
        description="If true, return only starred items.",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[SavedArticle]:
    stmt = select(SavedArticle).where(SavedArticle.user_id == current_user.id)
    if starred_only:
        stmt = stmt.where(SavedArticle.starred.is_(True))
    stmt = stmt.order_by(SavedArticle.saved_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


@router.get(
    "/export",
    summary="Download all saved articles as a single txt or pdf file",
    response_class=Response,
)
def export_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    format: DownloadFormat = Query(default="pdf"),
    style: DownloadStyle = Query(default="formatted"),
    starred_only: bool = Query(default=False),
) -> Response:
    """Bulk export of every saved article (or just the starred ones)."""
    stmt = select(SavedArticle).where(SavedArticle.user_id == current_user.id)
    if starred_only:
        stmt = stmt.where(SavedArticle.starred.is_(True))
    stmt = stmt.order_by(SavedArticle.saved_at.desc())

    articles = list(db.execute(stmt).scalars().all())
    _ensure_full_content(db, articles, style=style)

    if format == "pdf":
        payload = exporter.build_pdf(articles, style=style, title="Saved Current Affairs")
    else:
        payload = exporter.build_txt(articles, style=style)

    base = f"saved_{style}"
    return _build_download_response(payload=payload, fmt=format, base_filename=base)


@router.get(
    "/{article_id}",
    response_model=SavedArticleRead,
    summary="Read a single saved article",
)
def get_saved(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedArticle:
    return _load_owned(db, current_user, article_id)


@router.patch(
    "/{article_id}",
    response_model=SavedArticleRead,
    summary="Update a saved article (currently only `starred`)",
)
def update_saved(
    article_id: int,
    payload: SavedArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedArticle:
    article = _load_owned(db, current_user, article_id)

    if payload.starred is not None:
        article.starred = payload.starred

    db.commit()
    db.refresh(article)
    return article


@router.delete(
    "/{article_id}",
    response_model=Message,
    summary="Delete a saved article",
)
def delete_saved(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Message:
    article = _load_owned(db, current_user, article_id)
    db.delete(article)
    db.commit()
    return Message(detail="Saved article deleted.")


# ---------------------------------------------------------------------------
# Single-article download
# ---------------------------------------------------------------------------


@router.get(
    "/{article_id}/download",
    summary="Download one saved article as txt or pdf (detailed or formatted)",
    response_class=Response,
)
def download_saved(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    format: DownloadFormat = Query(default="pdf"),
    style: DownloadStyle = Query(default="detailed"),
) -> Response:
    article = _load_owned(db, current_user, article_id)
    _ensure_full_content(db, [article], style=style)

    if format == "pdf":
        payload = exporter.build_pdf([article], style=style, title=article.title)
    else:
        payload = exporter.build_txt([article], style=style)

    base_name = article.title or f"article_{article.id}"
    return _build_download_response(
        payload=payload,
        fmt=format,
        base_filename=f"{base_name}_{style}",
    )


__all__ = ["router"]
