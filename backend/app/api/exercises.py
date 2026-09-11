import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_learner_profile
from app.models import Exercise, ExerciseAttempt, LearnerProfile, LearningEvent
from app.schemas.curriculum import ExerciseAttemptRequest, ExerciseAttemptResult
from app.services.exercises import grade_answer

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.post("/{exercise_id}/attempt", response_model=ExerciseAttemptResult)
async def attempt_exercise(
    exercise_id: uuid.UUID,
    payload: ExerciseAttemptRequest,
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
):
    exercise = await db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    is_correct, correct_answer = grade_answer(exercise, payload.answer)

    attempt_count_result = await db.execute(
        select(func.count()).where(
            ExerciseAttempt.learner_id == profile.id, ExerciseAttempt.exercise_id == exercise_id
        )
    )
    attempt_number = attempt_count_result.scalar_one() + 1

    db.add(
        ExerciseAttempt(
            learner_id=profile.id,
            exercise_id=exercise_id,
            answer=payload.answer,
            is_correct=is_correct,
            score=100.0 if is_correct else 0.0,
            attempt_number=attempt_number,
            time_taken_seconds=payload.time_taken_seconds,
        )
    )
    db.add(
        LearningEvent(
            learner_id=profile.id,
            event_type="exercise_answered",
            payload={"exercise_id": str(exercise_id), "is_correct": is_correct},
        )
    )
    await db.commit()

    return ExerciseAttemptResult(
        is_correct=is_correct,
        correct_answer=correct_answer,
        explanation=exercise.explanation,
        attempt_number=attempt_number,
    )
