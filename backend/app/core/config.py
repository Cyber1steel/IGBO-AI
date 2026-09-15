from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration. Values come from environment variables /
    a local .env file — never hardcode secrets here."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    app_name: str = "Igbo AI API"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql+asyncpg://igboai:igboai@localhost:5432/igboai"

    # Auth — JWT access tokens + hashed opaque refresh tokens.
    # JWT_SECRET_KEY has no safe default: fail loudly in production if unset.
    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    # AI provider selection: "mock" (default) | "general" | "natlas"
    ai_provider: str = "mock"

    # N-ATLaS connection details — unused until AI_PROVIDER=natlas
    natlas_endpoint_url: str | None = None
    natlas_api_key: str | None = None

    # Real general-purpose LLM provider (Gemini) — a practical stand-in
    # while N-ATLaS has no reachable hosted API and no GPU is available to
    # self-host it. Free tier, no credit card required — see
    # app/ai/gemini_provider.py and backend/README.md for setup and current
    # free-tier notes.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    @model_validator(mode="after")
    def _refuse_default_secret_in_production(self) -> "Settings":
        if self.environment == "production" and self.jwt_secret_key == "dev-only-insecure-secret-change-me":
            raise ValueError(
                "JWT_SECRET_KEY must be set to a real secret when ENVIRONMENT=production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
