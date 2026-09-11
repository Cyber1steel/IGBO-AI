from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Exercise, Lesson, Level, Unit, Vocabulary


async def _seed_lesson_with_two_exercises(db: AsyncSession):
    level = Level(code="absolute_beginner", name="Absolute Beginner", order=1)
    db.add(level)
    await db.flush()
    unit = Unit(level_id=level.id, title="First Words", order=1)
    db.add(unit)
    await db.flush()
    lesson = Lesson(unit_id=unit.id, title="Greetings", order=1, examples=[])
    db.add(lesson)
    await db.flush()

    ex1 = Exercise(
        lesson_id=lesson.id, exercise_type="multiple_choice", prompt="Q1",
        content={"correct_option": "Ndewo"}, order=1,
    )
    ex2 = Exercise(
        lesson_id=lesson.id, exercise_type="fill_blank", prompt="Q2",
        content={"correct_answer": "m"}, order=2,
    )
    db.add_all([ex1, ex2])
    vocab = Vocabulary(igbo_text="Ndewo", english_text="Hello", level_id=level.id, lesson_id=lesson.id)
    db.add(vocab)
    await db.commit()
    return lesson, ex1, ex2


async def _register(client: AsyncClient, email="learner@example.com") -> str:
    resp = await client.post(
        "/auth/register", json={"email": email, "password": "igbo1234", "display_name": "Learner"}
    )
    return resp.json()["access_token"]


async def test_lesson_progress_defaults_to_not_started(client: AsyncClient, db_session: AsyncSession):
    lesson, _, _ = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    resp = await client.get(f"/lessons/{lesson.id}/progress", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "not_started"


async def test_starting_a_lesson_sets_in_progress(client: AsyncClient, db_session: AsyncSession):
    lesson, _, _ = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    resp = await client.post(f"/lessons/{lesson.id}/start", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["started_at"] is not None


async def test_correct_exercise_attempt_is_graded_correct(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, _ = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    resp = await client.post(
        f"/exercises/{ex1.id}/attempt",
        json={"answer": "Ndewo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_correct"] is True
    assert resp.json()["correct_answer"] == "Ndewo"


async def test_incorrect_exercise_attempt_is_graded_incorrect(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, _ = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    resp = await client.post(
        f"/exercises/{ex1.id}/attempt",
        json={"answer": "definitely wrong"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_correct"] is False


async def test_answer_grading_is_case_and_whitespace_insensitive(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, _ = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    resp = await client.post(
        f"/exercises/{ex1.id}/attempt",
        json={"answer": "  ndewo  "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.json()["is_correct"] is True


async def test_lesson_completion_computes_score_from_attempts(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, ex2 = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(f"/lessons/{lesson.id}/start", headers=headers)
    await client.post(f"/exercises/{ex1.id}/attempt", json={"answer": "Ndewo"}, headers=headers)  # correct
    await client.post(f"/exercises/{ex2.id}/attempt", json={"answer": "wrong"}, headers=headers)  # incorrect

    resp = await client.post(f"/lessons/{lesson.id}/complete", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["score"] == 50.0  # 1 of 2 correct


async def test_completing_a_lesson_awards_xp_once(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, ex2 = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    before = await client.get("/learners/me", headers=headers)
    xp_before = before.json()["total_xp"]

    await client.post(f"/lessons/{lesson.id}/complete", headers=headers)
    after_first = await client.get("/learners/me", headers=headers)
    xp_after_first = after_first.json()["total_xp"]
    assert xp_after_first > xp_before

    # Completing the same lesson again must not double-award XP.
    await client.post(f"/lessons/{lesson.id}/complete", headers=headers)
    after_second = await client.get("/learners/me", headers=headers)
    assert after_second.json()["total_xp"] == xp_after_first


async def test_completing_lesson_creates_vocabulary_progress(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, ex2 = await _seed_lesson_with_two_exercises(db_session)
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(f"/lessons/{lesson.id}/complete", headers=headers)
    resp = await client.get("/vocabulary/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["vocabulary"]["igbo_text"] == "Ndewo"
    assert body[0]["exposures_count"] == 1


async def test_exercise_attempt_requires_authentication(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, _ = await _seed_lesson_with_two_exercises(db_session)
    resp = await client.post(f"/exercises/{ex1.id}/attempt", json={"answer": "Ndewo"})
    assert resp.status_code == 401


async def test_one_learners_progress_is_independent_of_anothers(client: AsyncClient, db_session: AsyncSession):
    lesson, ex1, _ = await _seed_lesson_with_two_exercises(db_session)
    token_a = await _register(client, "a@example.com")
    token_b = await _register(client, "b@example.com")

    await client.post(
        f"/exercises/{ex1.id}/attempt", json={"answer": "Ndewo"}, headers={"Authorization": f"Bearer {token_a}"}
    )
    await client.post(f"/lessons/{lesson.id}/complete", headers={"Authorization": f"Bearer {token_a}"})

    progress_b = await client.get(
        f"/lessons/{lesson.id}/progress", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert progress_b.json()["status"] == "not_started"  # untouched by learner A's activity
