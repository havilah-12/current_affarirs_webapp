"""NewsData.io client.

Responsibilities:

- Talk to NewsData.io's `/latest` endpoint (https://newsdata.io/documentation).
  The same endpoint serves both our "top headlines" and "broad keyword search"
  use-cases; the difference is whether we pass a `q` parameter.
- Normalise each article into the internal `Article` Pydantic model so the
  rest of the app is insulated from NewsData.io's field names (`link`,
  `pubDate`, `image_url`, list-valued `creator` / `category`, etc.).
- Surface upstream errors as `HTTPException`s with sane status codes so the
  router layer can let them propagate unchanged.

NewsData.io's top-headlines category vocabulary (far richer than NewsAPI's):
    business, crime, domestic, education, entertainment, environment, food,
    health, lifestyle, other, politics, science, sports, technology, top,
    tourism, world.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

from ..config import settings
from ..schemas import Article, NewsResponse



DESCRIPTION_MAX_WORDS = 38
CONTENT_MAX_WORDS = 80


# Regexes used by `_clean_text`. Compiled once at import time.
_TAG_RE = re.compile(r"<[^>]+>")  # any HTML/XML tag
# NewsData.io occasionally leaks the raw RSS/atom container fragments below
# (e.g. "<content:encoded>", "<![CDATA[", "]]>"). Match them as literal text
# leftovers, which `_TAG_RE` may not catch when only one half of the bracket
# survives.
_RSS_ARTIFACT_RE = re.compile(
    r"<\s*/?\s*(content:encoded|description|item|rss|channel|atom[^>]*)>?",
    re.IGNORECASE,
)
_CDATA_RE = re.compile(r"<!\[CDATA\[|\]\]>")
# NewsAPI used to truncate with `[+1234 chars]`; NewsData.io occasionally
# does the same plus generic `[…]` ellipses. Trim them.
_TRUNCATION_RE = re.compile(r"\[\s*(\+?\d+\s*chars|…|\.{3})\s*\]\s*$")
_WS_RE = re.compile(r"\s+")


SUPPORTED_CATEGORIES = {
    "business",
    "crime",
    "domestic",
    "education",
    "entertainment",
    "environment",
    "food",
    "health",
    "lifestyle",
    "other",
    "politics",
    "science",
    "sports",
    "technology",
    "top",
    "tourism",
    "world",
}

# NewsData.io's `size` parameter is capped at 10 on the free tier and 50 on
# paid tiers. Sending a value above the tier's limit returns HTTP 422
# ("The size provided is invalid"), so we clamp to the safe free-tier value
# by default. Override MAX_PAGE_SIZE if you're on a paid plan.
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 10
HTTP_TIMEOUT = 10.0


def _require_api_key() -> str:
    """Return the configured NewsData.io key or raise a 503 if it's missing."""
    key = settings.news_api_key
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "NEWSDATA_API_KEY is not configured on the server. "
                "Set it in the backend .env file (get one at https://newsdata.io)."
            ),
        )
    return key


def _parse_published_at(raw: Optional[str]) -> Optional[datetime]:
    """Parse NewsData.io's `pubDate` (e.g. '2024-01-15 12:34:56', UTC).

    NewsData.io ships timestamps **in UTC** but without an explicit timezone
    marker, which Python parses into a *naive* datetime. We attach
    `tzinfo=UTC` so the JSON the frontend receives includes the offset
    (`...+00:00`) - otherwise `new Date(...)` in the browser interprets the
    string as local time and articles can show up labelled with the wrong
    date (e.g. an article published at 22:00 UTC would display as
    "yesterday" in IST).
    """
    if not raw or not isinstance(raw, str):
        return None
    parsed: Optional[datetime] = None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        # Some responses use a 'T' separator; swap and retry once.
        try:
            parsed = datetime.fromisoformat(raw.replace("T", " "))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _coerce_url(value: Any) -> Optional[str]:
    """Only return strings that look like http(s) URLs; Pydantic validates."""
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    return None


