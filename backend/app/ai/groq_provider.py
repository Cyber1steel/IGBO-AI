import json
import logging
import time

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply
from app.ai.errors import AIProviderError, AIProviderTimeout
from app.ai.prompts import build_tutor_system_prompt
from app.core.config import Settings

_REQUEST_TIMEOUT_SECONDS = 30.0
_MAX_OUTPUT_TOKENS = 900
logger = logging.getLogger(__name__)

_RESPONSE_FIELDS = (
    "message",
    "correction",
    "explanation",
    "hint",
    "example",
    "follow_up_question",
    "learning_action",
    "suggested_exercise",
    "language_level",
)


class GroqProvider(AIProvider):
    """Groq chat-completions provider using the shared tutor contract."""

    name = "groq"

    def __init__(self, settings: Settings):
        self._settings = settings

    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
        context: TutorContext,
    ) -> TutorReply:
        if not self._settings.groq_api_key:
            raise AIProviderError(
                "AI_PROVIDER=groq but GROQ_API_KEY is not set. Add a Groq API key to .env."
            )

        messages = self._build_messages(history, message, context)
        client = AsyncGroq(
            api_key=self._settings.groq_api_key,
            timeout=_REQUEST_TIMEOUT_SECONDS,
            max_retries=0,
        )
        started = time.monotonic()
        try:
            response = await client.chat.completions.create(
                model=self._settings.groq_model,
                messages=messages,
                temperature=0.5,
                max_tokens=_MAX_OUTPUT_TOKENS,
                response_format={"type": "json_object"},
            )
        except APITimeoutError as exc:
            raise AIProviderTimeout(
                f"Groq tutor did not respond within {_REQUEST_TIMEOUT_SECONDS}s"
            ) from exc
        except RateLimitError as exc:
            self._log_failure("rate_limit", exc, started)
            raise AIProviderError("Groq rate limit reached. Please try again shortly.") from exc
        except (AuthenticationError, PermissionDeniedError) as exc:
            self._log_failure("authentication", exc, started)
            raise AIProviderError("Groq rejected the configured API key.") from exc
        except NotFoundError as exc:
            self._log_failure("model_not_found", exc, started)
            raise AIProviderError("The configured Groq model is unavailable.") from exc
        except BadRequestError as exc:
            self._log_failure("bad_request", exc, started)
            raise AIProviderError("Groq rejected the tutor request configuration.") from exc
        except APIConnectionError as exc:
            self._log_failure("connection", exc, started)
            raise AIProviderError("Could not connect to Groq.") from exc
        except APIStatusError as exc:
            self._log_failure(f"http_{exc.status_code}", exc, started)
            raise AIProviderError(f"Groq returned an API error ({exc.status_code}).") from exc
        finally:
            await client.close()

        reply = self._parse_response(response)
        logger.info(
            "Groq tutor request succeeded provider=%s model=%s response_length=%d elapsed_ms=%.1f",
            self.name,
            self._settings.groq_model,
            len(reply.message),
            (time.monotonic() - started) * 1000,
        )
        return reply

    def _build_messages(
        self, history: list[TutorMessage], message: str, context: TutorContext
    ) -> list[dict]:
        system_prompt = build_tutor_system_prompt(context)
        system_prompt += (
            "\nReturn one JSON object with exactly these optional fields: "
            + ", ".join(_RESPONSE_FIELDS)
            + ". The message field is required. Use null for fields that are not useful."
        )
        messages = [{"role": "system", "content": system_prompt}]
        for item in history[-8:]:
            messages.append(
                {"role": "assistant" if item.role == "tutor" else "user", "content": item.content}
            )
        messages.append({"role": "user", "content": message})
        return messages

    def _parse_response(self, response) -> TutorReply:
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise AIProviderError("Groq returned an unrecognized response shape.") from exc

        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("Groq returned an empty response.")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return TutorReply(message=content.strip(), provider=self.name)

        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("message"), str)
            or not payload["message"].strip()
        ):
            raise AIProviderError("Groq returned a structured response without a usable message.")

        return TutorReply(
            message=payload["message"].strip(),
            provider=self.name,
            **{field: _clean(payload.get(field)) for field in _RESPONSE_FIELDS if field != "message"},
        )

    def _log_failure(self, category: str, exc: Exception, started: float) -> None:
        status_code = getattr(exc, "status_code", None)
        logger.warning(
            "Groq tutor request failed provider=%s model=%s category=%s status=%s elapsed_ms=%.1f",
            self.name,
            self._settings.groq_model,
            category,
            status_code,
            (time.monotonic() - started) * 1000,
        )


def _clean(value) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
