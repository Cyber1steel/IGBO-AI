import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base import AIProvider, TutorMessage, TutorReply
from app.ai.errors import AIProviderError, AIProviderQuotaError, AIProviderTimeout
from app.models import Conversation, ConversationMessage, LearnerProfile, LearningEvent
from app.services.tutor_context import build_tutor_context

# Hard ceiling on how long a single tutor turn may take, independent of
# whatever timeout the provider itself uses internally -- belt and suspenders
# against the UI ever hanging on an AI response (Phase 5/6: no indefinite
# spinners, ever).
PROVIDER_CALL_TIMEOUT_SECONDS = 25

# Only the most recent turns are loaded as conversation history sent to the
# provider (Phase 5/6: don't send unlimited history).
MAX_HISTORY_MESSAGES = 20


class TutorTurnTimeout(Exception):
    """Raised when the provider call doesn't finish within
    PROVIDER_CALL_TIMEOUT_SECONDS -- distinct from AIProviderTimeout so the
    API layer can treat "our own ceiling" and "the provider's own timeout"
    identically without the orchestrator needing to know which one fired."""


class TutorTurnFailed(Exception):
    """Raised when the provider fails for any other reason. Wraps the
    underlying AIProviderError so the API layer has one exception type to
    catch regardless of provider internals."""

    def __init__(self, message: str, provider_error: AIProviderError | None = None):
        super().__init__(message)
        self.provider_error = provider_error


async def handle_tutor_turn(
    db: AsyncSession,
    profile: LearnerProfile,
    provider: AIProvider,
    message: str,
    conversation_id: uuid.UUID | None,
    lesson_id: uuid.UUID | None,
) -> tuple[Conversation, TutorReply]:
    """The orchestrator: Learner -> Learner Context + Current Lesson +
    Relevant Vocabulary + Recent Conversation -> AIProvider -> Tutor
    Response -> Learning Event / Conversation Storage.

    Raises TutorTurnTimeout / TutorTurnFailed on provider failure -- the
    API route only needs to map those to HTTP status codes, not know
    anything about providers, context building, or persistence.
    """
    conversation, history_messages, is_new_conversation = await _get_or_create_conversation(
        db, profile.id, conversation_id
    )
    history = [
        TutorMessage(role=m.role, content=m.content)
        for m in history_messages[-MAX_HISTORY_MESSAGES:]
    ]
    context = await build_tutor_context(db, profile, lesson_id)

    try:
        reply = await asyncio.wait_for(
            provider.generate_tutor_reply(history, message, context),
            timeout=PROVIDER_CALL_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise TutorTurnTimeout() from exc
    except AIProviderTimeout as exc:
        raise TutorTurnTimeout() from exc
    except AIProviderError as exc:
        raise TutorTurnFailed(str(exc), exc) from exc

    await _persist_turn(db, profile.id, conversation.id, message, reply, is_new_conversation)
    return conversation, reply


async def get_latest_conversation(
    db: AsyncSession, learner_id: uuid.UUID
) -> tuple[Conversation, list[ConversationMessage]] | None:
    """For resuming a conversation after the learner leaves and comes back
    (Phase 6 section 11) -- most recently active conversation, with its
    full message history, scoped to this learner only."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.learner_id == learner_id)
        .order_by(Conversation.last_message_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        return None
    return conversation, list(conversation.messages)


async def _persist_turn(
    db: AsyncSession,
    learner_id: uuid.UUID,
    conversation_id: uuid.UUID,
    learner_message: str,
    reply: TutorReply,
    is_new_conversation: bool,
) -> None:
    db.add(ConversationMessage(conversation_id=conversation_id, role="learner", content=learner_message))
    db.add(
        ConversationMessage(
            conversation_id=conversation_id,
            role="tutor",
            content=reply.message,
            message_metadata={"provider": reply.provider},
        )
    )

    events = [
        LearningEvent(
            learner_id=learner_id,
            event_type="conversation_started" if is_new_conversation else "tutor_message_sent",
            payload={"conversation_id": str(conversation_id), "provider": reply.provider},
        )
    ]
    if reply.correction:
        events.append(
            LearningEvent(
                learner_id=learner_id,
                event_type="tutor_correction_given",
                payload={"conversation_id": str(conversation_id)},
            )
        )
    db.add_all(events)
    await db.commit()


async def _get_or_create_conversation(
    db: AsyncSession, learner_id: uuid.UUID, conversation_id: uuid.UUID | None
) -> tuple[Conversation, list[ConversationMessage], bool]:
    """Returns (conversation, its existing messages, whether it's new).

    Existing messages are returned explicitly (eagerly loaded) rather than
    via the ORM relationship after flush — accessing a lazy relationship
    post-flush in async SQLAlchemy raises MissingGreenlet, since lazy
    loading isn't awaited automatically.
    """
    if conversation_id is not None:
        result = await db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.learner_id == learner_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is not None:
            return conversation, list(conversation.messages), len(conversation.messages) == 0
        # Ownership is structural elsewhere in the app; here a mismatched
        # id (wrong learner, or doesn't exist) just starts a fresh one
        # rather than erroring -- a lost conversation_id shouldn't block
        # the learner from continuing to chat.

    conversation = Conversation(learner_id=learner_id)
    db.add(conversation)
    await db.flush()
    return conversation, [], True
