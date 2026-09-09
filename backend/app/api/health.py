from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    settings = get_settings()
    return {"status": "ok", "ai_provider": settings.ai_provider}
