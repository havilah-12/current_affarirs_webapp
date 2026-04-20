"""FastAPI dependencies.

Centralises the two dependencies that nearly every route uses:

- `get_db`           - yields a SQLAlchemy session and guarantees it closes.
- `get_current_user` - decodes the `Authorization: Bearer <jwt>` header and
                       returns the matching `User` row, or raises HTTP 401.
"""

from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User
from .security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it when the request is done."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the JWT from the `Authorization` header into a `User` row.

    A missing / malformed / expired token, or a token whose `sub` does not
    match a live user, all surface as HTTP 401 so the frontend can redirect
    to login without needing to differentiate between the failure modes.
    """
    if not token:
        raise _CREDENTIALS_ERROR

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise _CREDENTIALS_ERROR

    subject = payload.get("sub")
    if not subject:
        raise _CREDENTIALS_ERROR

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise _CREDENTIALS_ERROR

    user = db.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_ERROR

    return user
