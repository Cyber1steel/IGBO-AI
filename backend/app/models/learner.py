import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin

# Mirrors the Phase 1 proficiency ladder — kept as plain strings (not a DB
# enum) so new levels don't require a migration; validated at the schema layer.
LEVELS = (
    "absolute_beginner",
    "beginner",
    "elementary",
    "intermediate",
    "upper_intermediate",
    "advanced",
    "fluent",
)


class LearnerProfile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "learner_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    current_level: Mapped[str] = mapped_column(String(30), default="absolute_beginner", nullable=False)
    learning_goal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_learning_style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="learner_profile")
