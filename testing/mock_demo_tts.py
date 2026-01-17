"""Mock demo for ElevenLabs TTS integration.

This script does NOT call OpenAI/Knowunity. It only:
- creates mock tutor questions
- maps "predicted level" -> voice id + voice_settings
- synthesizes audio via ElevenLabs
- saves mp3 files under data/audio-demo/

Run:
  python testing/mock_demo_tts.py

Prereqs (in your .env):
  ELEVENLABS_API_KEY=...
  (optional) ELEVENLABS_VOICE_ID_CALM/NEUTRAL/CHALLENGING
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Optional

from src.config import settings
from src.services.tts import ElevenLabsTTS


@dataclass(frozen=True)
class VoiceProfile:
    voice_id: str
    voice_settings: dict


def voice_profile_for_level(level: Optional[int]) -> VoiceProfile:
    """Match the exact mapping used in LLMService (for demo purposes)."""
    # For quick testing, you can force a single voice id for *all* levels:
    #   set DEMO_ELEVENLABS_VOICE_ID=...  (Windows cmd: set DEMO_ELEVENLABS_VOICE_ID=...)
    forced_voice_id = os.getenv("DEMO_ELEVENLABS_VOICE_ID")
    base_voice_id = settings.ELEVENLABS_VOICE_ID

    if level is None:
        return VoiceProfile(
            # Unknown level -> neutral voice (fallback to base if not set)
            voice_id=forced_voice_id or settings.ELEVENLABS_VOICE_ID_NEUTRAL or base_voice_id,
            voice_settings={
                "stability": settings.ELEVENLABS_NEUTRAL_STABILITY,
                "similarity_boost": settings.ELEVENLABS_NEUTRAL_SIMILARITY_BOOST,
                "style": settings.ELEVENLABS_NEUTRAL_STYLE,
                "use_speaker_boost": True,
            },
        )

    if level <= 2:
        return VoiceProfile(
            voice_id=forced_voice_id or settings.ELEVENLABS_VOICE_ID_CALM or base_voice_id,
            voice_settings={
                "stability": settings.ELEVENLABS_CALM_STABILITY,
                "similarity_boost": settings.ELEVENLABS_CALM_SIMILARITY_BOOST,
                "style": settings.ELEVENLABS_CALM_STYLE,
                "use_speaker_boost": True,
            },
        )

    if level >= 4:
        return VoiceProfile(
            voice_id=forced_voice_id or settings.ELEVENLABS_VOICE_ID_CHALLENGING or base_voice_id,
            voice_settings={
                "stability": settings.ELEVENLABS_CHALLENGING_STABILITY,
                "similarity_boost": settings.ELEVENLABS_CHALLENGING_SIMILARITY_BOOST,
                "style": settings.ELEVENLABS_CHALLENGING_STYLE,
                "use_speaker_boost": True,
            },
        )

    return VoiceProfile(
        voice_id=forced_voice_id or settings.ELEVENLABS_VOICE_ID_NEUTRAL or base_voice_id,
        voice_settings={
            "stability": settings.ELEVENLABS_NEUTRAL_STABILITY,
            "similarity_boost": settings.ELEVENLABS_NEUTRAL_SIMILARITY_BOOST,
            "style": settings.ELEVENLABS_NEUTRAL_STYLE,
            "use_speaker_boost": True,
        },
    )


def build_mock_questions(topic: str) -> list[tuple[int, str]]:
    """Return (level, question_text) pairs.

    We intentionally vary the level so you can hear the tone change.
    """
    return [
        (3, f"Welcome! Let’s start with {topic}. In your own words, what is it?"),
        (1, "No worries—take your time. Can you give one simple example?"),
        (2, "Great. What does that example show us?"),
        (3, "Nice. Now explain it in one clear sentence."),
        (4, "Good. Let’s level up: how would you apply it to a new problem?"),
        (5, "Challenge: what’s a tricky edge case where people often make mistakes?"),
        (4, "If you had to teach this to someone, what would you emphasize first?"),
        (3, "Quick check: can you summarize the key steps?"),
        (2, "Good job—what part still feels confusing?"),
        (5, "Final challenge: solve a harder example and explain your reasoning."),
    ]


def load_mock_conversation(path: str = "data/mock_conversation.json") -> tuple[str, list[tuple[int, str]], int]:
    """Load mock conversation from JSON.

    Returns: (topic, [(predicted_level, tutor_text), ...], final_predicted_level)
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    topic = data.get("topic", "(unknown topic)")
    turns = [(t["predicted_level"], t["tutor_text"]) for t in data.get("turns", [])]
    final_level = int(data.get("final_predicted_level", 3))
    return topic, turns, final_level


def build_final_summary(predicted_level: int) -> str:
    if predicted_level <= 2:
        coaching = "You’re building the foundations. We’ll go step by step and practice with simple examples."
    elif predicted_level >= 4:
        coaching = "You’re doing really well. Next, we’ll push you with harder, applied questions to sharpen your skills."
    else:
        coaching = "You understand the basics well, and next we’ll focus on applying the concepts in different situations."
    return f"Based on your answers, you are currently at Level {predicted_level}. {coaching}"


def main() -> None:
    out_dir = Path("data/audio-demo")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load mock conversation from file (fallback to built-in if missing)
    try:
        topic, questions, final_level = load_mock_conversation()
    except Exception:
        topic = "Linear Equations"
        questions = build_mock_questions(topic)
        final_level = 3

    tts = ElevenLabsTTS()

    print(f"Saving demo mp3 files to: {out_dir.resolve()}")
    print("Synthesizing... (this calls ElevenLabs over the network)")

    for i, (level, text) in enumerate(questions, start=1):
        profile = voice_profile_for_level(level)
        audio = tts.synthesize_with_voice(text=text, voice_id=profile.voice_id, voice_settings=profile.voice_settings)
        path = out_dir / f"q{i:02d}_level{level}.mp3"
        path.write_bytes(audio)
        print(f"- wrote {path.name} (level={level}, voice_id={profile.voice_id})")

    # Final spoken feedback summary (after 10 answers)
    summary_text = build_final_summary(final_level)
    summary_profile = voice_profile_for_level(final_level)
    summary_audio = tts.synthesize_with_voice(
        text=summary_text,
        voice_id=summary_profile.voice_id,
        voice_settings=summary_profile.voice_settings,
    )
    summary_path = out_dir / "final_summary.mp3"
    summary_path.write_bytes(summary_audio)
    print(f"- wrote {summary_path.name} (predicted_level={final_level})")

    print("Done.")


if __name__ == "__main__":
    main()
