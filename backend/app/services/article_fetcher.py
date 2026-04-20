"""Fetch the full body of an article from its source URL.

Why this exists
---------------
NewsData.io's free tier returns very short snippets in the `content` field
(often a paragraph or even null). When the user downloads a saved article as
a PDF, that snippet is all we have unless we go back to the publisher and
read the actual page.

This module does exactly that:

  1. Download the URL with httpx (a sane User-Agent + timeouts + size cap).
  2. Run trafilatura's article-body extractor over the HTML, which
     identifies the main content block and strips chrome / nav / ads /
     boilerplate. Trafilatura is the de-facto best open-source extractor
     for news content.
  3. Return cleaned plain text broken into paragraphs by blank lines.

Failures are non-fatal: every code path returns `None` on any error so the
caller can fall back to whatever metadata it already has.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# Identify ourselves as a regular browser. Some publishers gate their HTML
# on a non-empty UA string and many ban known bot UAs.
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 CurrentAffairsApp/1.0"
)

# Caps to keep this from being abused as a download proxy.
_TIMEOUT_SECONDS = 12.0
_MAX_HTML_BYTES = 4 * 1024 * 1024  # 4 MB


def _fetch_html(url: str) -> Optional[str]:
    """Download the URL and return the decoded HTML body, or None on failure."""
    try:
        with httpx.Client(
            timeout=_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        logger.info("article fetch failed for %s: %s", url, exc)
        return None

    if response.status_code >= 400:
        logger.info("article fetch returned %s for %s", response.status_code, url)
        return None

    content = response.content[:_MAX_HTML_BYTES]
    encoding = response.encoding or response.charset_encoding or "utf-8"
    try:
        return content.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return content.decode("utf-8", errors="replace")


def fetch_full_article(url: Optional[str]) -> Optional[str]:
    """Return the cleaned article body text from `url`, or None on failure.

    Output is plain text with paragraphs separated by blank lines, suitable
    for direct rendering in a PDF / TXT exporter.
    """
    if not url or not isinstance(url, str):
        return None
    if not url.startswith(("http://", "https://")):
        return None

    html = _fetch_html(url)
    if not html:
        return None

    try:
        # Imported lazily so importing this module is cheap and so a
        # missing/broken trafilatura install doesn't take the whole app
        # down on startup - download just degrades to "no full content".
        import trafilatura
    except Exception as exc:  # pragma: no cover - defensive
        # Loud warning so a missing dependency doesn't masquerade as
        # "this article just doesn't have full content available".
        logger.warning(
            "trafilatura is not installed - full-article PDFs will only "
            "contain the URL. Run `pip install -r requirements.txt` in the "
            "backend venv to fix this. (import error: %s)",
            exc,
        )
        return None

    # Try the recall-friendly extraction first. `favor_precision=True` is
    # great for clean wire copy but tends to throw away anything with
    # heavy boilerplate (sidebars, pull-quotes, related links), which is
    # most of the modern Indian news web.
    extracted: Optional[str] = None
    for kwargs in (
        {"favor_recall": True},
        {"favor_precision": True},
        {},
    ):
        try:
            candidate = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                include_images=False,
                include_links=False,
                **kwargs,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.info("trafilatura extract failed for %s: %s", url, exc)
            continue
        if candidate and candidate.strip():
            extracted = candidate
            break

    if not extracted:
        return None

    cleaned = scrub_boilerplate(extracted.strip())
    # Reject only obvious paywall stubs ("Sign in to read the full article.")
    # rather than anything under 200 chars - some news briefs are legitimately
    # short but still much richer than NewsData's 200-char snippet.
    if len(cleaned) < 80:
        return None

    return cleaned


# ---------------------------------------------------------------------------
# Boilerplate scrubbing
# ---------------------------------------------------------------------------
#
# Trafilatura is good at finding the article body, but Indian-news pages
# love to wrap that body in noisy chrome that the extractor leaves intact:
#
#   * leading byline + dateline:  "- by B2B Desk 2020-09-14 05:59:37 In the..."
#   * trailing related-articles list:
#       "Also Read: Yes Bank repays ... - by Shan, 2025-11-05 09:57:37
#        - by Shan, 2025-11-05 10:29:23 ..."
#   * standalone "Source: <publisher>" footers.
#
# We scrub those *once*, before the cleaned body is cached in
# `SavedArticle.full_content`, so every subsequent download is already
# clean and we don't have to re-strip them at render time.

# Author byline at the very start of the article. We only strip when we're
# *certain* it's a byline and not the first words of a sentence - so we
# require either a dateline (YYYY-MM-DD ...) right after the author name
# OR an explicit separator (`-`, `|`, newline) signalling the end of the
# byline. A bare "By Reuters In a statement..." stays intact rather than
# risk swallowing actual content.
_LEADING_BYLINE_RE = re.compile(
    r"""
    \A                                       # start of text
    [\s\-\u2013\u2014\u2022|]*               # optional leading separators
    [Bb]y\s+
    [A-Z][A-Za-z0-9.&'\-]+                   # first name token (capitalised)
    (?:\s+[A-Z][A-Za-z0-9.&'\-]+){0,4}       # 0-4 more capitalised tokens
    (?:
        \s+\d{4}-\d{2}-\d{2}                 # YYYY-MM-DD dateline
        (?:[\sT]\d{1,2}:\d{2}(?::\d{2})?)?   # optional HH:MM(:SS)
        (?:\s*(?:UTC|IST|GMT|EDT|EST|PST|PDT))?
      |
        \s*[\-\u2013\u2014|]\s*              # explicit dash / pipe separator
      |
        \s*\n                                # or a newline
    )
    [\s\-\u2013\u2014:|,]*                   # trailing separators
    """,
    re.VERBOSE,
)

# Trailing chain of "- by Author, 2025-11-05 10:29:23" entries that some
# CMSes append as "more from this reporter" links. Matches one or more.
_TRAILING_BYLINE_LIST_RE = re.compile(
    r"""
    (?:
        [\s\-\u2013\u2014\u2022|]*
        [Bb]y\s+[A-Za-z][A-Za-z0-9.&'\-\s]{1,40}?
        ,?\s*\d{4}-\d{2}-\d{2}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?
        \s*
    )+
    \Z
    """,
    re.VERBOSE,
)

# "Also Read:" / "Read More:" / "Read Also:" related-article promos -
# everything from that marker to the end of the body is junk.
_ALSO_READ_RE = re.compile(
    r"\b(?:Also\s*Read|Read\s*Also|Read\s*More|Related|See\s*Also)\s*[:\-\u2013\u2014]\s*.*\Z",
    re.IGNORECASE | re.DOTALL,
)

# "Source: Publisher" stray footer (after Also Read removal). Only strips
# the trailing one - we keep mid-paragraph "Source: ..." attributions.
_TRAILING_SOURCE_RE = re.compile(
    r"\bSource\s*[:\-]\s*[^.\n]{1,80}\s*\Z",
    re.IGNORECASE,
)

# Collapse runs of 3+ newlines into a paragraph break.
_EXTRA_NEWLINES_RE = re.compile(r"\n{3,}")


def scrub_boilerplate(text: str) -> str:
    """Remove byline / dateline / "Also Read" boilerplate from extracted text."""
    if not text:
        return text

    text = _LEADING_BYLINE_RE.sub("", text, count=1).lstrip(" -\u2013\u2014:|\t")

    text = _ALSO_READ_RE.sub("", text)
    text = _TRAILING_BYLINE_LIST_RE.sub("", text)
    text = _TRAILING_SOURCE_RE.sub("", text)

    text = _EXTRA_NEWLINES_RE.sub("\n\n", text)
    return text.strip()
