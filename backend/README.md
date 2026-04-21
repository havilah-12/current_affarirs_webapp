# Current Affairs — Backend

FastAPI backend for a current-affairs / GK study webapp. It pulls live
headlines from [NewsData.io](https://newsdata.io), serves a detailed feed on
`GET /news` (what the SPA uses), optionally exposes a YAKE bullet view on
`GET /news/formatted`, lets signed-in users bookmark articles, tracks a daily
reading streak, and serves saved rows as `.txt` or `.pdf` downloads.

The React + Vite + Tailwind frontend lives in [`../frontend`](../frontend).
For Docker and one-command startup, see the repo root [`readme.md`](../readme.md).

---

## Stack

- **FastAPI** (Python 3.10+) — web framework
- **SQLAlchemy 2.x** + **SQLite** — ORM + storage
- **Pydantic v2** + **pydantic-settings** — schemas + config
- **python-jose** + **bcrypt** — JWT auth + password hashing
- **httpx** — async HTTP client for NewsData.io
- **YAKE** — unsupervised keyphrase extraction for the "formatted" view
- **trafilatura** — optional full-article fetch when saving (see `article_fetcher`)
- **reportlab** + **pillow** — PDF export and embedded images

---

## Project layout

```text
backend/
  requirements.txt
  .env.example
  app/
    __init__.py
    config.py             # Settings (reads .env; NEWSDATA_API_KEY + legacy NEWSAPI_KEY)
    database.py           # engine, SessionLocal, Base, init_db()
    models.py             # User, SavedArticle, ReadingActivity
    schemas.py            # Pydantic request/response models
    security.py           # bcrypt + JWT helpers
    deps.py               # get_db, get_current_user
    services/
      news_service.py     # NewsData.io client (/latest, normalised Article model)
      formatter.py        # Article -> bullet list (YAKE keyphrases)
      article_fetcher.py  # Full-body fetch + scrub when saving
      exporter.py         # Article(s) -> .txt / .pdf
      pdf_fonts.py        # PDF typography helpers
      pdf_images.py       # PDF image helpers
    routers/
      auth.py             # /auth/signup, /auth/login, /auth/me
      news.py             # /news, /news/formatted
      saved.py            # /saved CRUD + download + export
      activity.py         # /activity/ping, /activity/stats (streak)
    main.py               # FastAPI app factory
```

---

## Quick start

### 1. Create a virtual environment

**Windows (PowerShell):**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

- **`NEWSDATA_API_KEY`** — free dev key from <https://newsdata.io/register>  
  (`NEWSAPI_KEY` is still read as a **legacy alias** for the same value; prefer `NEWSDATA_API_KEY`.)
- **`JWT_SECRET`** — long random string, e.g.:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

Optional (see `.env.example`):

- **`JWT_ALGORITHM`**, **`JWT_EXPIRE_MINUTES`**
- **`DEFAULT_COUNTRY`** — ISO 3166-1 alpha-2 default when filters omit country (default `in`).
- **`CORS_ORIGINS`** — comma-separated frontend origins.
- **`DATABASE_URL`** — defaults to `sqlite:///./current_affairs.db`.

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

- Root:            <http://localhost:8000/>
- Swagger UI:      <http://localhost:8000/docs>
- ReDoc:           <http://localhost:8000/redoc>
- Health probe:    <http://localhost:8000/health>

On first start, `init_db()` creates the SQLite schema. The DB file path comes from `DATABASE_URL` (by default next to the working directory when you run uvicorn, typically `backend/`).

---

## API overview

These groups require a JWT as **`Authorization: Bearer <token>`**:

- `/news/*`
- `/saved/*`
- `/activity/*`

Auth routes are public (signup/login) except **`GET /auth/me`**, which requires a valid JWT.

### Auth

| Method | Path           | Body / Form                        | Notes                                 |
|--------|----------------|-------------------------------------|---------------------------------------|
| POST   | `/auth/signup` | JSON `{email, password}`            | Creates the user, returns a JWT.      |
| POST   | `/auth/login`  | Form `username` (email), `password` | OAuth2 password flow. Returns a JWT.  |
| GET    | `/auth/me`     | —                                   | Returns the current user (JWT).     |

### News (NewsData.io-backed)

| Method | Path               | Query params | Notes |
|--------|--------------------|--------------|-------|
| GET    | `/news`            | `category`, `country`, `q`, `q_in_title`, `page`, `page_size` | Detailed feed (cleaned passthrough). |
| GET    | `/news/formatted`  | same                                                          | Same filters; each article passed through `formatter.format_articles` (optional; not used by the SPA). |

**Categories** (NewsData.io vocabulary): `business`, `crime`, `domestic`, `education`, `entertainment`, `environment`, `food`, `health`, `lifestyle`, `other`, `politics`, `science`, `sports`, `technology`, `top`, `tourism`, `world`.

**`q_in_title`** — optional; when set, the keyword must appear in the article **title**. The frontend uses this for Indian-state style filters so results are about that region, not random mentions in the body.

Broad keyword search uses the same NewsData.io endpoint with a `q` filter; there is no separate `/everything`-style toggle like the old NewsAPI integration.

### Saved articles

| Method | Path                      | Notes                                                                   |
|--------|---------------------------|-------------------------------------------------------------------------|
| POST   | `/saved`                  | Persist an article snapshot (full payload, not just the URL).             |
| GET    | `/saved`                  | List the caller's saved items (`starred_only`, `limit`, `offset`).      |
| GET    | `/saved/{id}`             | Read one.                                                               |
| PATCH  | `/saved/{id}`             | Toggle `starred`.                                                       |
| DELETE | `/saved/{id}`             | Remove.                                                                 |
| GET    | `/saved/{id}/download`    | `format=txt|pdf`, `style=detailed|formatted`. Single-article export.    |
| GET    | `/saved/export`           | Bulk download; same query params + `starred_only`.                     |

### Activity (reading streak)

| Method | Path               | Notes |
|--------|--------------------|--------|
| POST   | `/activity/ping`   | Idempotently record "user opened news" for the current UTC day; returns streak hints. |
| GET    | `/activity/stats`  | Streaks, month/total counts, 30-day heatmap for the dashboard. |

---

## How the live feed vs formatted JSON vs exports relate

The **detailed feed** (`GET /news`) returns normalised fields: title, description, content, source, image URL, published time, etc., after cleaning HTML/truncation artefacts from the upstream payload. **The React app uses this endpoint only.**

The **formatted JSON feed** (`GET /news/formatted`) runs each article through `services/formatter.py`, which:

1. Cleans whitespace and strips common truncation markers (including legacy `[+N chars]` patterns).
2. Picks the first sentence of the description as a one-line summary where applicable.
3. Runs YAKE on `title + description` for the top keyphrases.
4. Emits a `bullets: [str]` list.

The same `format_article()` logic feeds the **`style=formatted`** branch in `exporter.py` for **saved-article downloads**, so exported “formatted” study notes match the bullet pipeline even though the home feed no longer renders that JSON.

---

## Downloads

```
GET /saved/{id}/download?format=pdf&style=formatted
GET /saved/export?format=pdf&style=formatted&starred_only=true
```

- `format=txt` returns `text/plain; charset=utf-8`.
- `format=pdf` returns `application/pdf` (reportlab).
- `style=detailed` keeps the full stored body.
- `style=formatted` emits the GK bullet list.

Responses use `Content-Disposition: attachment` so browsers download the file.

---

## Notes & gotchas

- **NewsData.io quotas and `page_size`.** The client clamps page size for compatibility with free-tier limits; paid plans can raise caps in code if needed (see `news_service.py`).
- **Per-user isolation.** Every `/saved/*` and `/activity/*` query is scoped to the authenticated `user_id`.
- **Article snapshots** store the full payload so PDF/TXT keep working if the source URL later fails.
- **No LLM summarisation** in the formatter; swap `formatter.py` if you want AI-generated bullets later.

---

## Deployment

Use the repo root **`docker compose`** setup to run the SPA + API together (`../docker-compose.yml`). The frontend container reverse-proxies `/api` to this backend so the browser sees a single origin.

For a production host, confirm your NewsData.io plan allows that server’s traffic and adjust `CORS_ORIGINS` / `DATABASE_URL` (e.g. move off file-based SQLite) as needed.
