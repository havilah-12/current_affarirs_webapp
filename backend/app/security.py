"""Password hashing and JWT helpers.

Two concerns live in this module:

1. **Password hashing** via `bcrypt` directly. Plain-text passwords never
   touch the database - only the hash does. We call `bcrypt` directly rather
   than going through `passlib` because `passlib 1.7.4` is unmaintained and
   crashes during its self-test against modern `bcrypt` (>= 4.1).
2. **JWT access tokens** signed with `settings.JWT_SECRET` using HS256.

The router layer uses `hash_password` and `verify_password` during signup and
login. `create_access_token` is called on successful login, and
`decode_access_token` is called by `deps.get_current_user` on every protected
request.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
from jose import jwt

from .config import settings


_BCRYPT_MAX_BYTES = 72


def _prepare_secret(password: str) -> bytes:
    """Encode `password` to bytes and truncate to bcrypt's 72-byte limit.

    bcrypt silently ignored bytes beyond 72 in older versions; `bcrypt >= 4.1`
    now raises `ValueError` instead. Truncating here preserves the original
    behaviour (any password that fits in 72 UTF-8 bytes - which is virtually
    every real password - is unchanged) and keeps the API non-raising.
    """
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Return a bcrypt hash of `password` suitable for storage in `users.hashed_password`."""
    hashed = bcrypt.hashpw(_prepare_secret(password), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True iff `plain_password` matches the stored bcrypt hash.

    Malformed or empty stored hashes return False rather than raising, so a
    corrupted row can't turn into a 500 on the login endpoint.
    """
    try:
        return bcrypt.checkpw(
            _prepare_secret(plain_password),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str | int) -> str:
    """Build and sign a JWT access token whose `sub` claim is `subject`.

    The numeric user id is stored as a string (JWT `sub` is conventionally a
    string). Lifetime comes from `settings.JWT_EXPIRE_MINUTES`.
    """
    now = datetime.now(timezone.utc)
    lifetime = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Validate + decode a JWT and return its claim dict.

    Raises `jose.JWTError` if the signature is invalid, the token is expired,
    or the payload is malformed. Callers (typically `deps.get_current_user`)
    translate this into an HTTP 401.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )


def access_token_ttl_seconds() -> int:
    """Lifetime (in seconds) advertised in the `/auth/login` response."""
    return settings.JWT_EXPIRE_MINUTES * 60