def _clean_text(raw: Any) -> Optional[str]:
    """Sanitise a free-text field from NewsData.io for safe UI rendering.

    Steps:
      1. Drop RSS/atom container leftovers (`<content:encoded>`, `<![CDATA[`).
      2. Strip remaining HTML/XML tags.
      3. HTML-decode entities (`&amp;`, `&#8217;`, ...).
      4. Strip the `[+123 chars]` / `[…]` truncation markers some feeds add.
      5. Collapse runs of whitespace.

    Returns `None` for empty / non-string input so downstream code can keep
    using truthiness checks unchanged.
    """
    if not isinstance(raw, str):
        return None
    text = _CDATA_RE.sub(" ", raw)
    text = _RSS_ARTIFACT_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _TRUNCATION_RE.sub("", text)
    text = _WS_RE.sub(" ", text).strip()
    return text or None


def _truncate_words(text: Optional[str], max_words: int) -> Optional[str]:
    """Clamp `text` to `max_words` words, appending an ellipsis if cut.

    Word-boundary truncation (rather than character-count) keeps the result
    readable - we never split a word in half. Pairs with the frontend
    `line-clamp` so card bodies are visually uniform.
    """
    if not text:
        return text
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(",;:.-") + "..."


def _first_of(value: Any) -> Optional[str]:
    """Return `value[0]` for list values, `value` for strings, else None.

    Several NewsData.io fields (`creator`, `category`, `country`, `keywords`)
    come back as lists. We flatten to the first entry.
    """
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return item.strip()
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _category_values(value: Any) -> List[str]:
    """Return normalized category tokens from a string/list category field."""
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                out.append(item.strip().lower())
        return out
    if isinstance(value, str) and value.strip():
        return [value.strip().lower()]
    return []


def _normalize_article(raw: Dict[str, Any], requested_category: Optional[str]) -> Optional[Article]:
    """Convert one raw NewsData.io article dict into our `Article` schema.

    Description and content are cleaned (HTML stripped, entities decoded,
    RSS leftovers removed) and clamped to a fixed word count so cards
    render at uniform heights in the UI.
    """
    title = _clean_text(raw.get("title"))
    if not title:
        return None

    source_name = (
        raw.get("source_name")
        or raw.get("source_id")
        or None
    )
    if isinstance(source_name, str):
        source_name = source_name.strip() or None

    description = _truncate_words(_clean_text(raw.get("description")), DESCRIPTION_MAX_WORDS)
    content = _truncate_words(_clean_text(raw.get("content")), CONTENT_MAX_WORDS)

    raw_categories = _category_values(raw.get("category"))
    # NewsData can occasionally return mixed-category rows even when category is
    # requested. Enforce strict category matching server-side for UI correctness.
    if requested_category and requested_category not in raw_categories:
        return None

    try:
        return Article(
            title=title,
            description=description,
            content=content,
            source=source_name,
            author=_first_of(raw.get("creator")),
            url=_coerce_url(raw.get("link")),
            image_url=_coerce_url(raw.get("image_url")),
            published_at=_parse_published_at(raw.get("pubDate")),
            category=requested_category or _first_of(raw.get("category")),
        )
    except Exception:
        # Defensive: one bad row shouldn't sink the whole response.
        return None


def _clamp_page_size(page_size: Optional[int]) -> int:
    if page_size is None:
        return DEFAULT_PAGE_SIZE
    return max(1, min(page_size, MAX_PAGE_SIZE))


def _validate_category(category: Optional[str]) -> Optional[str]:
    if not category:
        return None
    cat = category.strip().lower()
    if cat not in SUPPORTED_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported category {cat!r}. "
                f"Must be one of: {sorted(SUPPORTED_CATEGORIES)}."
            ),
        )
    return cat


