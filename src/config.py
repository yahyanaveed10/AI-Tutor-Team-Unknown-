"""Configuration from .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    KNOWUNITY_X_API_KEY: str
    KNOWUNITY_BASE_URL: str = "https://knowunity-agent-olympics-2026-api.vercel.app"
    OPENAI_MODEL: str = "gpt-5.2-pro"
    SET_TYPE: str = "mini_dev"
    TURNS_PER_CONVERSATION: int = 8  # Messages per student-topic session
    MAX_CONVERSATIONS: int = 0  # 0 = unlimited (run all), else limit total sessions
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()

