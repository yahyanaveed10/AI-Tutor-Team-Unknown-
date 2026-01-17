"""Tests for trace persistence."""

import json

from src.services.trace_store import TraceStore


def test_trace_store_load_missing_returns_empty(tmp_path):
    store = TraceStore(tmp_path / "agent_traces.json")

    assert store.load() == {}


def test_trace_store_update_student_writes_and_merges(tmp_path):
    store = TraceStore(tmp_path / "agent_traces.json")
    trace_a = [{"agent": "Opener", "detail": "Hello", "topic": "Algebra"}]
    trace_b = [{"agent": "Tutor", "detail": "Explain", "topic": "Geometry"}]

    store.update_student("student-a", trace_a)
    data = json.loads(store.path.read_text())
    assert data["student-a"] == trace_a

    store.update_student("student-b", trace_b)
    data = json.loads(store.path.read_text())
    assert data["student-a"] == trace_a
    assert data["student-b"] == trace_b
