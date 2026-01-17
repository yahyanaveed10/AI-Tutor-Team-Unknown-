"""Helpers for the Streamlit UI."""

from __future__ import annotations

import json
from pathlib import Path
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


def load_agent_traces(path: str | Path) -> dict[str, list[dict[str, str]]]:
    """Load persisted agent traces from disk."""
    trace_path = Path(path)
    if not trace_path.exists():
        return {}
    try:
        data = json.loads(trace_path.read_text())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_agent_traces(path: str | Path, traces: dict[str, list[dict[str, str]]]) -> None:
    """Persist agent traces to disk."""
    trace_path = Path(path)
    trace_path.parent.mkdir(exist_ok=True)
    trace_path.write_text(json.dumps(traces, indent=2))


def update_agent_traces(
    path: str | Path,
    student_id: str,
    trace: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    """Update persisted agent traces for a student and return merged data."""
    traces = load_agent_traces(path)
    traces[student_id] = trace
    save_agent_traces(path, traces)
    return traces
