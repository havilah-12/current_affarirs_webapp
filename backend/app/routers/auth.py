"""Authentication endpoints.

- `POST /auth/signup` : create a new user (JSON body) and return a JWT.
- `POST /auth/login`  : OAuth2 password form (so Swagger's "Authorize" button
                        works out of the box); returns a JWT.
- `GET  /auth/me`     : return the current user derived from the JWT.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import Token, UserCreate, UserRead
from ..security import (
    access_token_ttl_seconds,
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _get_user_by_email(db: Session, email: str) -> User | None:
    """Case-insensitive email lookup."""
    normalized = email.strip().lower()
    stmt = select(User).where(User.email == normalized)
    return db.execute(stmt).scalar_one_or_none()


def _issue_token_for(user: User) -> Token:
    """Build a `Token` response for the given user."""
    access_token = create_access_token(subject=user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_ttl_seconds(),
    )


@router.post(
    "/signup",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> Token:
    """Register a new user and return a JWT so the frontend can log in immediately."""
    email = payload.email.strip().lower()

    if _get_user_by_email(db, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_token_for(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Exchange email + password for a JWT (OAuth2 password flow)",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Swagger-friendly login using the standard OAuth2 password form.

    Send `username` (the email) and `password` as `application/x-www-form-urlencoded`.
    """
    user = _get_user_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_token_for(user)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Return the currently authenticated user",
)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
