"""Tests for UI helper utilities."""

from src.ui_utils import (
    condense_trace_timeline,
    extract_diagnosis_metrics,
    find_switch_event,
    parse_agent_trace,
)


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


def test_condense_trace_timeline_dedupes_consecutive_agents():
    trace = [
        {"agent": "Opener", "detail": "Q", "topic": "Algebra"},
        {"agent": "Detective", "detail": "Level=3 Conf=0.4", "topic": "Algebra"},
        {"agent": "Detective", "detail": "Level=3 Conf=0.5", "topic": "Algebra"},
        {"agent": "Shot Clock", "detail": "Forced switch", "topic": "Algebra"},
        {"agent": "Tutor", "detail": "Teaching", "topic": "Algebra"},
    ]

    assert condense_trace_timeline(trace) == [
        "Opener",
        "Detective",
        "Shot Clock",
        "Tutor",
    ]


def test_extract_diagnosis_metrics_parses_level_and_confidence():
    trace = [
        {"agent": "Detective", "detail": "Level=2 Conf=0.35 (LLM=2)", "topic": "X"},
        {"agent": "Tutor", "detail": "Teaching at Level 2", "topic": "X"},
        {"agent": "Detective", "detail": "Level=3 Conf=0.55 (LLM=3)", "topic": "X"},
    ]

    metrics = extract_diagnosis_metrics(trace)

    assert metrics == [
        {"turn": 1.0, "level": 2.0, "confidence": 0.35},
        {"turn": 2.0, "level": 3.0, "confidence": 0.55},
    ]


def test_find_switch_event_prefers_confidence_gate():
    trace = [
        {"agent": "Shot Clock", "detail": "Forced switch", "topic": "X"},
        {"agent": "Confidence Gate", "detail": "Frozen at 0.75", "topic": "X"},
    ]

    event = find_switch_event(trace)

    assert event == {"agent": "Confidence Gate", "detail": "Frozen at 0.75", "topic": "X"}
