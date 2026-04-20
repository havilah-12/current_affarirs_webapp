"""Service layer.

Pure helpers that routers depend on:

- `news_service`    : async client over NewsData.io.
- `formatter`       : turns a news article into a GK-style bullet list.
- `article_fetcher` : downloads + cleans the full body of an article from
                      its source URL (used for detailed PDF/TXT downloads).
- `exporter`        : renders one or more articles to .txt or .pdf.
- `pdf_fonts`       : registers Unicode TTF + ASCII fallbacks for ReportLab.
- `pdf_images`      : downloads + sizes hero images for PDF embedding.

These modules avoid FastAPI/SQLAlchemy imports where possible so they're
easy to unit-test in isolation. Routers stay thin and delegate here.
"""
