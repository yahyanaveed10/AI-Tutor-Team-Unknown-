"""Simple JSON-based state persistence."""

import json
from pathlib import Path
from typing import Optional
from src.models import StudentState


class DatabaseService:
    """Persists student state to JSON file."""
    
    def __init__(self, path: str = "data/state.json"):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)
        self._data = self._load()
        self._health_check()
    
    def _health_check(self):
        """Verify database is working."""
        try:
            self._save()
            print(f"✓ Database OK: {self.path}")
        except Exception as e:
            raise RuntimeError(f"Database error: {e}")
    
    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {}
    
    def _save(self):
        self.path.write_text(json.dumps(self._data, indent=2))
    
    def _key(self, student_id: str, topic_id: str) -> str:
        return f"{student_id}:{topic_id}"
    
    def get_state(self, student_id: str, topic_id: str) -> Optional[StudentState]:
        """Retrieve saved state for a student-topic pair."""
        key = self._key(student_id, topic_id)
        if key in self._data:
            return StudentState(**self._data[key])
        return None
    
    def save_state(self, state: StudentState):
        """Persist current state."""
        key = self._key(state.student_id, state.topic_id)
        self._data[key] = state.model_dump()
        self._save()
    
    def get_prediction(self, student_id: str, topic_id: str) -> Optional[int]:
        """Get saved level prediction."""
        state = self.get_state(student_id, topic_id)
        return state.estimated_level if state else None
    
    def list_predictions(self) -> list[dict]:
        """Get all predictions for submission."""
        predictions = []
        for key, data in self._data.items():
            student_id, topic_id = key.split(":")
            predictions.append({
                "student_id": student_id,
                "topic_id": topic_id,
                "predicted_level": data["estimated_level"]
            })
        return predictions
    
    def clear(self):
        """Clear all saved state."""
        self._data = {}
        self._save()
