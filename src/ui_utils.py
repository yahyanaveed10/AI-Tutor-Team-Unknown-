"""Helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Iterable

import re


def parse_agent_trace(log_lines: Iterable[str]) -> list[dict[str, str]]:
    """Parse run logs into agent activity events."""
    trace: list[dict[str, str]] = []
    current_topic = ""

    for raw_line in log_lines:
        line = raw_line.strip()
        if not line:
            continue

        if "Starting: " in line:
            current_topic = line.split("Starting: ", 1)[1].strip()
            continue

        if "[Turn 0] Tutor:" in line:
            detail = line.split("Tutor:", 1)[1].strip()
            trace.append(
                {"agent": "Opener", "detail": detail, "topic": current_topic}
            )
            continue

        if "[DIAGNOSIS Turn" in line:
            detail = line.split("] ", 1)[-1].strip()
            trace.append(
                {"agent": "Detective", "detail": detail, "topic": current_topic}
            )
            continue

        if "[TUTORING Turn" in line:
            detail = line.split("] ", 1)[-1].strip()
            trace.append({"agent": "Tutor", "detail": detail, "topic": current_topic})
            continue

        if ">>> SHOT CLOCK" in line:
            detail = line.split(">>>", 1)[1].strip()
            trace.append(
                {"agent": "Shot Clock", "detail": detail, "topic": current_topic}
            )
            continue

        if ">>> Level FROZEN" in line:
            detail = line.split(">>>", 1)[1].strip()
            trace.append(
                {"agent": "Confidence Gate", "detail": detail, "topic": current_topic}
            )

    return trace


def condense_trace_timeline(trace: Iterable[dict[str, str]]) -> list[str]:
    """Return a condensed agent timeline with consecutive duplicates removed."""
    timeline: list[str] = []
    for event in trace:
        agent = event.get("agent", "").strip()
        if not agent:
            continue
        if not timeline or timeline[-1] != agent:
            timeline.append(agent)
    return timeline


def extract_diagnosis_metrics(
    trace: Iterable[dict[str, str]],
) -> list[dict[str, float]]:
    """Extract level/confidence sequences from detective trace details."""
    metrics: list[dict[str, float]] = []
    pattern = re.compile(r"Level=(\d+).*Conf=([0-9.]+)")
    for event in trace:
        if event.get("agent") != "Detective":
            continue
        detail = event.get("detail", "")
        match = pattern.search(detail)
        if not match:
            continue
        level = float(match.group(1))
        confidence = float(match.group(2))
        metrics.append(
            {"turn": float(len(metrics) + 1), "level": level, "confidence": confidence}
        )
    return metrics


def find_switch_event(trace: Iterable[dict[str, str]]) -> dict[str, str] | None:
    """Return the most relevant switch event (confidence gate preferred)."""
    trace_list = list(trace)
    for agent_name in ("Confidence Gate", "Shot Clock"):
        matches = [event for event in trace_list if event.get("agent") == agent_name]
        if matches:
            return matches[-1]
    return None
