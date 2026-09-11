import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_learner_profile
from app.models import LearnerProfile, Vocabulary, VocabularyProgress
from app.schemas.curriculum import VocabularyOut, VocabularyProgressOut

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("", response_model=list[VocabularyOut])
async def list_vocabulary(
    level_id: uuid.UUID | None = None,
    lesson_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Vocabulary)
    if level_id:
        query = query.where(Vocabulary.level_id == level_id)
    if lesson_id:
        query = query.where(Vocabulary.lesson_id == lesson_id)
    result = await db.execute(query.order_by(Vocabulary.igbo_text))
    return result.scalars().all()


@router.get("/me", response_model=list[VocabularyProgressOut])
async def my_vocabulary_progress(
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
):
    """Only vocabulary the learner has actually been exposed to (i.e. has a
    VocabularyProgress row) — not the whole curated list. That's what makes
    this "my vocabulary" rather than just the vocabulary endpoint again."""
    result = await db.execute(
        select(VocabularyProgress)
        .join(Vocabulary, VocabularyProgress.vocabulary_id == Vocabulary.id)
        .where(VocabularyProgress.learner_id == profile.id)
        .order_by(VocabularyProgress.last_reviewed_at.desc())
    )
    rows = result.scalars().all()

    out = []
    for row in rows:
        vocab = await db.get(Vocabulary, row.vocabulary_id)
        out.append(
            VocabularyProgressOut(
                vocabulary=VocabularyOut.model_validate(vocab),
                exposures_count=row.exposures_count,
                correct_count=row.correct_count,
                incorrect_count=row.incorrect_count,
                mastery_score=row.mastery_score,
                last_reviewed_at=row.last_reviewed_at,
            )
        )
    return out