def _build_params(
    *,
    category: Optional[str],
    country: Optional[str],
    q: Optional[str],
    q_in_title: Optional[str] = None,
    page_size: int,
    language: Optional[str] = "en",
) -> Dict[str, Any]:
    """Assemble query params for NewsData.io `/latest`.

    `q_in_title` maps to NewsData.io's `qInTitle` parameter, which restricts
    the keyword search to the article title only. We use it for the state
    filter so picking "Andhra Pradesh" returns articles primarily *about*
    AP rather than any story that just mentions it in passing.

    NOTE: `timeframe` and `from_date`/`to_date` are NOT used here because
    NewsData.io's free tier rejects them with HTTP 422 ("Access Denied!
    To use the timeframe parameter, please upgrade your plan"). If/when
    the deployment moves to a paid plan, re-introduce them here and at
    the router layer.
    """
    params: Dict[str, Any] = {
        "apikey": _require_api_key(),
        "size": page_size,
    }
    if language:
        params["language"] = language

    cat = _validate_category(category)
    if cat:
        params["category"] = cat

    has_any_query = bool((q and q.strip()) or (q_in_title and q_in_title.strip()))

    if country is not None:
        country_norm = country.strip().lower()
        if country_norm:
            params["country"] = country_norm
    elif not has_any_query and "category" not in params:
        # No hints at all - fall back to the configured default country so
        # the result set is at least geographically scoped.
        params["country"] = settings.DEFAULT_COUNTRY

    if q:
        q_clean = q.strip()
        if q_clean:
            # NewsData.io's `q` searches title + description + content.
            params["q"] = q_clean

    if q_in_title:
        qit_clean = q_in_title.strip()
        if qit_clean:
            params["qInTitle"] = qit_clean

    return params


async def _get_json(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Issue a GET against NewsData.io and return the parsed JSON body."""
    url = f"{settings.NEWSDATA_BASE_URL.rstrip('/')}/{path.lstrip('/')}"

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(url, params=params)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="NewsData.io request timed out.",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"NewsData.io request failed: {exc}",
        )

    if response.status_code >= 400:
        # NewsData.io error bodies look like:
        #   {"status":"error","results":{"code":"Unauthorized","message":"..."}}
        message: str
        try:
            payload = response.json()
            err = payload.get("results") if isinstance(payload, dict) else None
            if isinstance(err, dict):
                message = err.get("message") or err.get("code") or response.text
            else:
                message = payload.get("message") if isinstance(payload, dict) else response.text
                message = message or response.text
        except ValueError:
            message = response.text
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"NewsData.io error ({response.status_code}): {message}",
        )

    try:
        body = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="NewsData.io returned a non-JSON response.",
        )

    # NewsData.io wraps errors even on HTTP 200 sometimes:
    #   {"status":"error","results":{"message": "..."}}.
    if isinstance(body, dict) and body.get("status") == "error":
        err = body.get("results") if isinstance(body.get("results"), dict) else {}
        message = err.get("message") or err.get("code") or "unknown error"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"NewsData.io error: {message}",
        )

    return body


async def fetch_top_headlines(
    *,
    category: Optional[str] = None,
    country: Optional[str] = None,
    q: Optional[str] = None,
    q_in_title: Optional[str] = None,
    page: Optional[int] = 1,  # accepted for router compatibility; see note below
    page_size: Optional[int] = DEFAULT_PAGE_SIZE,
) -> NewsResponse:
    """Fetch the latest headlines from NewsData.io.

    Note on pagination: NewsData.io uses an opaque `nextPage` token rather
    than 1-indexed pages. We currently only expose the first page to keep the
    router contract simple. If/when deeper paging is needed, a follow-up can
    thread the token through the `page` query parameter.
    """
    page_size_i = _clamp_page_size(page_size)
    params = _build_params(
        category=category,
        country=country,
        q=q,
        q_in_title=q_in_title,
        page_size=page_size_i,
    )
    body = await _get_json("latest", params)

    raw_articles: List[Dict[str, Any]] = body.get("results") or []
    articles: List[Article] = []
    for raw in raw_articles:
        if not isinstance(raw, dict):
            continue
        normalised = _normalize_article(raw, requested_category=params.get("category"))
        if normalised is not None:
            articles.append(normalised)

    return NewsResponse(
        total_results=int(body.get("totalResults") or len(articles)),
        page=1,
        page_size=page_size_i,
        articles=articles,
    )
