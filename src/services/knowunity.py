"""Knowunity API client."""

import httpx
from src.config import settings


class KnowunityClient:
    def __init__(self):
        self.base = settings.KNOWUNITY_BASE_URL
        self.headers = {
            "x-api-key": settings.KNOWUNITY_X_API_KEY,
            "content-type": "application/json"
        }

    def list_students(self, set_type: str = None) -> list[dict]:
        """Get all students for a set type."""
        set_type = set_type or settings.SET_TYPE
        r = httpx.get(f"{self.base}/students", params={"set_type": set_type})
        r.raise_for_status()
        return r.json().get("students", [])

    def get_topics(self, student_id: str) -> list[dict]:
        """Get topics for a student."""
        r = httpx.get(f"{self.base}/students/{student_id}/topics")
        r.raise_for_status()
        return r.json().get("topics", [])

    def start_conversation(self, student_id: str, topic_id: str) -> dict:
        """Start a new conversation."""
        r = httpx.post(
            f"{self.base}/interact/start",
            headers=self.headers,
            json={"student_id": student_id, "topic_id": topic_id}
        )
        r.raise_for_status()
        return r.json()

    def interact(self, conversation_id: str, tutor_message: str) -> dict:
        """Send tutor message, get student response."""
        r = httpx.post(
            f"{self.base}/interact",
            headers=self.headers,
            json={"conversation_id": conversation_id, "tutor_message": tutor_message},
            timeout=60.0
        )
        r.raise_for_status()
        return r.json()

    def submit_predictions(self, predictions: list[dict], set_type: str = None) -> dict:
        """Submit MSE predictions."""
        set_type = set_type or settings.SET_TYPE
        r = httpx.post(
            f"{self.base}/evaluate/mse",
            headers=self.headers,
            json={"predictions": predictions, "set_type": set_type}
        )
        r.raise_for_status()
        return r.json()

    def evaluate_tutoring(self, set_type: str = None) -> dict:
        """Evaluate tutoring quality for all conversations in the set."""
        set_type = set_type or settings.SET_TYPE
        r = httpx.post(
            f"{self.base}/evaluate/tutoring",
            headers=self.headers,
            json={"set_type": set_type}
        )
        r.raise_for_status()
        return r.json()
