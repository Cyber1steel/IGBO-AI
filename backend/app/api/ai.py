from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.errors import AIProviderQuotaError
from app.ai.factory import get_ai_provider
from app.core.db import get_db
from app.core.deps import get_current_learner_profile
from app.models import LearnerProfile
from app.schemas.ai import ConversationHistoryOut, ConversationMessageOut, TutorRequest, TutorResponse
from app.services.tutor_orchestrator import TutorTurnFailed, TutorTurnTimeout, get_latest_conversation, handle_tutor_turn

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/tutor", response_model=TutorResponse)
async def tutor_reply(
    request: TutorRequest,
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
    provider: AIProvider = Depends(get_ai_provider),
) -> TutorResponse:
    try:
        conversation, reply = await handle_tutor_turn(
            db, profile, provider, request.message, request.conversation_id, request.lesson_id
        )
    except TutorTurnTimeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The tutor is taking too long to respond. Please try again.",
        )
    except TutorTurnFailed as exc:
        if isinstance(exc.provider_error, AIProviderQuotaError):
            if exc.provider_error.category in {
                "daily_quota_exhausted",
                "free_tier_model_quota",
                "billing_or_quota_configuration",
            }:
                detail = "The AI provider quota is exhausted or unavailable for this model. Check Google AI Studio quota and billing settings."
            else:
                detail = "The AI provider is temporarily rate limited. Please try again later."
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI tutor is unavailable right now. Please try again shortly.",
        )

    return TutorResponse(
        conversation_id=conversation.id,
        message=reply.message,
        provider=reply.provider,
        correction=reply.correction,
        explanation=reply.explanation,
        hint=reply.hint,
        example=reply.example,
        follow_up_question=reply.follow_up_question,
        learning_action=reply.learning_action,
        suggested_exercise=reply.suggested_exercise,
        language_level=reply.language_level,
    )


@router.get("/conversation", response_model=ConversationHistoryOut | None)
async def latest_conversation(
    db: AsyncSession = Depends(get_db),
    profile: LearnerProfile = Depends(get_current_learner_profile),
):
    """The learner's most recently active conversation, with full message
    history, so leaving and returning to Conversation resumes where they
    left off (Phase 6 section 11). Returns null if they've never chatted."""
    result = await get_latest_conversation(db, profile.id)
    if result is None:
        return None
    conversation, messages = result
    return ConversationHistoryOut(
        conversation_id=conversation.id,
        messages=[
            ConversationMessageOut(role=m.role, content=m.content, created_at=m.created_at) for m in messages
        ],
    )
