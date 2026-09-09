from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_learner_profile
from app.models import LearnerProfile
from app.schemas.auth import LearnerProfileOut, LearnerProfileUpdate

router = APIRouter(prefix="/learners", tags=["learners"])


@router.get("/me", response_model=LearnerProfileOut)
async def get_my_profile(profile: LearnerProfile = Depends(get_current_learner_profile)):
    return LearnerProfileOut.model_validate(profile)


@router.patch("/me", response_model=LearnerProfileOut)
async def update_my_profile(
    payload: LearnerProfileUpdate,
    profile: LearnerProfile = Depends(get_current_learner_profile),
    db: AsyncSession = Depends(get_db),
):
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return LearnerProfileOut.model_validate(profile)


@router.post("/me/activity-ping", response_model=LearnerProfileOut)
async def record_activity(
    profile: LearnerProfile = Depends(get_current_learner_profile),
    db: AsyncSession = Depends(get_db),
):
    """Minimal streak logic: call this once when a learner does something
    today. Full XP/streak rules (grace periods, timezones, etc) are a Phase
    4+ concern — this is intentionally simple."""
    today = datetime.now(timezone.utc).date()
    if profile.last_activity_date == today:
        pass  # already counted today
    elif profile.last_activity_date == _yesterday(today):
        profile.current_streak += 1
    else:
        profile.current_streak = 1
    profile.longest_streak = max(profile.longest_streak, profile.current_streak)
    profile.last_activity_date = today
    await db.commit()
    await db.refresh(profile)
    return LearnerProfileOut.model_validate(profile)


def _yesterday(d: date) -> date:
    return d - timedelta(days=1)
