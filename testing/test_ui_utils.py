"""Tests for UI helper utilities."""

import json

from src.ui_utils import load_agent_traces, parse_agent_trace, update_agent_traces


def test_parse_agent_trace_extracts_agents_and_topic():
    lines = [
        "INFO: Starting: Linear Functions",
        "INFO: [Turn 0] Tutor: Opening question...",
        "INFO: [DIAGNOSIS Turn 1] Level=3 Conf=0.40 (LLM=3, signal=1.0)",
        "WARNING: >>> SHOT CLOCK: Forcing switch at Turn 6 (Conf=0.30)",
        "INFO: >>> Level FROZEN at 3 (confidence=0.75)",
        "INFO: [TUTORING Turn 6] Teaching at Level 3",
    ]

    trace = parse_agent_trace(lines)

    assert len(trace) == 5
    assert trace[0]["agent"] == "Opener"
    assert trace[0]["detail"] == "Opening question..."
    assert trace[0]["topic"] == "Linear Functions"
    assert trace[1]["agent"] == "Detective"
    assert trace[2]["agent"] == "Shot Clock"
    assert trace[3]["agent"] == "Confidence Gate"
    assert trace[4]["agent"] == "Tutor"


def test_load_agent_traces_missing_returns_empty(tmp_path):
    path = tmp_path / "agent_traces.json"

    assert load_agent_traces(path) == {}


def test_update_agent_traces_writes_and_merges(tmp_path):
    path = tmp_path / "agent_traces.json"
    trace_a = [{"agent": "Opener", "detail": "Hello", "topic": "Algebra"}]
    trace_b = [{"agent": "Tutor", "detail": "Explain", "topic": "Geometry"}]

    update_agent_traces(path, "student-a", trace_a)
    data = json.loads(path.read_text())
    assert data["student-a"] == trace_a

    update_agent_traces(path, "student-b", trace_b)
    data = json.loads(path.read_text())
    assert data["student-a"] == trace_a
    assert data["student-b"] == trace_b
