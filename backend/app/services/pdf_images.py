"""Image fetching for PDF embedding.

Hero images add a magazine feel to the PDF exports. We download the image
synchronously inside the PDF build, validate the bytes via Pillow (through
ReportLab's `ImageReader`), and return a Platypus `Image` flowable sized to
fit a sane page region.

Failures (timeout, HTTP 4xx, non-image bytes, decode errors) all silently
return None so the rest of the document still renders.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

import httpx
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image

logger = logging.getLogger(__name__)


# Constraints that keep PDF builds fast and bounded - we never want a huge
# hero image or a slow CDN turning a download into a 30s wait.
_TIMEOUT_SECONDS = 6.0
_MAX_BYTES = 3 * 1024 * 1024  # 3 MB
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 CurrentAffairsApp/1.0"
)


def fetch_image_flowable(
    url: Optional[str],
    *,
    max_width_mm: float = 160.0,
    max_height_mm: float = 90.0,
) -> Optional[Image]:
    """Download `url` and return a ReportLab `Image` sized to fit the page.

    Returns None on any failure so the PDF still renders without the picture.
    The image is held entirely in memory; no temp file is touched on disk.
    """
    if not url or not isinstance(url, str):
        return None
    if not url.startswith(("http://", "https://")):
        return None

    try:
        with httpx.Client(
            timeout=_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            response = client.get(url)
    except httpx.HTTPError as exc:
        logger.info("PDF image fetch failed for %s: %s", url, exc)
        return None

    if response.status_code >= 400:
        logger.info("PDF image fetch returned %s for %s", response.status_code, url)
        return None

    data = response.content[:_MAX_BYTES]
    if not data:
        return None

    try:
        # Probe the bytes via PIL/ImageReader before handing them to a
        # Platypus Image flowable - this catches "url returned HTML" or
        # "format ReportLab can't read" without crashing the build.
        reader = ImageReader(io.BytesIO(data))
        intrinsic_w, intrinsic_h = reader.getSize()
        if intrinsic_w <= 0 or intrinsic_h <= 0:
            return None
    except Exception as exc:  # pragma: no cover - defensive
        logger.info("PDF image decode failed for %s: %s", url, exc)
        return None

    max_w = max_width_mm * mm
    max_h = max_height_mm * mm
    aspect = intrinsic_w / intrinsic_h
    draw_w = max_w
    draw_h = draw_w / aspect
    if draw_h > max_h:
        draw_h = max_h
        draw_w = draw_h * aspect

    try:
        return Image(io.BytesIO(data), width=draw_w, height=draw_h)
    except Exception as exc:  # pragma: no cover - defensive
        logger.info("PDF image embed failed for %s: %s", url, exc)
        return None
