import json

import httpx

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply
from app.ai.errors import AIProviderError, AIProviderTimeout
from app.ai.prompts import build_tutor_system_prompt
from app.core.config import Settings

# Anthropic's Messages API specifically: it's the general LLM API reachable
# from this project's dev/sandbox network configuration, well-documented,
# and returns clean, instructable JSON when asked. If you'd rather use a
# different vendor (OpenAI, etc.), only _build_payload/_parse_response and
# the request URL/headers below need to change -- nothing else in the app
# (orchestrator, factory, tutor endpoint) knows or cares which one is used.
_REQUEST_TIMEOUT_SECONDS = 30.0
_MAX_TOKENS = 500
_ANTHROPIC_VERSION = "2023-06-01"

# Asking for JSON explicitly (rather than parsing free text) is what lets
# this provider reliably populate correction/hint/example/follow_up_question
# -- a capability NATLaSProvider deliberately doesn't attempt yet, since we
# have no evidence a self-hosted N-ATLaS deployment follows format
# instructions reliably. A general-purpose model like this one generally
# does, which is exactly the practical advantage of using one here.
_JSON_INSTRUCTIONS = """
Respond with ONLY a single JSON object (no markdown fences, no commentary
outside the JSON), with these keys:
{
  "message": "your main reply, required",
  "correction": "corrected form if they made a meaningful Igbo mistake, else null",
  "explanation": "brief why, only if correction is set, else null",
  "hint": "a hint if they're working through an exercise and haven't gotten it yet, else null",
  "example": "a short example sentence/phrase if it helps, else null",
  "follow_up_question": "a natural follow-up question if one fits, else null"
}
Omit fields you don't need by setting them to null. Keep "message" natural
and conversational -- it's the only field always shown; the others are
optional extras the app may display alongside it.
"""


class GeneralLLMProvider(AIProvider):
    """A real, general-purpose LLM used as the tutor's language engine.
    Genuinely reads and responds to what the learner wrote -- this is what
    replaces MockAIProvider's fixed-response-set behavior when configured.
    """

    name = "general"

    def __init__(self, settings: Settings):
        self._settings = settings

    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
        context: TutorContext,
    ) -> TutorReply:
        if not self._settings.general_llm_api_key:
            raise AIProviderError(
                "AI_PROVIDER=general but GENERAL_LLM_API_KEY is not set. "
                "Add a key to .env, or set AI_PROVIDER=mock for local development "
                "without a real AI backend."
            )

        system_prompt = build_tutor_system_prompt(context) + "\n" + _JSON_INSTRUCTIONS
        messages = [
            {"role": "assistant" if m.role == "tutor" else "user", "content": m.content}
            for m in history[-8:]
        ]
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self._settings.general_llm_model,
            "max_tokens": _MAX_TOKENS,
            "system": system_prompt,
            "messages": messages,
        }
        headers = {
            "x-api-key": self._settings.general_llm_api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        url = f"{self._settings.general_llm_base_url.rstrip('/')}/v1/messages"

        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AIProviderTimeout(f"AI tutor did not respond within {_REQUEST_TIMEOUT_SECONDS}s") from exc
        except httpx.HTTPStatusError as exc:
            # Never leak the key; do surface auth vs. rate-limit vs. other,
            # since those need different fixes and this message only ever
            # reaches server logs / the generic 503 the API layer returns.
            status = exc.response.status_code
            if status == 401:
                raise AIProviderError("AI tutor rejected the configured API key (401)") from exc
            if status == 429:
                raise AIProviderError("AI tutor rate limit exceeded (429)") from exc
            raise AIProviderError(f"AI tutor returned {status}") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Could not reach AI tutor provider: {exc}") from exc

        return self._parse_response(response)

    def _parse_response(self, response: httpx.Response) -> TutorReply:
        try:
            data = response.json()
            raw_text = data["content"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            raise AIProviderError("AI tutor returned an unrecognized response shape") from exc

        if not isinstance(raw_text, str) or not raw_text.strip():
            raise AIProviderError("AI tutor returned an empty response")

        parsed = self._try_parse_json(raw_text)
        if parsed is None:
            # Model didn't follow the JSON format for some reason -- degrade
            # gracefully to plain text rather than failing the whole turn.
            return TutorReply(message=raw_text.strip(), provider=self.name)

        message = parsed.get("message")
        if not isinstance(message, str) or not message.strip():
            raise AIProviderError("AI tutor's JSON response had no usable message")

        return TutorReply(
            message=message.strip(),
            provider=self.name,
            correction=_clean(parsed.get("correction")),
            explanation=_clean(parsed.get("explanation")),
            hint=_clean(parsed.get("hint")),
            example=_clean(parsed.get("example")),
            follow_up_question=_clean(parsed.get("follow_up_question")),
        )

    @staticmethod
    def _try_parse_json(text: str) -> dict | None:
        text = text.strip()
        # Tolerate the model wrapping JSON in a markdown fence despite
        # instructions not to -- strip it rather than failing outright.
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return None
        return result if isinstance(result, dict) else None


def _clean(value) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
