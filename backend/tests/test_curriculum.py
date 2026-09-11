from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Exercise, Lesson, Level, LessonObjective, Unit, Vocabulary


async def _seed_minimal_curriculum(db: AsyncSession):
    level = Level(code="absolute_beginner", name="Absolute Beginner", order=1)
    db.add(level)
    await db.flush()

    unit = Unit(level_id=level.id, title="First Words", description="Greetings", order=1)
    db.add(unit)
    await db.flush()

    lesson = Lesson(unit_id=unit.id, title="Greetings", order=1, content="Say hello.", examples=[])
    db.add(lesson)
    await db.flush()

    db.add(LessonObjective(lesson_id=lesson.id, description="Greet someone", order=1))
    exercise = Exercise(
        lesson_id=lesson.id,
        exercise_type="multiple_choice",
        prompt="How do you say hello?",
        content={"options": ["Ndewo", "Biko"], "correct_option": "Ndewo"},
        explanation="Ndewo means hello.",
        order=1,
    )
    db.add(exercise)
    vocab = Vocabulary(igbo_text="Ndewo", english_text="Hello", level_id=level.id, lesson_id=lesson.id)
    db.add(vocab)
    await db.commit()
    return level, unit, lesson, exercise


async def test_list_levels_is_public(client: AsyncClient, db_session: AsyncSession):
    await _seed_minimal_curriculum(db_session)
    resp = await client.get("/curriculum/levels")
    assert resp.status_code == 200
    codes = [lvl["code"] for lvl in resp.json()]
    assert "absolute_beginner" in codes


async def test_level_detail_includes_units(client: AsyncClient, db_session: AsyncSession):
    level, unit, _, _ = await _seed_minimal_curriculum(db_session)
    resp = await client.get(f"/curriculum/levels/{level.id}")
    assert resp.status_code == 200
    assert resp.json()["units"][0]["title"] == "First Words"


async def test_unknown_level_returns_404(client: AsyncClient):
    resp = await client.get("/curriculum/levels/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


async def test_lesson_detail_never_exposes_correct_answers(client: AsyncClient, db_session: AsyncSession):
    _, _, lesson, _ = await _seed_minimal_curriculum(db_session)
    resp = await client.get(f"/curriculum/lessons/{lesson.id}")
    assert resp.status_code == 200
    body = resp.json()
    exercise_content = body["exercises"][0]["content"]
    assert "correct_option" not in exercise_content
    assert "correct_answer" not in exercise_content
    # the non-answer content (e.g. options to choose from) should still be there
    assert exercise_content["options"] == ["Ndewo", "Biko"]


async def test_lesson_exercises_endpoint_also_strips_answers(client: AsyncClient, db_session: AsyncSession):
    _, _, lesson, _ = await _seed_minimal_curriculum(db_session)
    reg = await client.post(
        "/auth/register",
        json={"email": "learner@example.com", "password": "igbo1234", "display_name": "Learner"},
    )
    token = reg.json()["access_token"]

    resp = await client.get(
        f"/lessons/{lesson.id}/exercises", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "correct_option" not in resp.json()[0]["content"]
