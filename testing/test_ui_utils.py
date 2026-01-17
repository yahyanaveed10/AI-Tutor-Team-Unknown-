"""Tests for UI helper utilities."""

from src.ui_utils import parse_agent_trace


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
