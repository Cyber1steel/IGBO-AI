from fastapi import APIRouter, Depends

from app.ai.base import AIProvider, TutorMessage
from app.ai.factory import get_ai_provider
from app.schemas.ai import TutorRequest, TutorResponse

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/tutor", response_model=TutorResponse)
async def tutor_reply(
    request: TutorRequest,
    provider: AIProvider = Depends(get_ai_provider),
) -> TutorResponse:
    history = [TutorMessage(role=m.role, content=m.content) for m in request.history]
    reply = await provider.generate_tutor_reply(history, request.message)
    return TutorResponse(message=reply.message, provider=reply.provider)
