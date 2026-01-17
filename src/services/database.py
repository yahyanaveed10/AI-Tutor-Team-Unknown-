"""Simple JSON-based state persistence with per-student-topic files."""

import json
from pathlib import Path
from typing import Optional
from src.models import StudentState


class DatabaseService:
    """Persists student-topic state with set_type directories (parallel-safe)."""
    
    def __init__(self, data_dir: str = "data", set_type: str = "mini_dev"):
        self.base_dir = Path(data_dir)
        self.set_type = set_type
        self.data_dir = self.base_dir / set_type
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._health_check()
    
    def _health_check(self):
        """Verify database directory is working."""
        try:
            test_file = self.data_dir / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
            print(f"✓ Database OK: {self.data_dir}")
        except Exception as e:
            raise RuntimeError(f"Database error: {e}")
    
    def _state_path(self, student_id: str, topic_id: str) -> Path:
        """Get path to student-topic state file."""
        # Use short IDs for cleaner filenames
        sid = student_id[:8] if len(student_id) > 8 else student_id
        tid = topic_id[:8] if len(topic_id) > 8 else topic_id
        return self.data_dir / f"state_{sid}_{tid}.json"
    
    def get_state(self, student_id: str, topic_id: str) -> Optional[StudentState]:
        """Retrieve saved state for a student-topic pair."""
        path = self._state_path(student_id, topic_id)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return StudentState(**data)
            except Exception:
                pass  # Corrupted file, return None
        return None
    
    def save_state(self, state: StudentState):
        """Persist current state to student-topic file."""
        path = self._state_path(state.student_id, state.topic_id)
        path.write_text(json.dumps(state.model_dump(), indent=2))
    
    def get_prediction(self, student_id: str, topic_id: str) -> Optional[int]:
        """Get saved level prediction."""
        state = self.get_state(student_id, topic_id)
        return state.estimated_level if state else None
    
    def list_predictions(self) -> list[dict]:
        """Get all predictions for submission from all state files."""
        predictions = []
        for state_file in self.data_dir.glob("state_*.json"):
            try:
                data = json.loads(state_file.read_text())
                predictions.append({
                    "student_id": data["student_id"],
                    "topic_id": data["topic_id"],
                    "predicted_level": data["estimated_level"]
                })
            except Exception:
                continue  # Skip corrupted files
        return predictions
    
    def clear(self):
        """Clear all saved state files for current set_type."""
        for state_file in self.data_dir.glob("state_*.json"):
            state_file.unlink()
