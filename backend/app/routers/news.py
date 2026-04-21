"""Live news endpoints backed by NewsData.io.

- `GET /news`           : detailed headline feed (titles, descriptions, content,
                          source, image, etc.) — this is what the SPA uses.
- `GET /news/formatted` : optional condensed "GK quick-read" view (YAKE
                          bullets) for the same filters; same auth rules.

Both accept the same query parameters.

Endpoints are protected by `get_current_user` because the upstream API key is
a paid resource we don't want exposed to anonymous callers.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..deps import get_current_user
from ..models import User
from ..schemas import FormattedNewsResponse, NewsResponse
from ..services import formatter, news_service
from ..services.news_service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


router = APIRouter(prefix="/news", tags=["news"])


# ---------------------------------------------------------------------------
# Query-parameter aliases (shared by both routes)
# ---------------------------------------------------------------------------

_CategoryQuery = Query(
    default=None,
    description=(
        "NewsData.io category. One of: business, crime, domestic, education, "
        "entertainment, environment, food, health, lifestyle, other, politics, "
        "science, sports, technology, top, tourism, world."
    ),
)
_CountryQuery = Query(
    default=None,
    description=(
        "ISO 3166-1 alpha-2 country code (e.g. 'in', 'us'). Defaults to the "
        "server's DEFAULT_COUNTRY setting when no other filter is provided."
    ),
    min_length=2,
    max_length=2,
)
_QueryQuery = Query(
    default=None,
    description="Free-text keyword to filter headlines (matches title/description/content).",
    max_length=500,
)
_QInTitleQuery = Query(
    default=None,
    alias="q_in_title",
    description=(
        "Free-text keyword that must appear in the article TITLE. Used by the "
        "frontend to enforce the Indian-state filter (e.g. q_in_title='Andhra "
        "Pradesh') so results are about the state, not just any article that "
        "happens to mention it."
    ),
    max_length=500,
)
_PageQuery = Query(default=1, ge=1, description="1-indexed page number.")
_PageSizeQuery = Query(
    default=DEFAULT_PAGE_SIZE,
    ge=1,
    le=MAX_PAGE_SIZE,
    description=f"Number of articles per page (max {MAX_PAGE_SIZE}).",
)
async def _fetch(
    *,
    category: Optional[str],
    country: Optional[str],
    q: Optional[str],
    q_in_title: Optional[str],
    page: int,
    page_size: int,
) -> NewsResponse:
    return await news_service.fetch_top_headlines(
        category=category,
        country=country,
        q=q,
        q_in_title=q_in_title,
        page=page,
        page_size=page_size,
    )


@router.get(
    "",
    response_model=NewsResponse,
    summary="Detailed news feed (NewsData.io-backed)",
)
async def get_news(
    category: Optional[str] = _CategoryQuery,
    country: Optional[str] = _CountryQuery,
    q: Optional[str] = _QueryQuery,
    q_in_title: Optional[str] = _QInTitleQuery,
    page: int = _PageQuery,
    page_size: int = _PageSizeQuery,
    _user: User = Depends(get_current_user),
) -> NewsResponse:
    """Fetch headlines from NewsData.io and return the detailed view."""
    raw = await _fetch(
        category=category,
        country=country,
        q=q,
        q_in_title=q_in_title,
        page=page,
        page_size=page_size,
    )
    # Keep `/news` as the detailed feed while also exposing lightweight
    # key-heading chips for the card UI.
    articles = [
        article.model_copy(
            update={"keyphrases": formatter.format_article(article).keyphrases}
        )
        for article in raw.articles
    ]
    return raw.model_copy(update={"articles": articles})


@router.get(
    "/formatted",
    response_model=FormattedNewsResponse,
    summary="Condensed 'GK quick-read' view of the same feed",
)
async def get_news_formatted(
    category: Optional[str] = _CategoryQuery,
    country: Optional[str] = _CountryQuery,
    q: Optional[str] = _QueryQuery,
    q_in_title: Optional[str] = _QInTitleQuery,
    page: int = _PageQuery,
    page_size: int = _PageSizeQuery,
    _user: User = Depends(get_current_user),
) -> FormattedNewsResponse:
    """Fetch headlines and transform each into a GK-style bullet list."""
    raw = await _fetch(
        category=category,
        country=country,
        q=q,
        q_in_title=q_in_title,
        page=page,
        page_size=page_size,
    )

    return FormattedNewsResponse(
        total_results=raw.total_results,
        page=raw.page,
        page_size=raw.page_size,
        articles=formatter.format_articles(raw.articles),
    )
