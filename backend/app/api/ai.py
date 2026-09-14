import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.base import AIProvider, TutorMessage
from app.ai.errors import AIProviderError, AIProviderTimeout
from app.ai.factory import get_ai_provider
from app.core.db import get_db
from app.core.deps import get_current_learner_profile
from app.models import Conversation, ConversationMessage, LearnerProfile, LearningEvent
from app.schemas.ai import TutorRequest, TutorResponse
from app.services.tutor_context import build_tutor_context

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Hard ceiling on how long a single tutor turn may take, independent of
# whatever timeout the provider itself uses internally -- belt and suspenders
# against the UI ever hanging on an AI response (Phase 5 section 13).
_PROVIDER_CALL_TIMEOUT_SECONDS = 25

# Only the most recent turns are loaded as conversation history sent to the
# provider (Phase 5 section 11: don't send unlimited history).
_MAX_HISTORY_MESSAGES = 20


@router.post("/tutor", response_model=TutorResponse)
async def tutor_reply(
    request: TutorRequest,
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
    provider: AIProvider = Depends(get_ai_provider),
) -> TutorResponse:
    conversation, history_messages, is_new_conversation = await _get_or_create_conversation(
        db, profile.id, request.conversation_id
    )

    history = [
        TutorMessage(role=m.role, content=m.content)
        for m in history_messages[-_MAX_HISTORY_MESSAGES:]
    ]
    context = await build_tutor_context(db, profile, request.lesson_id)

    try:
        reply = await asyncio.wait_for(
            provider.generate_tutor_reply(history, request.message, context),
            timeout=_PROVIDER_CALL_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The tutor is taking too long to respond. Please try again.",
        )
    except AIProviderTimeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The tutor is taking too long to respond. Please try again.",
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI tutor is unavailable right now. Please try again shortly.",
        ) from exc

    db.add(
        ConversationMessage(conversation_id=conversation.id, role="learner", content=request.message)
    )
    db.add(
        ConversationMessage(
            conversation_id=conversation.id,
            role="tutor",
            content=reply.message,
            message_metadata={"provider": reply.provider},
        )
    )
    db.add(
        LearningEvent(
            learner_id=profile.id,
            event_type="conversation_started" if is_new_conversation else "conversation_message",
            payload={"conversation_id": str(conversation.id), "provider": reply.provider},
        )
    )
    await db.commit()

    return TutorResponse(
        conversation_id=conversation.id,
        message=reply.message,
        provider=reply.provider,
        correction=reply.correction,
        explanation=reply.explanation,
        suggested_exercise=reply.suggested_exercise,
        language_level=reply.language_level,
    )


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
            return conversation, list(conversation.messages), False
        # Ownership is structural elsewhere in the app; here a mismatched
        # id (wrong learner, or doesn't exist) just starts a fresh one
        # rather than erroring -- a lost conversation_id shouldn't block
        # the learner from continuing to chat.

    conversation = Conversation(learner_id=learner_id)
    db.add(conversation)
    await db.flush()
    return conversation, [], True
