from pathlib import Path

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    settings = get_settings()
    return {"status": "ok", "ai_provider": settings.ai_provider}


# TEMPORARY -- for diagnosing why AI_PROVIDER=general in .env isn't taking
# effect.
@router.get("/debug/env")
async def debug_env():
    settings = get_settings()
    expected_env_path = Path(".env").expanduser()
    return {
        "ai_provider": settings.ai_provider,
        "gemini_api_key_present": bool(settings.gemini_api_key),
        "current_working_directory": str(Path.cwd()),
        "expected_env_file_path": str(expected_env_path.resolve()),
        "env_file_found_at_that_path": expected_env_path.exists(),
    }