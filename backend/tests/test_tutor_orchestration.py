import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Exercise,
    LearnerProfile,
    LearningEvent,
    Lesson,
    LessonObjective,
    Level,
    Unit,
    User,
    Vocabulary,
)
from app.services.tutor_context import build_tutor_context


async def _seed_lesson(db: AsyncSession):
    level = Level(code="absolute_beginner", name="Absolute Beginner", order=1)
    db.add(level)
    await db.flush()
    unit = Unit(level_id=level.id, title="First Words", order=1)
    db.add(unit)
    await db.flush()
    lesson = Lesson(unit_id=unit.id, title="Greetings", order=1, examples=[])
    db.add(lesson)
    await db.flush()
    db.add(LessonObjective(lesson_id=lesson.id, description="Greet someone", order=1))
    exercise = Exercise(
        lesson_id=lesson.id, exercise_type="multiple_choice", prompt="Q1",
        content={"correct_option": "Ndewo"}, order=1,
    )
    db.add(exercise)
    vocab = Vocabulary(igbo_text="Ndewo", english_text="Hello", level_id=level.id, lesson_id=lesson.id)
    db.add(vocab)
    await db.commit()
    return lesson, exercise, vocab


async def _seed_bare_profile(db: AsyncSession, email: str) -> LearnerProfile:
    user = User(id=uuid.uuid4(), email=email, password_hash="x")
    db.add(user)
    await db.flush()
    profile = LearnerProfile(user_id=user.id, display_name="Ctx")
    db.add(profile)
    await db.commit()
    return profile


async def _register(client: AsyncClient, email="learner@example.com") -> str:
    resp = await client.post(
        "/auth/register", json={"email": email, "password": "igbo1234", "display_name": "Learner"}
    )
    return resp.json()["access_token"]


async def _load_profile_by_email(db: AsyncSession, email: str) -> LearnerProfile:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    return (await db.execute(select(LearnerProfile).where(LearnerProfile.user_id == user.id))).scalar_one()


# --- Context builder ---------------------------------------------------


async def test_context_includes_unit_and_lesson_when_lesson_given(db_session: AsyncSession):
    lesson, _, _ = await _seed_lesson(db_session)
    profile = await _seed_bare_profile(db_session, "ctx@example.com")

    context = await build_tutor_context(db_session, profile, lesson.id)
    assert context.unit_title == "First Words"
    assert context.lesson_title == "Greetings"
    assert context.lesson_objective == "Greet someone"
    assert "Ndewo" in context.relevant_vocabulary


async def test_performance_signal_is_new_with_no_attempts(db_session: AsyncSession):
    profile = await _seed_bare_profile(db_session, "new@example.com")
    context = await build_tutor_context(db_session, profile, None)
    assert context.performance_signal == "new"


async def test_performance_signal_reflects_recent_incorrect_attempts(
    client: AsyncClient, db_session: AsyncSession
):
    _, exercise, _ = await _seed_lesson(db_session)
    token = await _register(client, "struggling@example.com")
    await client.post(
        f"/exercises/{exercise.id}/attempt",
        json={"answer": "wrong"},
        headers={"Authorization": f"Bearer {token}"},
    )

    profile = await _load_profile_by_email(db_session, "struggling@example.com")
    context = await build_tutor_context(db_session, profile, None)
    assert context.performance_signal == "struggling"


async def test_performance_signal_is_comfortable_after_mostly_correct_attempts(
    client: AsyncClient, db_session: AsyncSession
):
    _, exercise, _ = await _seed_lesson(db_session)
    token = await _register(client, "comfortable@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(4):
        await client.post(f"/exercises/{exercise.id}/attempt", json={"answer": "Ndewo"}, headers=headers)

    profile = await _load_profile_by_email(db_session, "comfortable@example.com")
    context = await build_tutor_context(db_session, profile, None)
    assert context.performance_signal == "comfortable"


# --- Conversation resume -------------------------------------------------


async def test_latest_conversation_is_null_before_any_messages(client: AsyncClient):
    token = await _register(client)
    resp = await client.get("/api/ai/conversation", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() is None


async def test_latest_conversation_returns_history_after_messages(client: AsyncClient):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/ai/tutor", json={"message": "Ndewo"}, headers=headers)

    resp = await client.get("/api/ai/conversation", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "learner"
    assert body["messages"][0]["content"] == "Ndewo"


async def test_latest_conversation_is_scoped_to_the_authenticated_learner(client: AsyncClient):
    token_a = await _register(client, "a@example.com")
    token_b = await _register(client, "b@example.com")

    await client.post(
        "/api/ai/tutor", json={"message": "Hello from A"}, headers={"Authorization": f"Bearer {token_a}"}
    )

    resp_b = await client.get("/api/ai/conversation", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.json() is None  # B has no conversations of their own


async def test_latest_conversation_requires_authentication(client: AsyncClient):
    resp = await client.get("/api/ai/conversation")
    assert resp.status_code == 401


# --- Learning events -------------------------------------------------------


async def test_exercise_attempt_logs_correct_or_incorrect_event(
    client: AsyncClient, db_session: AsyncSession
):
    _, exercise, _ = await _seed_lesson(db_session)
    token = await _register(client)
    await client.post(
        f"/exercises/{exercise.id}/attempt",
        json={"answer": "Ndewo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    result = await db_session.execute(select(LearningEvent.event_type))
    event_types = [row[0] for row in result.all()]
    assert "exercise_correct" in event_types


async def test_tutor_message_logs_conversation_started_then_tutor_message_sent(
    client: AsyncClient, db_session: AsyncSession
):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}
    first = await client.post("/api/ai/tutor", json={"message": "Ndewo"}, headers=headers)
    conv_id = first.json()["conversation_id"]
    await client.post(
        "/api/ai/tutor", json={"message": "Daalụ", "conversation_id": conv_id}, headers=headers
    )

    result = await db_session.execute(select(LearningEvent.event_type).order_by(LearningEvent.created_at))
    event_types = [row[0] for row in result.all()]
    assert event_types == ["conversation_started", "tutor_message_sent"]


async def test_lesson_completion_logs_vocabulary_encountered_event(
    client: AsyncClient, db_session: AsyncSession
):
    lesson, _, _ = await _seed_lesson(db_session)
    token = await _register(client)
    await client.post(f"/lessons/{lesson.id}/complete", headers={"Authorization": f"Bearer {token}"})

    result = await db_session.execute(select(LearningEvent.event_type))
    event_types = [row[0] for row in result.all()]
    assert "vocabulary_encountered" in event_types
