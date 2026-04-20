"""ReportLab font registration helpers.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


_UNICODE_FONT_NAME = "AppUnicode"
_UNICODE_FONT_BOLD = "AppUnicode-Bold"

_REGULAR_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
)

_BOLD_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
)


# Walks the given list of file paths and returns the first one that actually exists on disk (or None).
def _first_existing(paths: tuple[str, ...]) -> Optional[str]:
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


# Finds a Unicode-capable TTF font on the system and registers it with ReportLab so PDFs can show ₹, €, smart quotes, etc. Falls back to built-in Helvetica if nothing is found.
def _register_unicode_fonts() -> tuple[str, str]:
    """Register Unicode-capable fonts with ReportLab.

    Returns a `(regular_name, bold_name)` tuple. Bold falls back to the
    regular font name when no bold variant is available. When no usable TTF
    can be found anywhere on disk we degrade to ReportLab's bundled
    Helvetica family and rely on `to_pdf_safe_text` for transliteration.
    """
    regular_path = _first_existing(_REGULAR_FONT_CANDIDATES)
    bold_path = _first_existing(_BOLD_FONT_CANDIDATES)

    if not regular_path:
        logger.info(
            "No Unicode TTF found - PDF will use Helvetica with ASCII fallbacks "
            "(currency / quote glyphs may degrade)."
        )
        return ("Helvetica", "Helvetica-Bold")

    try:
        pdfmetrics.registerFont(TTFont(_UNICODE_FONT_NAME, regular_path))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to register PDF font %s: %s", regular_path, exc)
        return ("Helvetica", "Helvetica-Bold")

    bold_name = _UNICODE_FONT_NAME
    if bold_path:
        try:
            pdfmetrics.registerFont(TTFont(_UNICODE_FONT_BOLD, bold_path))
            bold_name = _UNICODE_FONT_BOLD
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to register PDF bold font %s: %s", bold_path, exc)

    return (_UNICODE_FONT_NAME, bold_name)


REGULAR_FONT, BOLD_FONT = _register_unicode_fonts()
HAS_UNICODE_FONT = REGULAR_FONT != "Helvetica"


_ASCII_FALLBACKS = {
    "\u20b9": "Rs.",  # Indian Rupee Sign
    "\u20ac": "EUR",  # Euro Sign
    "\u00a3": "GBP",  # Pound Sign
    "\u2014": "-",    # Em dash
    "\u2013": "-",    # En dash
    "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2026": "...",
    "\u00a0": " ",
}


# Replaces special characters (₹, €, smart quotes, em dashes, …) with plain ASCII ("Rs.", "EUR", '"', "-", "...") ONLY when we had to fall back to Helvetica. Keeps PDFs from showing empty boxes.
def to_pdf_safe_text(text: str) -> str:
    """Substitute glyphs that Helvetica can't render when no TTF is available."""
    if HAS_UNICODE_FONT or not text:
        return text
    return text.translate(str.maketrans(_ASCII_FALLBACKS))
