import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import httpx
from groq import AuthenticationError, RateLimitError

from app.ai.base import TutorContext, TutorMessage
from app.ai.errors import AIProviderError
from app.ai.factory import get_ai_provider
from app.ai.groq_provider import GroqProvider
from app.core.config import Settings, get_settings


def _make_provider(api_key: str | None = "test-key") -> GroqProvider:
    return GroqProvider(Settings(groq_api_key=api_key))


def _fake_response(content: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _error_response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return httpx.Response(status_code, request=request)


def test_groq_builds_shared_tutor_messages():
    provider = _make_provider()
    messages = provider._build_messages(
        [TutorMessage(role="learner", content="Ndewo"), TutorMessage(role="tutor", content="Hello")],
        "Kedu?",
        TutorContext(learner_level="beginner"),
    )
    assert messages[0]["role"] == "system"
    assert "infer the learner's intent" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Ndewo"}
    assert messages[2] == {"role": "assistant", "content": "Hello"}
    assert messages[-1] == {"role": "user", "content": "Kedu?"}


def test_groq_parses_structured_response():
    provider = _make_provider()
    reply = provider._parse_response(
        _fake_response(
            '{"message":"Ndewo!","explanation":"Hello.","follow_up_question":"Kedu?",'
            '"correction":null,"hint":null,"example":null,"learning_action":null,'
            '"suggested_exercise":null,"language_level":"beginner"}'
        )
    )
    assert reply.provider == "groq"
    assert reply.message == "Ndewo!"
    assert reply.explanation == "Hello."
    assert reply.language_level == "beginner"


def test_groq_parses_plain_text_without_faking_fields():
    reply = _make_provider()._parse_response(_fake_response("Ndewo!"))
    assert reply.message == "Ndewo!"
    assert reply.explanation is None


def test_groq_rejects_structured_response_without_message():
    with pytest.raises(AIProviderError, match="usable message"):
        _make_provider()._parse_response(_fake_response('{"message":"  "}'))


@pytest.mark.asyncio
async def test_groq_requires_api_key():
    with pytest.raises(AIProviderError, match="GROQ_API_KEY"):
        await GroqProvider(Settings(groq_api_key=None)).generate_tutor_reply(
            [], "hello", TutorContext(learner_level="beginner")
        )


@pytest.mark.asyncio
async def test_groq_maps_rate_limit_without_sdk_retry():
    response = _error_response(429)
    error = RateLimitError("rate limited", response=response, body={"error": "rate limited"})
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=AsyncMock(side_effect=error))),
        close=AsyncMock(),
    )
    with patch("app.ai.groq_provider.AsyncGroq", return_value=fake_client):
        with pytest.raises(AIProviderError, match="rate limit"):
            await _make_provider().generate_tutor_reply([], "hello", TutorContext(learner_level="beginner"))
    assert fake_client.chat.completions.create.await_count == 1
    fake_client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_groq_maps_invalid_api_key_without_exposing_secret():
    response = _error_response(401)
    error = AuthenticationError("invalid key", response=response, body={"error": "invalid key"})
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=AsyncMock(side_effect=error))),
        close=AsyncMock(),
    )
    with patch("app.ai.groq_provider.AsyncGroq", return_value=fake_client):
        with pytest.raises(AIProviderError, match="rejected") as caught:
            await _make_provider("super-secret").generate_tutor_reply(
                [], "hello", TutorContext(learner_level="beginner")
            )
    assert "super-secret" not in str(caught.value)


def test_factory_selects_groq_and_preserves_existing_providers():
    get_settings.cache_clear()
    get_ai_provider.cache_clear()
    os.environ["AI_PROVIDER"] = "groq"
    try:
        provider = get_ai_provider()
        assert isinstance(provider, GroqProvider)
        assert provider.name == "groq"
    finally:
        del os.environ["AI_PROVIDER"]
        get_settings.cache_clear()
        get_ai_provider.cache_clear()


def test_factory_keeps_gemini_legacy_alias():
    get_settings.cache_clear()
    get_ai_provider.cache_clear()
    os.environ["AI_PROVIDER"] = "general"
    try:
        assert get_ai_provider().name == "general"
    finally:
        del os.environ["AI_PROVIDER"]
        get_settings.cache_clear()
        get_ai_provider.cache_clear()
