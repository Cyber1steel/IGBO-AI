import httpx

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply
from app.ai.errors import AIProviderError, AIProviderTimeout
from app.core.config import Settings

# Per Phase 1 research: N-ATLaS (NCAIR1/N-ATLaS) has no hosted inference API.
# It must be self-hosted. The most practical way to self-host a Llama-3-8B
# fine-tune with a stable HTTP contract is an OpenAI-compatible chat
# completions server (e.g. vLLM's OpenAI-compatible mode, or
# text-generation-inference's OpenAI-compatible route). This client assumes
# that contract: POST {endpoint}/v1/chat/completions. If your actual
# deployment differs, only _build_payload/_parse_response need to change --
# nothing else in the app touches this shape.
_REQUEST_TIMEOUT_SECONDS = 20.0
_MAX_TOKENS = 300


class NATLaSProvider(AIProvider):
    """Real N-ATLaS integration, calling a self-hosted inference endpoint.

    Requires NATLAS_ENDPOINT_URL to be configured. Deliberately does NOT
    fall back to mock behaviour on failure -- a caller asking for N-ATLaS
    and silently getting mock output would be exactly the kind of
    unlabeled substitution the project's own principles rule out. Failures
    raise AIProviderError/AIProviderTimeout for the API layer to handle.
    """

    name = "natlas"

    def __init__(self, settings: Settings):
        self._settings = settings

    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
        context: TutorContext,
    ) -> TutorReply:
        if not self._settings.natlas_endpoint_url:
            raise AIProviderError(
                "AI_PROVIDER=natlas but NATLAS_ENDPOINT_URL is not set. "
                "Point it at a self-hosted N-ATLaS inference server, or set "
                "AI_PROVIDER=mock for local development."
            )

        payload = self._build_payload(history, message, context)
        headers = {"Content-Type": "application/json"}
        if self._settings.natlas_api_key:
            headers["Authorization"] = f"Bearer {self._settings.natlas_api_key}"

        url = f"{self._settings.natlas_endpoint_url.rstrip('/')}/v1/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AIProviderTimeout(f"N-ATLaS did not respond within {_REQUEST_TIMEOUT_SECONDS}s") from exc
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(f"N-ATLaS returned {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise AIProviderError(f"Could not reach N-ATLaS endpoint: {exc}") from exc

        return self._parse_response(response)

    def _build_payload(
        self, history: list[TutorMessage], message: str, context: TutorContext
    ) -> dict:
        system_prompt = self._build_system_prompt(context)
        messages = [{"role": "system", "content": system_prompt}]
        # Context management (Phase 5 section 11): only the last few turns,
        # not the whole conversation -- keeps the prompt bounded regardless
        # of how long a conversation has run.
        for m in history[-8:]:
            role = "assistant" if m.role == "tutor" else "user"
            messages.append({"role": role, "content": m.content})
        messages.append({"role": "user", "content": message})

        return {
            "model": "n-atlas",
            "messages": messages,
            "max_tokens": _MAX_TOKENS,
            "temperature": 0.4,
        }

    def _build_system_prompt(self, context: TutorContext) -> str:
        lines = [
            "You are a patient Igbo language tutor embedded in a structured curriculum. "
            "Teach according to the curriculum -- don't just chat freely about Igbo.",
            "Teach, don't just answer. Give hints before answers when the learner is working "
            "through an exercise. Ask follow-up questions and encourage active practice.",
            "The learner may write in English, Igbo, or a mix of both -- respond naturally to "
            "whichever they use. For beginners, keep explanations primarily in English with light "
            "Igbo exposure; use more Igbo as the learner's level increases.",
            "When correcting a mistake, structure your correction clearly: acknowledge what they "
            "said, give the correct form, briefly explain why, and offer one short example. Only "
            "correct meaningful errors -- do not nitpick minor stylistic differences.",
            "Never invent Igbo vocabulary, grammar rules, or proverbs you are not confident about -- "
            "say you're not sure rather than guessing.",
            f"The learner's current level is: {context.learner_level}.",
        ]
        if context.performance_signal == "struggling":
            lines.append(
                "They've been finding recent exercises difficult -- simplify your language, slow "
                "down, and keep explanations short and encouraging."
            )
        elif context.performance_signal == "comfortable":
            lines.append(
                "They've been doing well recently -- you can introduce slightly more complexity "
                "and use more Igbo."
            )
        if context.unit_title:
            lines.append(f'They are currently in the unit: "{context.unit_title}".')
        if context.lesson_title:
            lines.append(f'They are currently working on the lesson: "{context.lesson_title}".')
        if context.lesson_objective:
            lines.append(f"The lesson's objective is: {context.lesson_objective}.")
        if context.relevant_vocabulary:
            lines.append("Relevant vocabulary for this conversation: " + ", ".join(context.relevant_vocabulary))
        if context.known_weaknesses:
            lines.append(
                "Words they've struggled to retain (reinforce these naturally if relevant, don't "
                "force them): " + ", ".join(context.known_weaknesses)
            )
        if context.lesson_title:
            lines.append(
                "If they ask to talk about something else, you may follow their interest briefly, "
                "but gently steer back toward the current lesson rather than abandoning it entirely."
            )
        return "\n".join(lines)

    def _parse_response(self, response: httpx.Response) -> TutorReply:
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise AIProviderError("N-ATLaS returned an unrecognized response shape") from exc

        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("N-ATLaS returned an empty response")

        # Deliberately not populating correction/explanation/suggested_exercise
        # here: doing so would mean inventing structure the model didn't
        # actually provide. A real structured-output parser (e.g. requesting
        # JSON mode from the inference server) is future work, not a guess
        # bolted on now.
        return TutorReply(message=content.strip(), provider=self.name)
