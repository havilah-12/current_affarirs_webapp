# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# Backend image: FastAPI + Uvicorn (Python 3.12-slim).
#
# Design notes:
# - Single stage. Python deps install cleanly from prebuilt manylinux wheels
#   (pillow / lxml / bcrypt / cryptography all ship them for 3.12).
# - Layers ordered for cache friendliness: requirements first, code last.
# - Runs as a non-root `app` user. The SQLite DB lives in /data, which is
#   chowned to that user and intended to be mounted as a named volume.
# - PYTHONDONTWRITEBYTECODE / PYTHONUNBUFFERED are the standard "good
#   citizen" Python container envs (no .pyc clutter, instant log flush).
# ---------------------------------------------------------------------------

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app \
    DATA_DIR=/data

# curl is included only for HEALTHCHECK; everything else (httpx etc.) ships
# its own networking stack. Clean apt lists in the same layer to keep image
# size lean.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

# Non-root runtime user. /data holds the SQLite file and is mounted as a
# volume in compose so the DB survives container rebuilds.
RUN groupadd --system app \
    && useradd --system --gid app --home ${APP_HOME} app \
    && mkdir -p ${DATA_DIR} \
    && chown -R app:app ${APP_HOME} ${DATA_DIR}

USER app

EXPOSE 8000

# Default DB path points at the mounted volume. Override via the env in
# docker-compose.yml or `docker run -e DATABASE_URL=...` if you'd rather
# point at Postgres etc.
ENV DATABASE_URL=sqlite:////data/current_affairs.db

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
