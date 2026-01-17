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

    ELEVENLABS_API_KEY: str | None = None
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io"
    # Base voice id (used as a fallback).
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    # Optional: use different voices/settings by predicted level band.
    # (You can set these to different ElevenLabs voice IDs to change the "character".)
    ELEVENLABS_VOICE_ID_CALM: str = "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_VOICE_ID_NEUTRAL: str = "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_VOICE_ID_CHALLENGING: str = "21m00Tcm4TlvDq8ikWAM"

    # Voice settings (0.0 - 1.0), used to shape delivery.
    ELEVENLABS_CALM_STABILITY: float = 0.7
    ELEVENLABS_CALM_SIMILARITY_BOOST: float = 0.8
    ELEVENLABS_CALM_STYLE: float = 0.2

    ELEVENLABS_NEUTRAL_STABILITY: float = 0.5
    ELEVENLABS_NEUTRAL_SIMILARITY_BOOST: float = 0.75
    ELEVENLABS_NEUTRAL_STYLE: float = 0.4

    ELEVENLABS_CHALLENGING_STABILITY: float = 0.3
    ELEVENLABS_CHALLENGING_SIMILARITY_BOOST: float = 0.7
    ELEVENLABS_CHALLENGING_STYLE: float = 0.7

    # If true, main.py will write generated mp3s to data/audio/ for debugging.
    SAVE_TTS_AUDIO: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
