import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base import TutorContext
from app.models import ExerciseAttempt, LearnerProfile, Lesson, Vocabulary, VocabularyProgress

_MAX_VOCAB_HINTS = 6
_MAX_WEAKNESS_HINTS = 5
# How many of the learner's most recent exercise attempts to look at when
# deriving a performance signal. Small and recent on purpose — this is a
# short-term "how are they doing right now" signal, not a mastery score.
_RECENT_ATTEMPTS_WINDOW = 10


async def build_tutor_context(
    db: AsyncSession,
    profile: LearnerProfile,
    lesson_id: uuid.UUID | None,
) -> TutorContext:
    """Builds the small, explicit context object passed to an AIProvider.

    Precedence for vocabulary hints: the current lesson's vocabulary if the
    learner is in one, otherwise their own weakest-mastery words (so the
    tutor conversation reinforces what they're actually struggling with,
    not the whole curriculum's word list).
    """
    unit_title: str | None = None
    lesson_title: str | None = None
    lesson_objective: str | None = None
    vocabulary: list[str] = []

    if lesson_id is not None:
        result = await db.execute(
            select(Lesson)
            .options(
                selectinload(Lesson.objectives),
                selectinload(Lesson.vocabulary),
                selectinload(Lesson.unit),
            )
            .where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()
        if lesson is not None:
            lesson_title = lesson.title
            unit_title = lesson.unit.title if lesson.unit else None
            if lesson.objectives:
                lesson_objective = lesson.objectives[0].description
            vocabulary = [v.igbo_text for v in lesson.vocabulary[:_MAX_VOCAB_HINTS]]

    if not vocabulary:
        vocabulary = await _weakest_vocabulary(db, profile.id, _MAX_VOCAB_HINTS)

    known_weaknesses = await _weakest_vocabulary(db, profile.id, _MAX_WEAKNESS_HINTS, max_mastery=40.0)
    performance_signal = await _compute_performance_signal(db, profile.id)

    return TutorContext(
        learner_level=profile.current_level,
        unit_title=unit_title,
        lesson_title=lesson_title,
        lesson_objective=lesson_objective,
        relevant_vocabulary=vocabulary,
        known_weaknesses=known_weaknesses,
        performance_signal=performance_signal,
    )


async def _weakest_vocabulary(
    db: AsyncSession, learner_id: uuid.UUID, limit: int, max_mastery: float | None = None
) -> list[str]:
    query = (
        select(Vocabulary)
        .join(VocabularyProgress, VocabularyProgress.vocabulary_id == Vocabulary.id)
        .where(VocabularyProgress.learner_id == learner_id)
        .order_by(VocabularyProgress.mastery_score.asc())
        .limit(limit)
    )
    if max_mastery is not None:
        query = query.where(VocabularyProgress.mastery_score < max_mastery)
    result = await db.execute(query)
    return [v.igbo_text for v in result.scalars().all()]


async def _compute_performance_signal(db: AsyncSession, learner_id: uuid.UUID) -> str:
    """A short-term, application-computed signal — never something the
    model reports about itself, and never fed back from a model response.
    This is deliberately simple (Phase 6 explicitly defers the final
    mastery/adaptive-learning algorithm); it only looks at the learner's
    most recent attempts, not their whole history."""
    result = await db.execute(
        select(ExerciseAttempt.is_correct)
        .where(ExerciseAttempt.learner_id == learner_id)
        .order_by(ExerciseAttempt.created_at.desc())
        .limit(_RECENT_ATTEMPTS_WINDOW)
    )
    recent = result.scalars().all()
    if not recent:
        return "new"

    correct_ratio = sum(1 for r in recent if r) / len(recent)
    if correct_ratio >= 0.8:
        return "comfortable"
    if correct_ratio < 0.5:
        return "struggling"
    return "developing"
