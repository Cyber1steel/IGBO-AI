from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration. Values come from environment variables /
    a local .env file — never hardcode secrets here."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    app_name: str = "Igbo AI API"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database (Phase 3 wires this up fully — placeholder for now)
    database_url: str = "postgresql+asyncpg://igboai:igboai@localhost:5432/igboai"

    # AI provider selection: "mock" (default/Phase 2) or "natlas" (Phase 5+)
    ai_provider: str = "mock"

    # N-ATLaS connection details — unused until Phase 5, read from env only
    natlas_endpoint_url: str | None = None
    natlas_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
