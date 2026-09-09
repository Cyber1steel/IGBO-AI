import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models import LearnerProfile, User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauthorized

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


async def get_current_learner_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LearnerProfile:
    """Every learner-scoped endpoint depends on this (not on a user-supplied
    id) — that's what makes cross-user data access structurally impossible
    rather than just checked-for."""
    result = await db.execute(select(LearnerProfile).where(LearnerProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        # Should not happen — a profile is created at registration — but
        # fail clearly rather than crashing on a None attribute access.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learner profile not found")
    return profile
