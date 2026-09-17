class AIProviderError(Exception):
    """Raised when a provider fails to produce a reply (unreachable,
    non-2xx response, malformed output, etc). Callers turn this into a
    clean user-facing error — never a raw 500 with a stack trace."""


class AIProviderTimeout(AIProviderError):
    """Raised when a provider doesn't respond within the allowed time.
    A distinct type from AIProviderError so callers can, if useful,
    give a more specific "the tutor is taking too long" message."""


class AIProviderQuotaError(AIProviderError):
    """A provider quota or rate limit blocked the request.

    category and retry_after_seconds are derived from provider metadata, never
    from learner input. They are safe for the API layer to use without exposing
    provider response bodies or credentials.
    """

    def __init__(self, message: str, category: str, retry_after_seconds: float | None = None):
        super().__init__(message)
        self.category = category
        self.retry_after_seconds = retry_after_seconds
