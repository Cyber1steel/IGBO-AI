from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TutorMessage:
    role: str  # "learner" | "tutor"
    content: str


@dataclass
class TutorReply:
    message: str
    provider: str  # identifies which provider produced this — never spoofed


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
    ) -> TutorReply:
        """Generate the tutor's next conversational turn."""
        raise NotImplementedError
