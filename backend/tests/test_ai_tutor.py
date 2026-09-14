from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply
from app.ai.errors import AIProviderError, AIProviderTimeout
from app.ai.factory import get_ai_provider
from app.main import app
from app.models import Conversation, ConversationMessage


async def _register(client: AsyncClient, email="learner@example.com") -> str:
    resp = await client.post(
        "/auth/register", json={"email": email, "password": "igbo1234", "display_name": "Learner"}
    )
    return resp.json()["access_token"]


async def test_tutor_requires_authentication(client: AsyncClient):
    resp = await client.post("/api/ai/tutor", json={"message": "Ndewo"})
    assert resp.status_code == 401


async def test_mock_provider_responds(client: AsyncClient):
    token = await _register(client)
    resp = await client.post(
        "/api/ai/tutor", json={"message": "Ndewo"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["message"]
    assert "conversation_id" in body


async def test_conversation_persists_both_messages(client: AsyncClient, db_session: AsyncSession):
    token = await _register(client)
    resp = await client.post(
        "/api/ai/tutor", json={"message": "Ndewo"}, headers={"Authorization": f"Bearer {token}"}
    )
    conversation_id = resp.json()["conversation_id"]

    result = await db_session.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
    )
    messages = result.scalars().all()
    assert len(messages) == 2
    assert messages[0].role == "learner"
    assert messages[0].content == "Ndewo"
    assert messages[1].role == "tutor"


async def test_second_message_continues_same_conversation(client: AsyncClient, db_session: AsyncSession):
    token = await _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post("/api/ai/tutor", json={"message": "Ndewo"}, headers=headers)
    conv_id = first.json()["conversation_id"]

    second = await client.post(
        "/api/ai/tutor",
        json={"message": "Daalụ", "conversation_id": conv_id},
        headers=headers,
    )
    assert second.json()["conversation_id"] == conv_id

    result = await db_session.execute(
        select(ConversationMessage).where(ConversationMessage.conversation_id == conv_id)
    )
    assert len(result.scalars().all()) == 4


async def test_learner_cannot_continue_another_learners_conversation(client: AsyncClient):
    token_a = await _register(client, "a@example.com")
    token_b = await _register(client, "b@example.com")

    resp_a = await client.post(
        "/api/ai/tutor", json={"message": "Ndewo"}, headers={"Authorization": f"Bearer {token_a}"}
    )
    conv_id = resp_a.json()["conversation_id"]

    # B tries to continue A's conversation id -- should silently get a NEW
    # conversation of their own, never A's history or content.
    resp_b = await client.post(
        "/api/ai/tutor",
        json={"message": "Hello", "conversation_id": conv_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    assert resp_b.json()["conversation_id"] != conv_id


async def test_provider_error_returns_clean_503_not_a_crash(client: AsyncClient):
    class FailingProvider(AIProvider):
        name = "failing"

        async def generate_tutor_reply(self, history, message, context):
            raise AIProviderError("simulated failure")

    app.dependency_overrides[get_ai_provider] = lambda: FailingProvider()
    try:
        token = await _register(client, "fail@example.com")
        resp = await client.post(
            "/api/ai/tutor", json={"message": "Ndewo"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 503
        assert "detail" in resp.json()
    finally:
        del app.dependency_overrides[get_ai_provider]


async def test_provider_timeout_returns_clean_504(client: AsyncClient):
    class SlowProvider(AIProvider):
        name = "slow"

        async def generate_tutor_reply(self, history, message, context):
            raise AIProviderTimeout("simulated timeout")

    app.dependency_overrides[get_ai_provider] = lambda: SlowProvider()
    try:
        token = await _register(client, "timeout@example.com")
        resp = await client.post(
            "/api/ai/tutor", json={"message": "Ndewo"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 504
    finally:
        del app.dependency_overrides[get_ai_provider]


async def test_failed_request_does_not_persist_partial_messages(client: AsyncClient, db_session: AsyncSession):
    class FailingProvider(AIProvider):
        name = "failing"

        async def generate_tutor_reply(self, history, message, context):
            raise AIProviderError("simulated failure")

    app.dependency_overrides[get_ai_provider] = lambda: FailingProvider()
    try:
        token = await _register(client, "nopartial@example.com")
        await client.post(
            "/api/ai/tutor", json={"message": "Ndewo"}, headers={"Authorization": f"Bearer {token}"}
        )
        result = await db_session.execute(select(ConversationMessage))
        assert len(result.scalars().all()) == 0
    finally:
        del app.dependency_overrides[get_ai_provider]
