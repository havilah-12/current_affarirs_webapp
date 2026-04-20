# Current Affairs — Backend

FastAPI backend for a current-affairs / GK study webapp. It pulls live
headlines from [NewsAPI.org](https://newsapi.org), converts them into a
condensed "GK quick-read" bullet view, lets signed-in users bookmark
articles, and hands back those bookmarks as `.txt` or `.pdf` downloads.

The frontend (React + Tailwind) will be built in a separate phase and will
talk to this API over HTTP.

---

## Stack

- **FastAPI** (Python 3.10+) — web framework
- **SQLAlchemy 2.x** + **SQLite** — ORM + storage
- **Pydantic v2** + **pydantic-settings** — schemas + config
- **python-jose** + **passlib[bcrypt]** — JWT auth + password hashing
- **httpx** — async HTTP client for NewsAPI
- **YAKE** — unsupervised keyphrase extraction for the "formatted" view
- **reportlab** — PDF export

---

## Project layout

```text
backend/
  requirements.txt
  .env.example
  app/
    __init__.py
    config.py           # Settings (reads .env via pydantic-settings)
    database.py         # engine, SessionLocal, Base, init_db()
    models.py           # User, SavedArticle
    schemas.py          # Pydantic request/response models
    security.py         # bcrypt + JWT helpers
    deps.py             # get_db, get_current_user
    services/
      news_service.py   # NewsAPI client (top-headlines + everything)
      formatter.py      # Article -> bullet list (YAKE keyphrases)
      exporter.py       # Article(s) -> .txt / .pdf
    routers/
      auth.py           # /auth/signup, /auth/login, /auth/me
      news.py           # /news, /news/formatted
      saved.py          # /saved CRUD + /saved/{id}/download + /saved/export
    main.py             # FastAPI app factory
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

- `NEWSAPI_KEY` — get a free dev key at <https://newsapi.org/register>
- `JWT_SECRET` — any long random string, e.g.:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

Optional:

- `DEFAULT_COUNTRY` — ISO 3166-1 alpha-2 code used when no filter is given (default `in`).
- `CORS_ORIGINS` — comma-separated list of allowed frontend origins.
- `DATABASE_URL` — defaults to `sqlite:///./current_affairs.db`.

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

- Root:            <http://localhost:8000/>
- Swagger UI:      <http://localhost:8000/docs>
- ReDoc:           <http://localhost:8000/redoc>
- Health probe:    <http://localhost:8000/health>

On first start, the SQLite database is created automatically next to the
`backend/` folder.

---

## API overview

All `/news/*` and `/saved/*` endpoints require a JWT sent as
`Authorization: Bearer <token>`.

### Auth

| Method | Path           | Body / Form                        | Notes                                 |
|--------|----------------|-------------------------------------|---------------------------------------|
| POST   | `/auth/signup` | JSON `{email, password}`            | Creates the user, returns a JWT.      |
| POST   | `/auth/login`  | Form `username` (email), `password` | OAuth2 password flow. Returns a JWT.  |
| GET    | `/auth/me`     | —                                   | Returns the current user.             |

### News (NewsAPI-backed)

| Method | Path               | Query                                                    | Notes                                    |
|--------|--------------------|-----------------------------------------------------------|------------------------------------------|
| GET    | `/news`            | `category`, `country`, `q`, `page`, `page_size`, `search` | Detailed feed.                           |
| GET    | `/news/formatted`  | same                                                      | GK-bullet view of the same articles.     |

Supported categories: `business`, `entertainment`, `general`, `health`,
`science`, `sports`, `technology`.

Set `search=true` together with `q=...` to hit NewsAPI's broader
`/everything` endpoint (keyword search across all sources; category /
country are ignored in this mode).

### Saved articles

| Method | Path                      | Notes                                                                   |
|--------|---------------------------|-------------------------------------------------------------------------|
| POST   | `/saved`                  | Persist an article snapshot (full payload, not just the URL).           |
| GET    | `/saved`                  | List the caller's saved items (`starred_only`, `limit`, `offset`).      |
| GET    | `/saved/{id}`             | Read one.                                                               |
| PATCH  | `/saved/{id}`             | Toggle `starred`.                                                       |
| DELETE | `/saved/{id}`             | Remove.                                                                 |
| GET    | `/saved/{id}/download`    | `format=txt|pdf`, `style=detailed|formatted`. Single-article export.    |
| GET    | `/saved/export`           | Bulk download of all saved (or just starred). Same query params.        |

---

## How the two "views" work

The **detailed view** (`GET /news`) is essentially a cleaned NewsAPI
passthrough: full title, description, content, source, image URL,
published timestamp.

The **formatted view** (`GET /news/formatted`) runs each article through
`services/formatter.py`, which:

1. Cleans whitespace and strips NewsAPI's `[+123 chars]` truncation marker.
2. Picks the first sentence of the description as a one-line summary.
3. Runs YAKE on `title + description` to pull the top 3–5 keyphrases.
4. Renders everything into a `bullets: [str]` list, ready for the UI.

The same `format_article()` function feeds the `style=formatted` branch of
the PDF/TXT exporter, so the "quick-read" view and the downloadable study
notes are always in sync.

---

## Downloads

```
GET /saved/{id}/download?format=pdf&style=formatted
GET /saved/export?format=pdf&style=formatted&starred_only=true
```

- `format=txt` returns `text/plain; charset=utf-8`.
- `format=pdf` returns `application/pdf` built with reportlab.
- `style=detailed` keeps the full article body.
- `style=formatted` emits the GK bullet list.

The server sets `Content-Disposition: attachment; filename=...` so
browsers trigger a real download.

---

## Notes & gotchas

- **NewsAPI free tier is dev-only.** It works fine on `localhost`, but the
  free plan blocks production hosts. Swap to GNews / Mediastack / a paid
  tier before deploying.
- **Per-user isolation.** Every `/saved/*` query is filtered by
  `user_id`; a user can never read or mutate another user's rows.
- **Article snapshots are stored in full** (title, description, content,
  source, image URL). This means PDF/TXT downloads keep working even if
  the original URL later 404s.
- **No AI summarisation.** The formatted view is rule-based (regex +
  YAKE). `services/formatter.py` is the single swap point if you later
  want to plug in an LLM.

---

## Roadmap

- React + Tailwind frontend (next phase).
- Optional Dockerfile + `docker-compose.yml` for deployment.
- Optional: swap `formatter.py` for an LLM-backed summariser.
