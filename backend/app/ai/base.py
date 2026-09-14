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
    what Phase 5 section 11 means by not sending unlimited/unnecessary
    state to the model.
    """

    learner_level: str
    lesson_title: str | None = None
    lesson_objective: str | None = None
    relevant_vocabulary: list[str] = field(default_factory=list)


@dataclass
class TutorReply:
    """Structured tutor output. Only `message` is guaranteed — the other
    fields are populated when a provider can confidently produce them, and
    are None otherwise. MockAIProvider only ever fills `message`; a real
    NATLaSProvider may fill more once response-parsing is built out, but
    even then these must come from parsed, validated model output, never be
    invented by application code and attributed to the model."""

    message: str
    provider: str  # identifies which provider produced this — never spoofed
    correction: str | None = None
    explanation: str | None = None
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
