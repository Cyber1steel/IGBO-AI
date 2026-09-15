import os
from types import SimpleNamespace

import pytest
from httpx import AsyncClient

from app.ai.base import TutorContext
from app.ai.errors import AIProviderError
from app.ai.factory import get_ai_provider
from app.ai.gemini_provider import GeminiProvider, _GeminiTutorReplySchema
from app.core.config import Settings, get_settings
from app.main import app


def _make_provider(api_key: str | None = "test-key") -> GeminiProvider:
    return GeminiProvider(Settings(gemini_api_key=api_key))


def _fake_response(parsed=None, text: str | None = None):
    """A minimal stand-in for types.GenerateContentResponse -- _parse_response
    only reads .parsed and .text, so a real SDK object isn't needed to test
    the parsing logic in isolation."""
    return SimpleNamespace(parsed=parsed, text=text)


# --- Response parsing (pure, no network) ------------------------------------


def test_parses_well_formed_structured_reply():
    provider = _make_provider()
    schema = _GeminiTutorReplySchema(message="Ndewo means hello.", correction=None)
    reply = provider._parse_response(_fake_response(parsed=schema))
    assert reply.message == "Ndewo means hello."
    assert reply.provider == "general"
    assert reply.correction is None


def test_parses_structured_reply_with_correction_and_example():
    provider = _make_provider()
    schema = _GeminiTutorReplySchema(
        message="Close!",
        correction="Ndewo",
        explanation="That is the greeting form.",
        example="Ndewo, kedu?",
        follow_up_question="Can you try it?",
    )
    reply = provider._parse_response(_fake_response(parsed=schema))
    assert reply.correction == "Ndewo"
    assert reply.explanation == "That is the greeting form."
    assert reply.example == "Ndewo, kedu?"
    assert reply.follow_up_question == "Can you try it?"


def test_falls_back_to_raw_text_when_structured_parsing_is_empty():
    provider = _make_provider()
    reply = provider._parse_response(_fake_response(parsed=None, text="Ndewo just means hello."))
    assert reply.message == "Ndewo just means hello."
    assert reply.correction is None


def test_raises_when_structured_message_is_blank():
    provider = _make_provider()
    schema = _GeminiTutorReplySchema(message="   ")
    with pytest.raises(AIProviderError):
        provider._parse_response(_fake_response(parsed=schema))


def test_raises_when_both_parsed_and_text_are_empty():
    provider = _make_provider()
    with pytest.raises(AIProviderError):
        provider._parse_response(_fake_response(parsed=None, text=None))


def test_raises_when_text_is_only_whitespace():
    provider = _make_provider()
    with pytest.raises(AIProviderError):
        provider._parse_response(_fake_response(parsed=None, text="   "))


# --- Conversation formatting (pure, no network) -----------------------------


def test_history_roles_map_to_gemini_user_and_model():
    from app.ai.base import TutorMessage

    provider = _make_provider()
    history = [TutorMessage(role="learner", content="hi"), TutorMessage(role="tutor", content="Ndewo!")]
    contents = provider._build_contents(history, "next message")

    assert contents[0]["role"] == "user"
    assert contents[1]["role"] == "model"  # NOT "assistant" -- Gemini-specific
    assert contents[-1] == {"role": "user", "parts": [{"text": "next message"}]}


# --- Missing configuration (no network required) -----------------------------


async def test_raises_immediately_when_api_key_missing():
    provider = _make_provider(api_key=None)
    with pytest.raises(AIProviderError):
        await provider.generate_tutor_reply([], "hello", TutorContext(learner_level="beginner"))


async def test_tutor_endpoint_fails_cleanly_with_no_gemini_key_configured(client: AsyncClient):
    # The test settings never set GEMINI_API_KEY, so AI_PROVIDER=general
    # here exercises the real missing-key path end to end, not a mock.
    app.dependency_overrides[get_ai_provider] = lambda: _make_provider(api_key=None)
    try:
        reg = await client.post(
            "/auth/register",
            json={"email": "nogem@example.com", "password": "igbo1234", "display_name": "NoGem"},
        )
        token = reg.json()["access_token"]
        resp = await client.post(
            "/api/ai/tutor", json={"message": "hello"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 503
    finally:
        del app.dependency_overrides[get_ai_provider]


# --- Provider selection -------------------------------------------------


def test_factory_selects_gemini_for_general_provider():
    get_settings.cache_clear()
    os.environ["AI_PROVIDER"] = "general"
    get_ai_provider.cache_clear()
    try:
        provider = get_ai_provider()
        assert provider.name == "general"
        assert isinstance(provider, GeminiProvider)
    finally:
        del os.environ["AI_PROVIDER"]
        get_settings.cache_clear()
        get_ai_provider.cache_clear()
