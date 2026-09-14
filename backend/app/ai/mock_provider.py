import random

from app.ai.base import AIProvider, TutorContext, TutorMessage, TutorReply

# A small set of canned exchanges so the Conversation UI has something real
# to respond with. This is NOT Igbo-language intelligence — it's fixture
# data for building and testing the product (and the full response
# contract: hint/example/follow_up_question/etc) around, per Phase 2 scope.
_GREETING_REPLIES = [
    "Ndewo! Nice greeting. Try asking me how I'm doing: \"Kedu ka ị mere?\"",
    "Nnọọ! That's a solid start. Can you tell me your name in Igbo?",
]
_DEFAULT_REPLIES = [
    "Good attempt. In natural Igbo, that phrase is usually said a little differently — want the correction?",
    "I understood you. Let's build on that — try using it in a full sentence.",
    "Daalụ for practicing! Once N-ATLaS is connected, replies here will get much richer.",
]
_STRUGGLING_ENCOURAGEMENT = [
    "No rush — let's slow down and take this one small step at a time.",
    "That's alright, this is genuinely tricky. Let's try something a bit simpler first.",
]
_FOLLOW_UPS = [
    "Can you try using that in a full sentence?",
    "What do you think the response to that would be?",
]


class MockAIProvider(AIProvider):
    """Active by default. Returns canned, clearly-labeled responses so the
    rest of the product (UI, API contract, conversation flow) can be built
    and tested without a live N-ATLaS endpoint. Never fails, never times
    out — that's what makes it a safe development fallback.

    The context-awareness here (mentioning the lesson, softening tone when
    performance_signal is "struggling") is superficial pattern-matching for
    demo/testing purposes, not real language understanding — it never
    generates or corrects actual Igbo content beyond the fixed phrases
    above.
    """

    name = "mock"

    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
        context: TutorContext,
    ) -> TutorReply:
        lowered = message.strip().lower()

        if context.performance_signal == "struggling":
            reply_text = random.choice(_STRUGGLING_ENCOURAGEMENT)
        elif any(greeting in lowered for greeting in ("ndewo", "nnọọ", "hello", "hi")):
            reply_text = random.choice(_GREETING_REPLIES)
        else:
            reply_text = random.choice(_DEFAULT_REPLIES)

        if context.lesson_title and random.random() < 0.34:
            reply_text += f" (We're working on \"{context.lesson_title}\" right now.)"

        example = None
        if context.relevant_vocabulary:
            example = f"{context.relevant_vocabulary[0]} — try using this word in your next message."

        return TutorReply(
            message=reply_text,
            provider=self.name,
            example=example,
            follow_up_question=random.choice(_FOLLOW_UPS) if random.random() < 0.5 else None,
        )
