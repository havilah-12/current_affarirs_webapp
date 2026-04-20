"""FastAPI application entry point.

Run the backend locally:

    uvicorn app.main:app --reload

Responsibilities:

- Create the FastAPI app and configure CORS for the React frontend.
- Ensure the SQLite schema exists on startup (`init_db()`).
- Mount the auth, news, and saved routers.
- Expose a lightweight `/health` probe.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import activity as activity_router
from .routers import auth as auth_router
from .routers import news as news_router
from .routers import saved as saved_router


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    """Create database tables on startup.

    Using the lifespan context rather than the deprecated `on_event` hooks
    keeps us aligned with FastAPI >= 0.110.
    """
    init_db()
    yield


def create_app() -> FastAPI:
    """Application factory. Keeps `main` importable without side effects."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        debug=settings.DEBUG,
        description=(
            "Backend for the Current Affairs / GK study webapp. "
            "Serves News headlines around the world  all in one place, "
            "per-user saved articles, and txt/pdf downloads."
        ),
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router.router)
    app.include_router(news_router.router)
    app.include_router(saved_router.router)
    app.include_router(activity_router.router)

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    def health() -> dict:
        return {"status": "ok", "app": settings.APP_NAME}

    @app.get("/", tags=["meta"], include_in_schema=False)
    def root() -> dict:
        return {
            "app": settings.APP_NAME,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
