import asyncio

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply
from app.ai.errors import AIProviderError, AIProviderTimeout
from app.ai.prompts import build_tutor_system_prompt
from app.core.config import Settings

# Google's official Gen AI SDK (`google-genai`, `from google import genai`) --
# NOT the deprecated `google-generativeai` package. Verified against the
# SDK actually installed in this project (v2.23.0), not just docs: Client,
# errors.ClientError/ServerError, GenerateContentConfig's
# system_instruction/response_mime_type/response_schema/http_options
# fields, and GenerateContentResponse.parsed/.text all confirmed present.
#
# Chosen over the Anthropic-based implementation this replaces specifically
# because Gemini has a real, no-credit-card-required free tier on its Flash
# models (see backend/README.md for current free-tier notes and a link to
# check the live model list, since availability shifts over time).
_REQUEST_TIMEOUT_SECONDS = 30.0
_MAX_OUTPUT_TOKENS = 500


class _GeminiTutorReplySchema(BaseModel):
    """Passed as response_schema so Gemini's structured-output mode (the
    officially supported mechanism, not prompt-engineered JSON) constrains
    the reply shape. See GenerateContentResponse.parsed below."""

    message: str
    correction: str | None = None
    explanation: str | None = None
    hint: str | None = None
    example: str | None = None
    follow_up_question: str | None = None


class GeminiProvider(AIProvider):
    """A real, general-purpose LLM (Google Gemini) used as the tutor's
    language engine. Genuinely reads and responds to what the learner
    wrote -- this is what replaces MockAIProvider's fixed-response-set
    behavior when configured."""

    name = "general"

    def __init__(self, settings: Settings):
        self._settings = settings

    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
        context: TutorContext,
    ) -> TutorReply:
        if not self._settings.gemini_api_key:
            raise AIProviderError(
                "AI_PROVIDER=general but GEMINI_API_KEY is not set. "
                "Add a free-tier key from https://aistudio.google.com/apikey to .env, "
                "or set AI_PROVIDER=mock for local development without a real AI backend."
            )

        client = genai.Client(api_key=self._settings.gemini_api_key)
        contents = self._build_contents(history, message)
        config = types.GenerateContentConfig(
            system_instruction=build_tutor_system_prompt(context),
            response_mime_type="application/json",
            response_schema=_GeminiTutorReplySchema,
            max_output_tokens=_MAX_OUTPUT_TOKENS,
            temperature=0.4,
        )

        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self._settings.gemini_model, contents=contents, config=config
                ),
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise AIProviderTimeout(f"AI tutor did not respond within {_REQUEST_TIMEOUT_SECONDS}s") from exc
        except errors.ClientError as exc:
            # Never leak the key -- these messages only ever reach server
            # logs / the generic 503 the API layer returns to the learner.
            if exc.code == 401 or exc.code == 403:
                raise AIProviderError(f"AI tutor rejected the configured API key ({exc.code})") from exc
            if exc.code == 429:
                raise AIProviderError(
                    "AI tutor hit its free-tier rate limit (429) -- wait a moment and try again"
                ) from exc
            raise AIProviderError(f"AI tutor request was rejected ({exc.code})") from exc
        except errors.ServerError as exc:
            raise AIProviderError(f"AI tutor provider is having issues (server error {exc.code})") from exc
        except errors.APIError as exc:
            raise AIProviderError(f"AI tutor request failed: {exc}") from exc

        return self._parse_response(response)

    def _build_contents(self, history: list[TutorMessage], message: str) -> list[dict]:
        # Gemini's roles are "user" and "model" -- NOT "assistant" like
        # OpenAI/Anthropic. Getting this wrong silently breaks turn
        # attribution rather than erroring, so it's worth this comment.
        contents = [
            {"role": "model" if m.role == "tutor" else "user", "parts": [{"text": m.content}]}
            for m in history[-8:]
        ]
        contents.append({"role": "user", "parts": [{"text": message}]})
        return contents

    def _parse_response(self, response: types.GenerateContentResponse) -> TutorReply:
        parsed = response.parsed
        if isinstance(parsed, _GeminiTutorReplySchema):
            if not parsed.message.strip():
                raise AIProviderError("AI tutor's structured response had no usable message")
            return TutorReply(
                message=parsed.message.strip(),
                provider=self.name,
                correction=_clean(parsed.correction),
                explanation=_clean(parsed.explanation),
                hint=_clean(parsed.hint),
                example=_clean(parsed.example),
                follow_up_question=_clean(parsed.follow_up_question),
            )

        # Structured parsing can come back empty if the model was cut off
        # by max_output_tokens (a known SDK behavior) or otherwise declined
        # to follow the schema. Fall back to raw text rather than failing
        # the whole turn -- never crash the tutor endpoint over this.
        raw_text = response.text
        if not raw_text or not raw_text.strip():
            raise AIProviderError("AI tutor returned an empty response")
        return TutorReply(message=raw_text.strip(), provider=self.name)


def _clean(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
