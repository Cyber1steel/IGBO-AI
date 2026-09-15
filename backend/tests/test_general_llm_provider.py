import httpx
import pytest
from httpx import AsyncClient

from app.ai.errors import AIProviderError
from app.ai.factory import get_ai_provider
from app.ai.general_llm_provider import GeneralLLMProvider
from app.core.config import Settings
from app.main import app


def _make_provider(api_key: str | None = "test-key") -> GeneralLLMProvider:
    settings = Settings(general_llm_api_key=api_key)
    return GeneralLLMProvider(settings)


def _fake_response(text: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json={"content": [{"text": text}]},
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
    )


# --- Response parsing (pure, no network) ------------------------------------


def test_parses_well_formed_json_reply():
    provider = _make_provider()
    reply = provider._parse_response(
        _fake_response('{"message": "Ndewo means hello.", "correction": null, "hint": null}')
    )
    assert reply.message == "Ndewo means hello."
    assert reply.provider == "general"
    assert reply.correction is None


def test_parses_json_with_correction_and_example():
    provider = _make_provider()
    reply = provider._parse_response(
        _fake_response(
            '{"message": "Close!", "correction": "Ndewo", "explanation": "That is the greeting form.", '
            '"hint": null, "example": "Ndewo, kedu?", "follow_up_question": "Can you try it?"}'
        )
    )
    assert reply.correction == "Ndewo"
    assert reply.explanation == "That is the greeting form."
    assert reply.example == "Ndewo, kedu?"
    assert reply.follow_up_question == "Can you try it?"


def test_degrades_gracefully_when_model_does_not_return_json():
    provider = _make_provider()
    reply = provider._parse_response(_fake_response("Ndewo just means hello, nothing fancier."))
    assert reply.message == "Ndewo just means hello, nothing fancier."
    assert reply.correction is None


def test_strips_markdown_fence_around_json():
    provider = _make_provider()
    reply = provider._parse_response(_fake_response('```json\n{"message": "Hi there"}\n```'))
    assert reply.message == "Hi there"


def test_raises_when_json_message_field_is_missing():
    provider = _make_provider()
    with pytest.raises(AIProviderError):
        provider._parse_response(_fake_response('{"correction": "Ndewo"}'))


def test_raises_on_empty_response_text():
    provider = _make_provider()
    with pytest.raises(AIProviderError):
        provider._parse_response(_fake_response("   "))


def test_raises_on_unrecognized_response_shape():
    provider = _make_provider()
    bad_response = httpx.Response(
        status_code=200,
        json={"unexpected": "shape"},
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
    )
    with pytest.raises(AIProviderError):
        provider._parse_response(bad_response)


# --- Missing/failed configuration (no network required) ---------------------


async def test_raises_immediately_when_api_key_missing():
    provider = _make_provider(api_key=None)
    with pytest.raises(AIProviderError):
        from app.ai.base import TutorContext

        await provider.generate_tutor_reply([], "hello", TutorContext(learner_level="beginner"))


async def test_tutor_endpoint_fails_cleanly_when_general_provider_misconfigured(client: AsyncClient):
    app.dependency_overrides[get_ai_provider] = lambda: _make_provider(api_key=None)
    try:
        reg = await client.post(
            "/auth/register",
            json={"email": "nogen@example.com", "password": "igbo1234", "display_name": "NoGen"},
        )
        token = reg.json()["access_token"]
        resp = await client.post(
            "/api/ai/tutor", json={"message": "hello"}, headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 503
    finally:
        del app.dependency_overrides[get_ai_provider]


# --- Provider selection -------------------------------------------------


def test_factory_selects_general_provider():
    from app.core.config import get_settings

    get_settings.cache_clear()
    import os

    os.environ["AI_PROVIDER"] = "general"
    get_ai_provider.cache_clear()
    try:
        provider = get_ai_provider()
        assert provider.name == "general"
    finally:
        del os.environ["AI_PROVIDER"]
        get_settings.cache_clear()
        get_ai_provider.cache_clear()
