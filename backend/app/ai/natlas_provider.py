from app.ai.base import AIProvider, TutorMessage, TutorReply
from app.core.config import Settings


class NATLaSProvider(AIProvider):
    """Placeholder for the real N-ATLaS integration (Phase 5).

    Per Phase 1 research: N-ATLaS (NCAIR1/N-ATLaS, Llama-3-8B fine-tune) has
    no hosted inference API as of Phase 1 — this provider will call a
    self-hosted inference endpoint (e.g. a GPU server running the model via
    transformers/vLLM) once one exists. Until then this class exists only to
    define the contract and keep the app architected around it.

    Deliberately unimplemented: calling this must fail loudly rather than
    silently pretending to be N-ATLaS.
    """

    name = "natlas"

    def __init__(self, settings: Settings):
        self._settings = settings

    async def generate_tutor_reply(
        self,
        history: list[TutorMessage],
        message: str,
    ) -> TutorReply:
        raise NotImplementedError(
            "NATLaSProvider is not implemented yet — see Phase 5. "
            "Set AI_PROVIDER=mock (default) until then."
        )
