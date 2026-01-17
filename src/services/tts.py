"""Text-to-speech services.

This module currently provides a small ElevenLabs wrapper that can:
- select a specific voice_id per request
- apply voice_settings (stability/similarity_boost/style/speaker_boost)
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from src.config import settings


class ElevenLabsTTS:
    """Simple ElevenLabs TTS client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128",
    ) -> None:
        # .env values sometimes contain accidental leading spaces; strip to be safe.
        self.api_key = (api_key or settings.ELEVENLABS_API_KEY or "").strip() or None
        self.base_url = (base_url or settings.ELEVENLABS_BASE_URL).strip()
        self.voice_id = (voice_id or settings.ELEVENLABS_VOICE_ID).strip()
        self.model_id = model_id
        self.output_format = output_format

        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is not set")
        if not self.voice_id:
            raise ValueError("ELEVENLABS_VOICE_ID is not set")

    def synthesize(self, text: str) -> bytes:
        """Return raw audio bytes for the given text using the default voice."""
        return self.synthesize_with_voice(text=text, voice_id=self.voice_id)

    def synthesize_with_voice(
        self,
        text: str,
        voice_id: str,
        voice_settings: Optional[dict[str, Any]] = None,
    ) -> bytes:
        """Return raw audio bytes for the given text.

        Args:
            text: Text to speak.
            voice_id: ElevenLabs voice id to use.
            voice_settings: Optional dict sent as `voice_settings`.
                Typical keys: stability, similarity_boost, style, use_speaker_boost.
        """
        url = f"{self.base_url}/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.model_id,
            "output_format": self.output_format,
        }

        if voice_settings:
            payload["voice_settings"] = voice_settings

        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                # ElevenLabs often returns useful JSON error details on failure.
                detail = None
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                raise httpx.HTTPStatusError(
                    f"{e} | ElevenLabs detail: {detail}",
                    request=e.request,
                    response=e.response,
                )
            return response.content
