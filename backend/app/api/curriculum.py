import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.models import Level, Lesson, Unit
from app.schemas.curriculum import (
    LessonDetail,
    LessonObjectiveOut,
    LessonSummary,
    LevelDetail,
    LevelSummary,
    UnitDetail,
    UnitSummary,
    VocabularyOut,
)
from app.services.exercises import to_public_exercise

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

# Curriculum content (levels/units/lessons/vocabulary text) is not
# learner-specific, so these reads are public — matches Phase 4 spec section
# 10/12. Only progress/attempts (in app/api/lessons.py, exercises.py) require auth.


@router.get("/levels", response_model=list[LevelSummary])
async def list_levels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Level).order_by(Level.order))
    return result.scalars().all()


@router.get("/levels/{level_id}", response_model=LevelDetail)
async def get_level(level_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Level).options(selectinload(Level.units).selectinload(Unit.lessons)).where(Level.id == level_id)
    )
    level = result.scalar_one_or_none()
    if level is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Level not found")

    return LevelDetail(
        id=level.id,
        code=level.code,
        name=level.name,
        order=level.order,
        units=[
            UnitSummary(
                id=u.id, title=u.title, description=u.description, order=u.order, lesson_count=len(u.lessons)
            )
            for u in level.units
        ],
    )


@router.get("/units/{unit_id}", response_model=UnitDetail)
async def get_unit(unit_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Unit).options(selectinload(Unit.lessons)).where(Unit.id == unit_id)
    )
    unit = result.scalar_one_or_none()
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    return UnitDetail(
        id=unit.id,
        title=unit.title,
        description=unit.description,
        order=unit.order,
        lesson_count=len(unit.lessons),
        lessons=[LessonSummary(id=lesson.id, title=lesson.title, order=lesson.order) for lesson in unit.lessons],
    )


@router.get("/lessons/{lesson_id}", response_model=LessonDetail)
async def get_lesson(lesson_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lesson)
        .options(
            selectinload(Lesson.objectives),
            selectinload(Lesson.vocabulary),
            selectinload(Lesson.exercises),
        )
        .where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    return LessonDetail(
        id=lesson.id,
        title=lesson.title,
        order=lesson.order,
        content=lesson.content,
        examples=lesson.examples,
        unit_id=lesson.unit_id,
        objectives=[LessonObjectiveOut.model_validate(o) for o in lesson.objectives],
        vocabulary=[VocabularyOut.model_validate(v) for v in lesson.vocabulary],
        exercises=[to_public_exercise(e) for e in lesson.exercises],
    )


