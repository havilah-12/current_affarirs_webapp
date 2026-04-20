"""API routers.

Each module here exposes a FastAPI `APIRouter` that `main.py` mounts:

- `auth`     : signup, login, /auth/me
- `news`     : live NewsData.io-backed endpoints (detailed + formatted)
- `saved`    : CRUD for per-user saved articles + downloads
- `activity` : daily-streak ping + dashboard stats

Routers are kept thin - all business logic lives in `services/`.
"""
