"""Persistence for agent trace events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TraceStore:
    """Store agent trace events in a JSON file."""

    def __init__(self, path: str | Path = "data/agent_traces.json"):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)

    def load(self) -> dict[str, list[dict[str, str]]]:
        """Load stored traces from disk."""
        if not self.path.exists():
            return {}
        try:
            data: Any = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, traces: dict[str, list[dict[str, str]]]) -> None:
        """Write traces to disk."""
        self.path.write_text(json.dumps(traces, indent=2))

    def update_student(
        self, student_id: str, trace: list[dict[str, str]]
    ) -> dict[str, list[dict[str, str]]]:
        """Update a student's trace and return merged data."""
        traces = self.load()
        traces[student_id] = trace
        self.save(traces)
        return traces

    def append_events(
        self, student_id: str, events: list[dict[str, str]]
    ) -> dict[str, list[dict[str, str]]]:
        """Append events to a student's trace and return merged data."""
        traces = self.load()
        traces.setdefault(student_id, [])
        traces[student_id].extend(events)
        self.save(traces)
        return traces
