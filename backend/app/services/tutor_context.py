import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base import TutorContext
from app.models import LearnerProfile, Lesson, VocabularyProgress, Vocabulary

_MAX_VOCAB_HINTS = 6


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
    lesson_title: str | None = None
    lesson_objective: str | None = None
    vocabulary: list[str] = []

    if lesson_id is not None:
        result = await db.execute(
            select(Lesson)
            .options(selectinload(Lesson.objectives), selectinload(Lesson.vocabulary))
            .where(Lesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()
        if lesson is not None:
            lesson_title = lesson.title
            if lesson.objectives:
                lesson_objective = lesson.objectives[0].description
            vocabulary = [v.igbo_text for v in lesson.vocabulary[:_MAX_VOCAB_HINTS]]

    if not vocabulary:
        result = await db.execute(
            select(Vocabulary)
            .join(VocabularyProgress, VocabularyProgress.vocabulary_id == Vocabulary.id)
            .where(VocabularyProgress.learner_id == profile.id)
            .order_by(VocabularyProgress.mastery_score.asc())
            .limit(_MAX_VOCAB_HINTS)
        )
        vocabulary = [v.igbo_text for v in result.scalars().all()]

    return TutorContext(
        learner_level=profile.current_level,
        lesson_title=lesson_title,
        lesson_objective=lesson_objective,
        relevant_vocabulary=vocabulary,
    )
