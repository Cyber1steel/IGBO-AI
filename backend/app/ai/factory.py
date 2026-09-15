from functools import lru_cache

from app.ai.base import AIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.natlas_provider import NATLaSProvider
from app.core.config import Settings, get_settings


@lru_cache
def get_ai_provider() -> AIProvider:
    """Single place that decides which AIProvider implementation is active,
    via AI_PROVIDER=mock|general|natlas. Nothing else in the app (the tutor
    orchestrator, the API route, the frontend) knows or cares which one is
    behind the interface -- that's the whole point of the abstraction."""
    settings: Settings = get_settings()

    if settings.ai_provider == "general":
        return GeminiProvider(settings)
    if settings.ai_provider == "natlas":
        return NATLaSProvider(settings)
    return MockAIProvider()
