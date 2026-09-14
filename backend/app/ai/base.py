from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TutorMessage:
    role: str  # "learner" | "tutor"
    content: str


@dataclass
class TutorContext:
    """Learner context assembled by application logic (see
    app/services/tutor_context.py) and handed to the provider — the
    provider never queries the database itself. Keeping this a small,
    explicit, serializable object (not "the whole learner record") is
    what Phase 5/6 mean by not sending unlimited/unnecessary state to
    the model.

    performance_signal is computed by application code from recent
    ExerciseAttempt correctness (see tutor_context.py) — it is never
    something the LLM reports about itself, and the app never lets a model
    response feed back into it. That's what keeps "the LLM invents mastery
    scores" (explicitly ruled out in Phase 6) structurally impossible.
    """

    learner_level: str
    unit_title: str | None = None
    lesson_title: str | None = None
    lesson_objective: str | None = None
    relevant_vocabulary: list[str] = field(default_factory=list)
    known_weaknesses: list[str] = field(default_factory=list)
    # "new" | "struggling" | "developing" | "comfortable" — see
    # tutor_context.py for how this is derived.
    performance_signal: str = "new"


@dataclass
class TutorReply:
    """Structured tutor output. Only `message` is guaranteed — every other
    field is populated when a provider can confidently produce it, and is
    None otherwise. MockAIProvider fills a few for contract-testing
    purposes but is always clearly fixture data; NATLaSProvider only fills
    fields it actually parsed from the model, never invents structure on
    top of plain text."""

    message: str
    provider: str  # identifies which provider produced this — never spoofed
    correction: str | None = None
    explanation: str | None = None
    hint: str | None = None
    example: str | None = None
    follow_up_question: str | None = None
    learning_action: str | None = None
    suggested_exercise: str | None = None
    language_level: str | None = None


class AIProvider(ABC):
    """Contract for anything that can act as the Igbo AI tutor's language engine.

    This is intentionally narrow: an AIProvider only generates text given
    conversational + learner context. It does NOT decide curriculum, grade
    exercises, or manage learner state — that's application logic, and stays
    that way even once N-ATLaS is wired in (see Phase 1 architecture notes).
    """

    name: str = "base"

    @abstractmethod
    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
        context: TutorContext,
    ) -> TutorReply:
        """Generate the tutor's next conversational turn.

        Implementations must raise AIProviderError/AIProviderTimeout
        (app/ai/errors.py) on failure rather than letting a raw
        network/parsing exception escape — that's what lets the API layer
        respond cleanly instead of a bare 500.
        """
        raise NotImplementedError
