from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models import LearnerProfile, RefreshToken, User
from app.schemas.auth import AccessTokenResponse, LoginRequest, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

REFRESH_COOKIE_NAME = "igboai_refresh_token"
REFRESH_COOKIE_PATH = "/auth"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
        max_age=settings.refresh_token_ttl_days * 24 * 3600,
    )


async def _issue_tokens(db: AsyncSession, user: User, response: Response) -> str:
    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_ttl_days),
        )
    )
    await db.commit()
    _set_refresh_cookie(response, raw_refresh)
    return create_access_token(str(user.id))


@router.post("/register", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()  # assigns user.id without committing yet

    db.add(LearnerProfile(user_id=user.id, display_name=payload.display_name))
    await db.commit()
    await db.refresh(user)

    access_token = await _issue_tokens(db, user, response)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in_minutes=settings.access_token_ttl_minutes,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=AccessTokenResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    generic_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user is None or not verify_password(payload.password, user.password_hash):
        raise generic_error
    if not user.is_active:
        raise generic_error

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = await _issue_tokens(db, user, response)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in_minutes=settings.access_token_ttl_minutes,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    igboai_refresh_token: str | None = Cookie(default=None),
):
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    if not igboai_refresh_token:
        raise unauthorized

    token_hash = hash_refresh_token(igboai_refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if stored is None or stored.revoked_at is not None or stored.expires_at < now:
        raise unauthorized

    user = await db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise unauthorized

    # Rotate: revoke the used token and issue a fresh one. Limits the damage
    # window if a refresh token cookie is ever stolen.
    stored.revoked_at = now
    access_token = await _issue_tokens(db, user, response)
    return AccessTokenResponse(
        access_token=access_token,
        expires_in_minutes=settings.access_token_ttl_minutes,
        user=UserOut.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    igboai_refresh_token: str | None = Cookie(default=None),
):
    if igboai_refresh_token:
        token_hash = hash_refresh_token(igboai_refresh_token)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        stored = result.scalar_one_or_none()
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            await db.commit()

    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
