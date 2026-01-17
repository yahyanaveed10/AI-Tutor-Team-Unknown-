"""Tests for CLI trace persistence."""

from __future__ import annotations

import argparse

from src.main import run_batch
from src.models import DetectiveOutput
from src.services.database import DatabaseService
from src.services.trace_store import TraceStore


class FakeLLM:
    """LLM stub for deterministic tests."""

    def generate_opener(self, topic_name: str) -> str:
        return f"Opener for {topic_name}"

    def analyze_with_verification(self, state, student_msg: str) -> DetectiveOutput:
        return DetectiveOutput(
            is_correct=True,
            reasoning_score=3,
            misconception=None,
            estimated_level=3,
            confidence=0.4,
            next_message="Diagnostic follow-up",
        )

    def tutor(self, state, student_msg: str) -> str:
        return "Tutor response"


class FakeAPI:
    """Knowunity stub with a short conversation."""

    def __init__(self) -> None:
        self._calls = 0

    def list_students(self, set_type: str):
        return [{"id": "student-1", "name": "Student One"}]

    def get_topics(self, student_id: str):
        return [{"id": "topic-1", "name": "Linear Functions"}]

    def start_conversation(self, student_id: str, topic_id: str):
        return {"conversation_id": "conv-1"}

    def interact(self, conversation_id: str, tutor_message: str):
        self._calls += 1
        return {
            "student_response": "Student response",
            "is_complete": self._calls >= 2,
        }


def test_cli_run_saves_agent_traces(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(
        turns=3,
        max_convos=0,
        set_type="mini_dev",
        student_id=None,
        submit=False,
        parallel=1,
    )
    llm = FakeLLM()
    api = FakeAPI()
    db = DatabaseService(data_dir=str(tmp_path))
    trace_store = TraceStore(tmp_path / "agent_traces.json")

    run_batch(llm, api, db, trace_store, args)

    stored = trace_store.load()
    assert "student-1" in stored
    agents = [event["agent"] for event in stored["student-1"]]
    assert "Opener" in agents
    assert "Detective" in agents
