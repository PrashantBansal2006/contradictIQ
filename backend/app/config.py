"""
config.py — Application settings loaded from environment / .env file.

All env vars are documented in .env.example.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./data/app.db"

    # ── Auth ──────────────────────────────────────────────────────────────────
    jwt_secret: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 h

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: str = "none"  # none | gemini | groq | openai | ollama | anthropic
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""

    # ── Upload ────────────────────────────────────────────────────────────────
    max_upload_mb: int = 20

    # ── Fiscal year ───────────────────────────────────────────────────────────
    fy_end_month: int = 3  # 3 = March (India default)

    # ── Verification ──────────────────────────────────────────────────────────
    min_confidence: float = 0.8

    # ── CORS ──────────────────────────────────────────────────────────────────
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()

