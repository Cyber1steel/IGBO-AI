class AIProviderError(Exception):
    """Raised when a provider fails to produce a reply (unreachable,
    non-2xx response, malformed output, etc). Callers turn this into a
    clean user-facing error — never a raw 500 with a stack trace."""


class AIProviderTimeout(AIProviderError):
    """Raised when a provider doesn't respond within the allowed time.
    A distinct type from AIProviderError so callers can, if useful,
    give a more specific "the tutor is taking too long" message."""
