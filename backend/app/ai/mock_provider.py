import random

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply

# A small set of canned exchanges so the Conversation UI has something real
# to respond with. This is NOT Igbo-language intelligence — it's fixture
# data for building and testing the product around, per Phase 2 scope.
_GREETING_REPLIES = [
    "Ndewo! Nice greeting. Try asking me how I'm doing: \"Kedu ka ị mere?\"",
    "Nnọọ! That's a solid start. Can you tell me your name in Igbo?",
]
_DEFAULT_REPLIES = [
    "Good attempt. In natural Igbo, that phrase is usually said a little differently — want the correction?",
    "I understood you. Let's build on that — try using it in a full sentence.",
    "Daalụ for practicing! Once N-ATLaS is connected, replies here will get much richer.",
]


class MockAIProvider(AIProvider):
    """Active by default. Returns canned, clearly-labeled responses so the
    rest of the product (UI, API contract, conversation flow) can be built
    and tested without a live N-ATLaS endpoint. Never fails, never times
    out — that's what makes it a safe development fallback."""

    name = "mock"

    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
        context: TutorContext,
    ) -> TutorReply:
        lowered = message.strip().lower()
        if any(greeting in lowered for greeting in ("ndewo", "nnọọ", "hello", "hi")):
            reply = random.choice(_GREETING_REPLIES)
        else:
            reply = random.choice(_DEFAULT_REPLIES)

        # Light, honest use of context: mention it's aware of the lesson
        # without inventing any Igbo-language content from it.
        if context.lesson_title and random.random() < 0.34:
            reply += f" (We're working on \"{context.lesson_title}\" right now.)"

        return TutorReply(message=reply, provider=self.name)
