import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.deps import get_current_learner_profile
from app.models import (
    ExerciseAttempt,
    LearnerProfile,
    LearningEvent,
    Lesson,
    LessonProgress,
    VocabularyProgress,
)
from app.services.exercises import to_public_exercise
from app.schemas.curriculum import ExercisePublicOut, LessonProgressOut

router = APIRouter(prefix="/lessons", tags=["lessons"])

# Flat XP award per completed lesson. Deliberately simple — the real
# mastery/XP model is a later-phase concern (see Phase 4 spec section 6).
_XP_PER_LESSON = 20


async def _get_lesson_or_404(db: AsyncSession, lesson_id: uuid.UUID) -> Lesson:
    lesson = await db.get(Lesson, lesson_id, options=[selectinload(Lesson.exercises), selectinload(Lesson.vocabulary)])
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


async def _get_or_create_progress(
    db: AsyncSession, learner_id: uuid.UUID, lesson_id: uuid.UUID
) -> LessonProgress:
    result = await db.execute(
        select(LessonProgress).where(
            LessonProgress.learner_id == learner_id, LessonProgress.lesson_id == lesson_id
        )
    )
    progress = result.scalar_one_or_none()
    if progress is None:
        progress = LessonProgress(learner_id=learner_id, lesson_id=lesson_id, status="not_started")
        db.add(progress)
        await db.flush()
    return progress


@router.get("/{lesson_id}/exercises", response_model=list[ExercisePublicOut])
async def list_lesson_exercises(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _profile: LearnerProfile = Depends(get_current_learner_profile),
):
    lesson = await _get_lesson_or_404(db, lesson_id)
    return [to_public_exercise(e) for e in lesson.exercises]


@router.get("/{lesson_id}/progress", response_model=LessonProgressOut)
async def get_lesson_progress(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
):
    await _get_lesson_or_404(db, lesson_id)
    progress = await _get_or_create_progress(db, profile.id, lesson_id)
    await db.commit()
    return LessonProgressOut.model_validate(progress)


@router.post("/{lesson_id}/start", response_model=LessonProgressOut)
async def start_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
):
    await _get_lesson_or_404(db, lesson_id)
    progress = await _get_or_create_progress(db, profile.id, lesson_id)

    if progress.status == "not_started":
        progress.status = "in_progress"
        progress.started_at = datetime.now(timezone.utc)
        db.add(
            LearningEvent(
                learner_id=profile.id,
                event_type="lesson_started",
                payload={"lesson_id": str(lesson_id)},
            )
        )

    await db.commit()
    await db.refresh(progress)
    return LessonProgressOut.model_validate(progress)


@router.post("/{lesson_id}/complete", response_model=LessonProgressOut)
async def complete_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
):
    lesson = await _get_lesson_or_404(db, lesson_id)
    progress = await _get_or_create_progress(db, profile.id, lesson_id)

    # Score is computed server-side from the learner's own recorded attempts
    # — never trusted from the client — using each exercise's most recent
    # attempt in this lesson.
    score = await _compute_lesson_score(db, profile.id, lesson)

    was_already_completed = progress.status == "completed"
    progress.status = "completed"
    progress.completed_at = datetime.now(timezone.utc)
    progress.score = score
    progress.attempts += 1
    if progress.started_at is None:
        progress.started_at = progress.completed_at

    if not was_already_completed:
        profile.total_xp += _XP_PER_LESSON
        db.add(
            LearningEvent(
                learner_id=profile.id,
                event_type="lesson_completed",
                payload={"lesson_id": str(lesson_id), "score": score},
            )
        )
        await _reinforce_lesson_vocabulary(db, profile.id, lesson)

    await db.commit()
    await db.refresh(progress)
    return LessonProgressOut.model_validate(progress)


async def _compute_lesson_score(db: AsyncSession, learner_id: uuid.UUID, lesson: Lesson) -> float:
    if not lesson.exercises:
        return 100.0

    exercise_ids = [e.id for e in lesson.exercises]
    # Most recent attempt per exercise, for this learner.
    result = await db.execute(
        select(ExerciseAttempt)
        .where(ExerciseAttempt.learner_id == learner_id, ExerciseAttempt.exercise_id.in_(exercise_ids))
        .order_by(ExerciseAttempt.created_at.desc())
    )
    latest_by_exercise: dict[uuid.UUID, ExerciseAttempt] = {}
    for attempt in result.scalars().all():
        latest_by_exercise.setdefault(attempt.exercise_id, attempt)

    correct = sum(1 for a in latest_by_exercise.values() if a.is_correct)
    return round((correct / len(lesson.exercises)) * 100, 1)


async def _reinforce_lesson_vocabulary(db: AsyncSession, learner_id: uuid.UUID, lesson: Lesson) -> None:
    """Very simple exposure bump for vocabulary tied to a just-completed
    lesson. Not the final SRS/mastery algorithm (Phase 4 explicitly defers
    that) — just enough to make VocabularyProgress real and non-empty."""
    for vocab in lesson.vocabulary:
        result = await db.execute(
            select(VocabularyProgress).where(
                VocabularyProgress.learner_id == learner_id, VocabularyProgress.vocabulary_id == vocab.id
            )
        )
        progress = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if progress is None:
            db.add(
                VocabularyProgress(
                    learner_id=learner_id,
                    vocabulary_id=vocab.id,
                    exposures_count=1,
                    mastery_score=20.0,
                    last_reviewed_at=now,
                )
            )
        else:
            progress.exposures_count += 1
            progress.mastery_score = min(100.0, progress.mastery_score + 15.0)
            progress.last_reviewed_at = now
