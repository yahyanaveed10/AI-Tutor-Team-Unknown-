"""OpenAI LLM service - Maximized for quality."""

import json
from typing import Optional, Tuple

from openai import OpenAI

from src.config import settings
from src.models import DetectiveOutput, StudentState, Message, TutorSummary
from src.prompts import OPENER, DETECTIVE, get_tutor_prompt
from src.services.tts import ElevenLabsTTS


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.pro_model = "gpt-5.2-pro"
        self.tts: Optional[ElevenLabsTTS] = None

    def _format_history(self, history: list[Message]) -> str:
        if not history:
            return "(no previous messages)"
        return "\n".join(f"{m.role}: {m.content}" for m in history)

    def _get_tts(self) -> Optional[ElevenLabsTTS]:
        if self.tts is not None:
            return self.tts
        try:
            self.tts = ElevenLabsTTS()
        except ValueError:
            self.tts = None
        return self.tts

    def _synthesize(self, text: str) -> Optional[bytes]:
        """Backward-compatible helper (uses default voice)."""
        return self._synthesize_for_level(text=text, level=None)

    def _voice_profile_for_level(self, level: Optional[int]) -> tuple[str, dict]:
        """Map predicted level to a voice id + voice_settings dict."""
        if not settings.USE_ELEVENLABS_VOICE_SETTINGS:
            # Use voice switching only (no style/stability tuning)
            if level is None:
                return (settings.ELEVENLABS_VOICE_ID_NEUTRAL, {})
            if level <= 2:
                return (settings.ELEVENLABS_VOICE_ID_CALM, {})
            if level >= 4:
                return (settings.ELEVENLABS_VOICE_ID_CHALLENGING, {})
            return (settings.ELEVENLABS_VOICE_ID_NEUTRAL, {})

        # Default to neutral when unknown
        if level is None:
            return (
                settings.ELEVENLABS_VOICE_ID_NEUTRAL,
                {
                    "stability": settings.ELEVENLABS_NEUTRAL_STABILITY,
                    "similarity_boost": settings.ELEVENLABS_NEUTRAL_SIMILARITY_BOOST,
                    "style": settings.ELEVENLABS_NEUTRAL_STYLE,
                    "use_speaker_boost": True,
                },
            )

        if level <= 2:
            return (
                settings.ELEVENLABS_VOICE_ID_CALM,
                {
                    "stability": settings.ELEVENLABS_CALM_STABILITY,
                    "similarity_boost": settings.ELEVENLABS_CALM_SIMILARITY_BOOST,
                    "style": settings.ELEVENLABS_CALM_STYLE,
                    "use_speaker_boost": True,
                },
            )

        if level >= 4:
            return (
                settings.ELEVENLABS_VOICE_ID_CHALLENGING,
                {
                    "stability": settings.ELEVENLABS_CHALLENGING_STABILITY,
                    "similarity_boost": settings.ELEVENLABS_CHALLENGING_SIMILARITY_BOOST,
                    "style": settings.ELEVENLABS_CHALLENGING_STYLE,
                    "use_speaker_boost": True,
                },
            )

        return (
            settings.ELEVENLABS_VOICE_ID_NEUTRAL,
            {
                "stability": settings.ELEVENLABS_NEUTRAL_STABILITY,
                "similarity_boost": settings.ELEVENLABS_NEUTRAL_SIMILARITY_BOOST,
                "style": settings.ELEVENLABS_NEUTRAL_STYLE,
                "use_speaker_boost": True,
            },
        )

    def _synthesize_for_level(self, text: str, level: Optional[int]) -> Optional[bytes]:
        tts = self._get_tts()
        if not tts or not text:
            return None
        voice_id, voice_settings = self._voice_profile_for_level(level)
        try:
            return tts.synthesize_with_voice(
                text=text,
                voice_id=voice_id,
                voice_settings=voice_settings,
            )
        except Exception:
            return None

    def generate_opener(self, topic: str) -> Tuple[str, Optional[bytes]]:
        """Generate opening trap question (text + optional audio)."""
        response = self.client.responses.create(
            model=self.pro_model,
            input=OPENER.format(topic=topic),
            reasoning={"effort": "high"}
        )
        text = response.output_text
        # Opener has no predicted level yet -> neutral voice profile
        return text, self._synthesize_for_level(text=text, level=None)

    def analyze(self, state: StudentState, student_response: str) -> DetectiveOutput:
        """Analyze student response, return structured data."""
        prompt = DETECTIVE.format(
            topic=state.topic_name,
            history=self._format_history(state.history),
            response=student_response
        )
        json_prompt = prompt + """

Return ONLY valid JSON:
{
  "is_correct": bool,
  "reasoning_score": 1-5,
  "misconception": string or null,
  "estimated_level": 1-5,
  "confidence": 0.0-1.0,
  "next_message": "The ACTUAL message to send to the student. NOT an instruction. Write exactly what the student should read."
}

CRITICAL: "next_message" must be the literal text the student will see. Do NOT write instructions like "Ask the student to..." - write the actual question or teaching content directly."""
        
        response = self.client.responses.create(
            model=self.pro_model,
            input=json_prompt,
            reasoning={"effort": "high"}
        )
        
        # Robust JSON parsing with fallback
        raw_text = response.output_text
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            # Sanitize common escape issues and retry
            import re
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
            if json_match:
                raw_text = json_match.group(1)
            # Fix common escape issues
            raw_text = raw_text.replace('\\"', '"').replace("\\'", "'")
            raw_text = re.sub(r'\\(?!["\\/bfnrt])', r'\\\\', raw_text)  # Fix invalid escapes
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                # Ultimate fallback: return safe defaults
                data = {
                    "is_correct": False,
                    "reasoning_score": 3,
                    "misconception": None,
                    "estimated_level": 3,
                    "confidence": 0.5,
                    "next_message": "Let's continue. Can you tell me more about your thinking?"
                }
        audio = self._synthesize_for_level(text=data.get("next_message", ""), level=state.estimated_level)
        return DetectiveOutput(**data, next_message_audio=audio)

    def tutor(self, state: StudentState, student_response: str) -> Tuple[str, Optional[bytes]]:
        """Generate tutoring response with level-adaptive persona (text + optional audio)."""
        tutor_prompt = get_tutor_prompt(state.estimated_level)
        prompt = tutor_prompt.format(
            level=state.estimated_level,
            topic=state.topic_name,
            misconceptions=", ".join(state.misconceptions) or "none identified",
            history=self._format_history(state.history),
            response=student_response
        )
        response = self.client.responses.create(
            model=self.pro_model,
            input=prompt,
            reasoning={"effort": "medium"}
        )
        text = response.output_text
        return text, self._synthesize_for_level(text=text, level=state.estimated_level)

    def generate_summary(self, state: StudentState) -> TutorSummary:
        """Generate a short spoken summary at the end of a session.

        This is rule-based for now (no extra LLM call), so it is predictable and cheap.
        """
        level = state.estimated_level

        if level <= 2:
            coaching = "You’re building the foundations. We’ll go step by step and practice with simple examples."
        elif level >= 4:
            coaching = "You’re doing really well. Next, we’ll push you with harder, applied questions to sharpen your skills."
        else:
            coaching = "You understand the basics well, and next we’ll focus on applying the concepts in different situations."

        text = (
            f"Based on your answers, you are currently at Level {level}. "
            f"{coaching}"
        )
        audio = self._synthesize_for_level(text=text, level=level)
        return TutorSummary(predicted_level=level, text=text, audio=audio)
