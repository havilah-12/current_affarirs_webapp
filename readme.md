# Current Affairs Webapp

A  full-stack study tool for competetive exam and  daily news readers aspirants. It provides much more quick article download and interesting dashboard to keep track of the reading streak.

```text
.
|-- backend/             # FastAPI + SQLite + SQLAlchemy + JWT auth
|   |-- Dockerfile
|   `-- app/
|-- frontend/            # React 18 + Vite + Tailwind CSS + React Router
|   |-- Dockerfile
|   |-- nginx.conf       # SPA fallback + /api reverse proxy for prod
|   `-- src/
|-- docker-compose.yml   # one-command stack: backend + nginx-served SPA
|-- .env.example         # copy to .env for `docker compose`
`-- readme.md            # (this file)
```

## Stack

- **Backend** — FastAPI, SQLAlchemy 2, SQLite, python-jose (JWT), bcrypt, httpx (NewsData.io client), YAKE (keyphrase extraction), trafilatura (full-article extraction), reportlab + pillow (PDF).
- **Frontend** — React 18, Vite 5, Tailwind CSS 3, React Router v6, axios.
- **External APIs** — [NewsData.io](https://newsdata.io) for headlines (free dev key works for both localhost and Docker).

## Features

- Signup / login with JWT auth; each user's saved articles are isolated.
- News feed with category / country / Indian-state / keyword filters, persisted in the URL so views are bookmarkable.
- Headline cards: hero image, title, and excerpt from the article description or body, plus a one-click Save button (live feed uses `GET /news`).
- Save any article. The full snapshot — title, body, image — is stored, so PDF / TXT downloads keep working even if the source URL later 404s.
- Daily reading streak tracker on the dashboard.
- Star / unstar saved items.
- Per-article and bulk downloads from saved items, in `.txt` or `.pdf`, in either "detailed" (full body) or "formatted" (YAKE bullet notes) style.

## Quick start — Docker (recommended)

The whole stack runs as two containers (FastAPI backend + Nginx-served React
SPA), wired together by `docker-compose.yml`. The frontend container reverse-
proxies `/api/*` to the backend over the compose-internal network, so the
browser only ever sees one origin and there is no CORS dance.

Prereqs: **Docker Desktop ≥ 4.x** (or Docker Engine ≥ 24 + Compose v2).

```powershell
# 1. Configure
Copy-Item .env.example .env
# Open .env and fill in:
#   NEWSDATA_API_KEY  - free key from https://newsdata.io/register
#   JWT_SECRET        - long random string, e.g.:
#     python -c "import secrets; print(secrets.token_urlsafe(64))"

# 2. Build + run
docker compose up --build -d

# 3. Open the app
#    Frontend (SPA + /api proxy): http://localhost:8080
#    Backend Swagger UI:          http://localhost:8000/docs

# 4. Tail logs
docker compose logs -f

# 5. Stop / wipe DB
docker compose down       # keeps the SQLite volume
docker compose down -v    # ALSO drops the volume (factory reset)
```

The SQLite database lives on the named volume `backend-data` (mounted at
`/data` inside the backend container) so it survives `down` / `up` cycles.

## Quick start — local Python + Node (for hacking)

```powershell
# Backend (http://localhost:8000)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # set NEWSDATA_API_KEY and JWT_SECRET
uvicorn app.main:app --reload

# Frontend (http://localhost:5173) - in a second terminal
cd ..\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open <http://localhost:5173>, create an account, and start browsing.

Full setup details live in each subproject's README:

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)

