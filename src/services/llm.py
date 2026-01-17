"""OpenAI LLM service - Maximized for quality."""

import json
from openai import OpenAI
from src.config import settings
from src.models import DetectiveOutput, StudentState, Message
from src.prompts import OPENER, DETECTIVE, get_tutor_prompt


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.pro_model = "gpt-5.2-pro"

    def _format_history(self, history: list[Message]) -> str:
        if not history:
            return "(no previous messages)"
        return "\n".join(f"{m.role}: {m.content}" for m in history)

    def generate_opener(self, topic: str) -> str:
        """Generate opening trap question."""
        response = self.client.responses.create(
            model=self.pro_model,
            input=OPENER.format(topic=topic),
            reasoning={"effort": "high"}
        )
        return response.output_text

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
        return DetectiveOutput(**data)

    def tutor(self, state: StudentState, student_response: str) -> str:
        """Generate tutoring response with level-adaptive persona."""
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
        return response.output_text

    def verify_correctness(self, topic: str, student_response: str) -> bool:
        """Ultra-fast correctness check using lighter model."""
        # Minimal prompt for speed
        prompt = f"Topic: {topic}\nStudent: {student_response}\n\nIs this factually correct? Reply: true or false"
        
        response = self.client.responses.create(
            model="gpt-5.2",  # Faster non-pro model for simple check
            input=prompt,
            reasoning={"effort": "medium"}
        )
        return response.output_text.strip().lower() == "true"


    def analyze_with_verification(self, state: StudentState, student_response: str) -> DetectiveOutput:
        """Run double-check only in narrow ambiguity zone (0.50 <= conf <= 0.65)."""
        result1 = self.analyze(state, student_response)
        
        # Only double-check in NARROW ambiguity zone (reduces extra calls)
        if 0.50 <= result1.confidence <= 0.65:
            # Verify correctness separately
            verified_correct = self.verify_correctness(state.topic_name, student_response)
            
            # If verifier disagrees with Detective, trust verifier
            if verified_correct != result1.is_correct:
                return DetectiveOutput(
                    is_correct=verified_correct,
                    reasoning_score=result1.reasoning_score,
                    misconception=result1.misconception if not verified_correct else None,
                    estimated_level=result1.estimated_level,
                    confidence=result1.confidence,
                    next_message=result1.next_message
                )
        
        return result1
