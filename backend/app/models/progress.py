import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPKMixin


class LearnerProgress(UUIDPKMixin, Base):
    """Generic rollup progress at any curriculum scope (course/level/unit/
    lesson/skill), so we're not bolting a new column onto LearnerProfile
    every time a new scope is needed."""

    __tablename__ = "learner_progress"
    __table_args__ = (
        UniqueConstraint("learner_id", "scope_type", "scope_id", name="uq_progress_scope"),
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "course" | "level" | "unit" | "lesson" | "skill"
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # "not_started" | "in_progress" | "completed"
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class LessonProgress(UUIDPKMixin, Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("learner_id", "lesson_id", name="uq_lesson_progress"),)

    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class VocabularyProgress(UUIDPKMixin, Base):
    __tablename__ = "vocabulary_progress"
    __table_args__ = (UniqueConstraint("learner_id", "vocabulary_id", name="uq_vocab_progress"),)

    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vocabulary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exposures_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100
    difficulty: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0-1
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class ExerciseAttempt(UUIDPKMixin, Base):
    __tablename__ = "exercise_attempts"

    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answer: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    time_taken_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class Mastery(UUIDPKMixin, Base):
    """Flexible per-skill mastery. reference_id lets a row point at a specific
    grammar topic / vocabulary item / etc; NULL means the skill_type overall."""

    __tablename__ = "mastery"
    __table_args__ = (
        UniqueConstraint("learner_id", "skill_type", "reference_id", name="uq_mastery"),
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "vocabulary" | "grammar" | "pronunciation" | "listening" | "reading" | "writing" | "conversation"
    skill_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ReviewItem(UUIDPKMixin, Base):
    """Spaced-repetition queue. Algorithm (SM-2 or similar) is implemented in
    a service in a later phase — this table just holds the scheduling state."""

    __tablename__ = "review_items"
    __table_args__ = (
        UniqueConstraint("learner_id", "item_type", "item_id", name="uq_review_item"),
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "vocabulary" | "grammar" | "phrase"
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    interval_days: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
