"""Render saved articles to downloadable files.

This module only affects **saved-article exports** (`GET /saved/.../download` and
`GET /saved/export`). It does not control the live news feed on the home page.

Two output formats are supported for a single, normal export layout:

                 | normal export
    -------------+-----------------------------
    format="txt" | full title + body + meta
    format="pdf" | paragraphed PDF of the same

`build_txt` / `build_pdf` both accept one *or more* articles so the same
code path powers both `GET /saved/{id}/download` and the bulk `GET /saved/export`
endpoint.

Sub-modules:
    pdf_fonts  - Unicode TrueType registration + ASCII fallbacks.
    pdf_images - hero-image fetching and Image-flowable creation.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Sequence

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from ..models import SavedArticle
from .pdf_fonts import BOLD_FONT, REGULAR_FONT, to_pdf_safe_text
from .pdf_images import fetch_image_flowable


# ---------------------------------------------------------------------------
# Adapter: SavedArticle (ORM row) -> _ExportArticle (display-ready dataclass)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ExportArticle:
    """A display-ready view of a saved row, independent of the ORM.

    `full_content` (when present) is the trafilatura-extracted body of the
    article and takes precedence over the short `content` snippet for the
    detailed view.
    """

    title: str
    description: Optional[str]
    content: Optional[str]
    full_content: Optional[str]
    source: Optional[str]
    author: Optional[str]
    url: Optional[str]
    image_url: Optional[str]
    published_at: Optional[datetime]
    category: Optional[str]


def _saved_to_export(article: SavedArticle) -> _ExportArticle:
    return _ExportArticle(
        title=article.title,
        description=article.description,
        content=article.content,
        full_content=getattr(article, "full_content", None),
        source=article.source,
        author=None,  # not persisted on SavedArticle
        url=article.url,
        image_url=article.image_url,
        published_at=article.published_at,
        category=article.category,
    )


def _normalize_inputs(
    articles: Iterable[SavedArticle | _ExportArticle],
) -> List[_ExportArticle]:
    out: List[_ExportArticle] = []
    for a in articles:
        if isinstance(a, SavedArticle):
            out.append(_saved_to_export(a))
        elif isinstance(a, _ExportArticle):
            out.append(a)
        else:  # pragma: no cover - defensive
            raise TypeError(f"Unsupported article type: {type(a).__name__}")
    return out


# ---------------------------------------------------------------------------
# Filename + body helpers (shared by TXT and PDF renderers)
# ---------------------------------------------------------------------------


_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(base: str, extension: str) -> str:
    """Return a filesystem-safe filename based on `base` + `.extension`."""
    slug = _FILENAME_SAFE_RE.sub("_", base).strip("._-") or "article"
    # Keep the slug short so Content-Disposition headers don't explode.
    return f"{slug[:80]}.{extension.lstrip('.')}"


def _format_date_human(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    try:
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return None


def _split_paragraphs(text: str) -> List[str]:
    """Break trafilatura-style text on blank lines into separate paragraphs.

    Any run of one-or-more blank lines is treated as a paragraph break.
    """
    pieces = re.split(r"\n\s*\n+|\r\n\s*\r\n+", text.strip())
    return [p.strip() for p in pieces if p and p.strip()]


def _detailed_body_blocks(article: _ExportArticle) -> List[str]:
    """Return the paragraphs that make up the body of a detailed export.

    Preference order:
      1. `full_content` (trafilatura-extracted from the source URL).
      2. The short `content` snippet from NewsData.io.
      3. The even-shorter `description` snippet.
    """
    if article.full_content and article.full_content.strip():
        return _split_paragraphs(article.full_content)

    blocks: List[str] = []
    if article.description and article.description.strip():
        blocks.append(article.description.strip())
    if article.content and article.content.strip():
        # Only add `content` if it's not just a near-duplicate of description.
        if not blocks or article.content.strip() != blocks[0]:
            blocks.append(article.content.strip())
    return blocks


# ---------------------------------------------------------------------------
# TXT renderer
# ---------------------------------------------------------------------------


def _txt_detailed(article: _ExportArticle) -> str:
    lines: List[str] = []
    lines.append(article.title)
    lines.append("=" * min(80, max(10, len(article.title))))
    lines.append("")

    meta_parts: List[str] = []
    if article.source:
        meta_parts.append(f"Source: {article.source}")
    if article.category:
        meta_parts.append(f"Category: {article.category.capitalize()}")
    published = _format_date_human(article.published_at)
    if published:
        meta_parts.append(f"Published: {published}")
    if meta_parts:
        lines.append(" | ".join(meta_parts))
        lines.append("")

    for block in _detailed_body_blocks(article):
        lines.append(block)
        lines.append("")

    if article.url:
        lines.append(f"Read more: {article.url}")

    return "\n".join(lines).rstrip() + "\n"


def build_txt(
    articles: Sequence[SavedArticle | _ExportArticle],
) -> bytes:
    """Render one or more articles to a UTF-8 encoded `.txt` payload."""
    items = _normalize_inputs(articles)
    if not items:
        return b"No articles.\n"

    separator = "\n" + ("-" * 80) + "\n\n"
    body = separator.join(_txt_detailed(a) for a in items)
    return body.encode("utf-8")


# ---------------------------------------------------------------------------
# PDF renderer
# ---------------------------------------------------------------------------


def _pdf_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ArticleTitle",
            parent=base["Heading1"],
            fontName=BOLD_FONT,
            fontSize=18,
            leading=22,
            spaceAfter=6,
            alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "ArticleMeta",
            parent=base["Normal"],
            fontName=REGULAR_FONT,
            fontSize=9,
            textColor="#555555",
            leading=12,
            spaceAfter=12,
        ),
        "body": ParagraphStyle(
            "ArticleBody",
            parent=base["BodyText"],
            fontName=REGULAR_FONT,
            fontSize=11,
            leading=15,
            spaceAfter=10,
        ),
        "link": ParagraphStyle(
            "ArticleLink",
            parent=base["Normal"],
            fontName=REGULAR_FONT,
            fontSize=9,
            textColor="#1a4b8c",
            leading=12,
            spaceBefore=6,
        ),
    }


def _escape_pdf(text: str) -> str:
    """Sanitize text for ReportLab's Paragraph mini-HTML parser.

    Two passes:
      1. ASCII fallback for glyphs Helvetica can't render (only applied
         when no Unicode TTF was registered at startup).
      2. XML-escape `<`, `>`, `&` so the mini-HTML parser doesn't choke.
    """
    text = to_pdf_safe_text(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _pdf_meta_paragraph(parts: List[str], styles) -> Optional[Paragraph]:
    """Join meta parts with a separator and return a Paragraph (or None if empty)."""
    if not parts:
        return None
    return Paragraph(" &nbsp;|&nbsp; ".join(parts), styles["meta"])


def _pdf_flowables_detailed(article: _ExportArticle, styles) -> list:
    flow: list = [Paragraph(_escape_pdf(article.title), styles["title"])]

    meta_parts: List[str] = []
    if article.source:
        meta_parts.append(f"Source: {_escape_pdf(article.source)}")
    if article.category:
        meta_parts.append(f"Category: {_escape_pdf(article.category.capitalize())}")
    published = _format_date_human(article.published_at)
    if published:
        meta_parts.append(f"Published: {_escape_pdf(published)}")
    meta = _pdf_meta_paragraph(meta_parts, styles)
    if meta:
        flow.append(meta)

    # Hero image (if available) right under the metadata line so it reads
    # like a magazine spread. Network failures degrade silently.
    hero = fetch_image_flowable(article.image_url)
    if hero is not None:
        flow.append(hero)
        flow.append(Spacer(1, 8))

    # Each body paragraph becomes its own Paragraph flowable so the PDF
    # actually paragraph-breaks (ReportLab won't insert blank lines for
    # `\n\n` inside a single Paragraph).
    for block in _detailed_body_blocks(article):
        flow.append(Paragraph(_escape_pdf(block), styles["body"]))

    if article.url:
        escaped_url = _escape_pdf(article.url)
        flow.append(
            Paragraph(
                f'Source: <link href="{escaped_url}">{escaped_url}</link>',
                styles["link"],
            )
        )

    return flow


def build_pdf(
    articles: Sequence[SavedArticle | _ExportArticle],
    *,
    title: str = "Current Affairs",
) -> bytes:
    """Render one or more articles to a PDF and return the raw bytes."""
    items = _normalize_inputs(articles)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Current Affairs API",
    )
    styles = _pdf_styles()
    flowables: list = []

    if not items:
        flowables.append(Paragraph("No articles.", styles["body"]))
    else:
        for idx, article in enumerate(items):
            flowables.extend(_pdf_flowables_detailed(article, styles))
            if idx != len(items) - 1:
                flowables.append(Spacer(1, 12))
                flowables.append(PageBreak())

    doc.build(flowables)
    return buffer.getvalue()
