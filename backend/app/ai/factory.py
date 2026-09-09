from functools import lru_cache

from app.ai.base import AIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.natlas_provider import NATLaSProvider
from app.core.config import Settings, get_settings


@lru_cache
def get_ai_provider() -> AIProvider:
    """Single place that decides which AIProvider implementation is active.
    Swapping the default from mock to N-ATLaS in Phase 5 is a one-line change
    here (and setting AI_PROVIDER=natlas) — nothing else in the app needs to
    know which provider is behind the interface."""
    settings: Settings = get_settings()

    if settings.ai_provider == "natlas":
        return NATLaSProvider(settings)
    return MockAIProvider()
