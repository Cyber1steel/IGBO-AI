import asyncio
import logging
import re

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply
from app.ai.errors import AIProviderError, AIProviderQuotaError, AIProviderTimeout
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
_MAX_OUTPUT_TOKENS = 900
_MAX_QUOTA_RETRY_SECONDS = 5.0
logger = logging.getLogger(__name__)


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
    learning_action: str | None = None
    suggested_exercise: str | None = None
    language_level: str | None = None


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
            temperature=0.5,
        )

        async def request():
            return await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self._settings.gemini_model, contents=contents, config=config
                ),
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )

        try:
            response = await request()
        except asyncio.TimeoutError as exc:
            raise AIProviderTimeout(f"AI tutor did not respond within {_REQUEST_TIMEOUT_SECONDS}s") from exc
        except errors.ClientError as exc:
            if exc.code == 401 or exc.code == 403:
                raise AIProviderError(f"AI tutor rejected the configured API key ({exc.code})") from exc
            if exc.code == 429:
                category, retry_after_seconds = _classify_gemini_quota_error(exc)
                logger.warning(
                    "Gemini tutor quota response provider=%s model=%s status=%s category=%s "
                    "retry_after_seconds=%s",
                    self.name,
                    self._settings.gemini_model,
                    exc.code,
                    category,
                    retry_after_seconds,
                )
                if category in {"requests_per_minute", "tokens_per_minute"} and (
                    retry_after_seconds is not None and retry_after_seconds <= _MAX_QUOTA_RETRY_SECONDS
                ):
                    try:
                        await asyncio.sleep(retry_after_seconds)
                        response = await request()
                    except errors.ClientError as retry_exc:
                        if retry_exc.code == 429:
                            category, retry_after_seconds = _classify_gemini_quota_error(retry_exc)
                        else:
                            raise
                    except asyncio.TimeoutError as retry_exc:
                        raise AIProviderTimeout(
                            f"AI tutor did not respond within {_REQUEST_TIMEOUT_SECONDS}s"
                        ) from retry_exc
                    else:
                        return self._parse_response(response)
                raise AIProviderQuotaError(
                    _quota_message(category, retry_after_seconds), category, retry_after_seconds
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
                learning_action=_clean(parsed.learning_action),
                suggested_exercise=_clean(parsed.suggested_exercise),
                language_level=_clean(parsed.language_level),
            )

        raw_text = response.text
        if not raw_text or not raw_text.strip():
            raise AIProviderError("AI tutor returned an empty response")
        return TutorReply(message=raw_text.strip(), provider=self.name)


def _classify_gemini_quota_error(exc: errors.ClientError) -> tuple[str, float | None]:
    """Classify Google's structured 429 metadata without retaining its body."""
    details = getattr(exc, "details", {})
    error = details.get("error", details) if isinstance(details, dict) else {}
    error = error if isinstance(error, dict) else {}
    fragments = [str(error.get("message", "")), str(error.get("status", ""))]
    retry_after = _retry_after_from_headers(getattr(getattr(exc, "response", None), "headers", {}))

    for item in error.get("details", []):
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("@type", ""))
        if item_type.endswith("RetryInfo"):
            retry_after = retry_after or _duration_seconds(item.get("retryDelay"))
        if item_type.endswith("ErrorInfo"):
            fragments.extend([str(item.get("reason", "")), str(item.get("domain", ""))])
            fragments.extend(str(value) for value in (item.get("metadata") or {}).values())
        if item_type.endswith("QuotaFailure"):
            for violation in item.get("violations", []):
                if isinstance(violation, dict):
                    fragments.extend(str(violation.get(key, "")) for key in ("description", "quotaMetric", "quotaId"))

    text = " ".join(fragments).lower()
    if any(term in text for term in ("billing", "active billing account", "paid tier")):
        category = "billing_or_quota_configuration"
    elif any(term in text for term in ("free tier", "free_tier", "limit: 0", "model quota")):
        category = "free_tier_model_quota"
    elif any(term in text for term in ("daily", "per day", "quota_day")):
        category = "daily_quota_exhausted"
    elif any(term in text for term in ("token", "tokens", "tpm")):
        category = "tokens_per_minute"
    elif any(term in text for term in ("request", "requests", "rpm", "rate_limit")):
        category = "requests_per_minute"
    else:
        category = "quota_or_rate_limit"
    return category, retry_after


def _retry_after_from_headers(headers) -> float | None:
    try:
        return float(headers.get("retry-after")) if headers.get("retry-after") else None
    except (TypeError, ValueError):
        return None


def _duration_seconds(value) -> float | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)s", value.strip())
    return float(match.group(1)) if match else None


def _quota_message(category: str, retry_after_seconds: float | None) -> str:
    if category in {"daily_quota_exhausted", "free_tier_model_quota", "billing_or_quota_configuration"}:
        return "The AI provider quota is exhausted or unavailable for this model. Check Google AI Studio quota and billing settings."
    if retry_after_seconds is not None:
        return f"The AI provider is rate limited. Please retry after {retry_after_seconds:g} seconds."
    return "The AI provider is rate limited. Please try again later."

def _clean(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
