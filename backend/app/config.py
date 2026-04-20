"""Application configuration.

Loads environment variables (from `.env` during development) via
`pydantic-settings` and exposes a single cached `Settings` instance that the
rest of the backend imports.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Current Affairs API"
    DEBUG: bool = False

    # --- NewsData.io ---
    # Primary setting name; NEWSAPI_KEY is still accepted as a legacy fallback
    # so older .env files (which used the NewsAPI.org naming) keep working.
    NEWSDATA_API_KEY: str = Field(
        default="",
        description="API key for https://newsdata.io. Required for live news endpoints.",
    )
    NEWSDATA_BASE_URL: str = "https://newsdata.io/api/1"

    # Legacy alias for NEWSDATA_API_KEY (read via `news_api_key` property
    # only). Old .env files that still use this name keep working.
    NEWSAPI_KEY: str = Field(default="", description="Legacy alias for NEWSDATA_API_KEY.")

    # --- JWT / Auth ---
    JWT_SECRET: str = Field(
        default="change_me_to_a_long_random_string",
        description="Secret used to sign JWT access tokens.",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- News scope ---
    DEFAULT_COUNTRY: str = "in"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./current_affairs.db"

    # --- CORS ---
    # Stored as a comma-separated string (not `List[str]`) so pydantic-settings
    # does not try to JSON-decode the `.env` value. Use `cors_origins` to get
    # the parsed list for FastAPI's CORSMiddleware.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @field_validator("DEFAULT_COUNTRY", mode="before")
    @classmethod
    def _normalize_country(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @property
    def cors_origins(self) -> List[str]:
        """Return `CORS_ORIGINS` split into a list of trimmed, non-empty origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def news_api_key(self) -> str:
        """Resolve the NewsData.io key, falling back to the legacy field name."""
        return (self.NEWSDATA_API_KEY or self.NEWSAPI_KEY).strip()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached `Settings` instance."""
    return Settings()


settings = get_settings()
