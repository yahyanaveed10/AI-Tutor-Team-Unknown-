"""Helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Iterable


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
