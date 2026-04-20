"""Convert a raw news article into a GK-style bullet list.

The `Article -> FormattedArticle` transformation is the "quick read" view
that exam-prep students see when they flip the toggle in the UI. It is also
reused by the PDF/TXT exporter when `style="formatted"` is requested.

Implementation: rule-based extraction using YAKE for keyphrase mining.
YAKE is unsupervised, ships no model weights, and works reasonably on short
news snippets.

Keep this module dependency-light and deterministic so it stays fast in
the request path.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable, List, Optional

import yake

from ..schemas import Article, FormattedArticle


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE_RE = re.compile(r"\s+")
_NEWSAPI_TRUNCATION_RE = re.compile(r"\[\+\d+\s*chars\]\s*$")

DEFAULT_MAX_KEYPHRASES = 5
DEFAULT_NGRAM = 3  # allow uni-, bi-, and tri-grams (e.g. "Reserve Bank of India")


@lru_cache(maxsize=1)
def _extractor() -> yake.KeywordExtractor:
    """Return a cached YAKE extractor. Creating one is cheap but not free."""
    return yake.KeywordExtractor(
        lan="en",
        n=DEFAULT_NGRAM,
        dedupLim=0.7,
        top=20,  # request more than we need; we'll filter + trim downstream
        features=None,
    )


def _clean_text(raw: Optional[str]) -> str:
    """Collapse whitespace and strip NewsAPI's `[+123 chars]` truncation marker."""
    if not raw:
        return ""
    text = _NEWSAPI_TRUNCATION_RE.sub("", raw).strip()
    return _WHITESPACE_RE.sub(" ", text)


def _split_sentences(text: str, *, limit: int) -> List[str]:
    """Split `text` into up to `limit` non-empty sentences, in order."""
    text = text.strip()
    if not text:
        return []
    pieces = _SENTENCE_SPLIT_RE.split(text)
    sentences: List[str] = []
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        sentences.append(piece)
        if len(sentences) >= limit:
            break
    return sentences


def _dedup_preserving_order(items: Iterable[str]) -> List[str]:
    """De-duplicate strings case-insensitively while preserving first-seen order."""
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        key = item.casefold()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _extract_keyphrases(text: str, limit: int = DEFAULT_MAX_KEYPHRASES) -> List[str]:
    """Pull the top keyphrases from `text` using YAKE (lower score = better)."""
    if not text.strip():
        return []

    try:
        ranked = _extractor().extract_keywords(text)
    except Exception:
        # YAKE occasionally trips on short / punctuation-heavy strings.
        # Fail soft - formatted view still works, just without keyphrases.
        return []

    ranked.sort(key=lambda item: item[1])
    phrases = [phrase for phrase, _score in ranked if phrase and phrase.strip()]
    return _dedup_preserving_order(phrases)[:limit]


def _render_bullets(sentences: List[str]) -> List[str]:
    """Return the user-visible bullet lines (body sentences only).

    The card UI already renders title, source, date, category, keyphrase chips
    and a "Read more" link separately, so we keep the bullets focused on
    genuine summary content. Case-insensitive de-dup preserves order.
    """
    return _dedup_preserving_order(s for s in sentences if s and s.strip())


MAX_BODY_BULLETS = 3


def format_article(article: Article) -> FormattedArticle:
    """Transform a detailed `Article` into a condensed `FormattedArticle`."""
    title_clean = _clean_text(article.title) or article.title
    description_clean = _clean_text(article.description)
    content_clean = _clean_text(article.content)

    # Use description if available, otherwise fall back to content, for both
    # summarisation and keyphrase mining.
    body_text = description_clean or content_clean

    body_sentences = _split_sentences(body_text, limit=MAX_BODY_BULLETS)
    summary = body_sentences[0] if body_sentences else None

    keyphrase_corpus = " ".join(part for part in [title_clean, body_text] if part)
    keyphrases = _extract_keyphrases(keyphrase_corpus)

    bullets = _render_bullets(body_sentences)

    return FormattedArticle(
        title=title_clean,
        source=article.source,
        published_at=article.published_at,
        category=article.category,
        url=article.url,
        image_url=article.image_url,
        summary=summary,
        keyphrases=keyphrases,
        bullets=bullets,
    )


def format_articles(articles: Iterable[Article]) -> List[FormattedArticle]:
    """Vectorised convenience wrapper around `format_article`."""
    return [format_article(a) for a in articles]
