"""Streamlit UI for AI Tutor dev runs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import httpx
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ui_utils import load_agent_traces, parse_agent_trace, update_agent_traces

DATA_PATH = ROOT_DIR / "data" / "state.json"
AGENT_TRACE_PATH = ROOT_DIR / "data" / "agent_traces.json"
DEFAULT_BASE_URL = "https://knowunity-agent-olympics-2026-api.vercel.app"
DEFAULT_DEV_STUDENTS = [
    {
        "id": "1c6afe74-c388-4eb1-b82e-8326d95e29a3",
        "name": "Alex Test",
        "grade_level": 8,
    },
    {
        "id": "2ee4a025-4845-47f4-a634-3c9e423a4b0e",
        "name": "Sam Struggle",
        "grade_level": 9,
    },
    {
        "id": "2b9da93c-5616-49ca-999c-a894b9d004a3",
        "name": "Maya Advanced",
        "grade_level": 11,
    },
]
DEFAULT_DEV_STUDENT_ALLOWLIST = {student["id"] for student in DEFAULT_DEV_STUDENTS}


def init_state() -> None:
    """Initialize Streamlit session state keys."""
    st.session_state.setdefault("run_logs", {})
    st.session_state.setdefault("agent_traces", {})
    st.session_state.setdefault("last_status", {})
    st.session_state.setdefault("run_events", {})
    st.session_state.setdefault("run_state", {})


def hydrate_agent_traces() -> None:
    """Load persisted agent traces into session state."""
    persisted = load_agent_traces(AGENT_TRACE_PATH)
    if not persisted:
        return
    current = st.session_state.get("agent_traces", {})
    for student_id, trace in persisted.items():
        current.setdefault(student_id, trace)
    st.session_state["agent_traces"] = current


def extract_run_event(line: str) -> str | None:
    """Filter and normalize run log lines for UI display."""
    if "HTTP Request:" in line or "httpx" in line.lower():
        return None
    cleaned = line.replace("INFO:", "", 1).replace("WARNING:", "", 1).strip()
    keep_tokens = (
        "Config:",
        "Found ",
        "Starting:",
        "[Turn 0]",
        "[DIAGNOSIS Turn",
        "[TUTORING Turn",
        ">>>",
        "=== Session Complete",
        "Saved ",
        "Reached max conversations limit",
    )
    if any(token in cleaned for token in keep_tokens):
        return cleaned
    return None


def should_refresh_chat(line: str) -> bool:
    """Return True when log lines suggest new chat content."""
    chat_tokens = (
        "[Turn 0] Tutor:",
        "[Turn 0] Student:",
        "[DIAGNOSIS Turn",
        "[TUTORING Turn",
        "[Student Response]:",
        "Saved ",
    )
    return any(token in line for token in chat_tokens)


def load_student_allowlist() -> set[str]:
    """Load allowlisted dev student IDs from env."""
    raw_ids = os.getenv("DEV_STUDENT_IDS", "").strip()
    if raw_ids:
        return {entry.strip() for entry in raw_ids.split(",") if entry.strip()}
    return set(DEFAULT_DEV_STUDENT_ALLOWLIST)


def load_dev_set_type() -> str:
    """Load the dataset type for dev UI runs."""
    raw_type = os.getenv("DEV_SET_TYPE", "").strip()
    return raw_type or "mini_dev"


def load_dev_students_override() -> list[dict[str, Any]] | None:
    """Load a dev student list override from env."""
    raw_json = os.getenv("DEV_STUDENTS_JSON", "").strip()
    if not raw_json:
        return None
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid DEV_STUDENTS_JSON: {exc}") from exc
    if isinstance(payload, dict):
        return payload.get("students", [])
    if isinstance(payload, list):
        return payload
    raise ValueError("DEV_STUDENTS_JSON must be a list or an object with 'students'.")


def get_base_url() -> str:
    """Return the Knowunity API base URL."""
    return os.getenv("KNOWUNITY_BASE_URL", DEFAULT_BASE_URL)


def fetch_dev_students() -> list[dict[str, Any]]:
    """Fetch students from the dev set."""
    override = load_dev_students_override()
    if override is not None:
        return override
    set_type = load_dev_set_type()
    response = httpx.get(
        f"{get_base_url()}/students", params={"set_type": set_type}, timeout=30
    )
    response.raise_for_status()
    students = response.json().get("students", [])
    allowlist = load_student_allowlist()
    if allowlist:
        students = [student for student in students if student.get("id") in allowlist]
    if not students and allowlist == DEFAULT_DEV_STUDENT_ALLOWLIST:
        return list(DEFAULT_DEV_STUDENTS)
    return students


def load_state() -> dict[str, Any]:
    """Load the persisted conversation state from disk."""
    if not DATA_PATH.exists():
        return {}
    return json.loads(DATA_PATH.read_text())


def get_student_entries(
    state_data: dict[str, Any], student_id: str
) -> list[dict[str, Any]]:
    """Collect state entries for a single student."""
    entries: list[dict[str, Any]] = []
    for entry in state_data.values():
        if entry.get("student_id") == student_id:
            entries.append(entry)
    return sorted(entries, key=lambda item: item.get("topic_name", ""))


def run_ai_for_student(
    student_id: str,
    status_container: st.delta_generator.DeltaGenerator | None = None,
    event_callback: Callable[[str], None] | None = None,
    chat_refresh: Callable[[], None] | None = None,
) -> list[str]:
    """Run the dockerized tutor for a single student and capture logs."""
    run_mode = os.getenv("TUTOR_RUN_MODE", "").strip().lower()
    if not run_mode:
        run_mode = "local" if Path("/.dockerenv").exists() else "docker"
    set_type = load_dev_set_type()

    if run_mode == "local":
        cmd = [
            "python",
            "-m",
            "src.main",
            "--student-id",
            student_id,
            "--turns",
            "10",
            "--set-type",
            set_type,
        ]
    else:
        cmd = [
            "make",
            "docker-run",
            f"ARGS=--student-id {student_id} --turns 10 --set-type {set_type}",
        ]
    env = os.environ.copy()
    env["SET_TYPE"] = set_type
    log_lines: list[str] = []

    process = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    if process.stdout:
        for line in process.stdout:
            clean = line.rstrip()
            log_lines.append(clean)
            event = extract_run_event(clean)
            if event:
                if event_callback:
                    event_callback(event)
                if status_container:
                    status_container.info(f"⏳ Running tutor... {event}")
            if chat_refresh and should_refresh_chat(clean):
                chat_refresh()

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Run failed with exit code {process.returncode}")

    return log_lines


st.set_page_config(page_title="AI Tutor Dev Console", layout="wide")
init_state()
hydrate_agent_traces()

st.title("AI Tutor Dev Console")
st.caption("Dev-only student selection with dockerized tutor runs.")

with st.sidebar:
    dev_set_type = load_dev_set_type()
    st.subheader(f"Students ({dev_set_type} set)")
    selected_student_id = None
    students: list[dict[str, Any]] = []
    try:
        students = fetch_dev_students()
    except httpx.HTTPError as exc:
        st.error(f"Student list error: {exc}")
    except ValueError as exc:
        st.error(str(exc))

    if students:
        student_options = [student["id"] for student in students]
        student_labels = {
            student["id"]: (
                f"{student.get('name', student['id'])} "
                f"(Grade {student.get('grade_level', '?')})"
            )
            for student in students
        }
        selected_student_id = st.selectbox(
            "Student",
            student_options,
            format_func=lambda student_id: student_labels.get(student_id, student_id),
        )
    else:
        st.warning("No dev students available.")

    st.subheader("Tutor run")
    if selected_student_id:
        st.code(
            f'make docker-run ARGS="--student-id {selected_student_id} --turns 10 --set-type {dev_set_type}"',
            language="bash",
        )
    run_clicked = st.button("Run AI", disabled=not selected_student_id)


left, right = st.columns([2, 1], gap="large")

with left:
    run_status_slot = st.empty()
    chat_container = st.empty()
    if selected_student_id:
        run_state = st.session_state.get("run_state", {}).get(selected_student_id)
        if run_state == "running":
            run_status_slot.info("⏳ Tutor run in progress...")
        elif run_state == "completed":
            run_status_slot.success("✅ Tutor run completed.")
        elif run_state and run_state.startswith("error"):
            run_status_slot.error(run_state)

def render_chat_view() -> list[dict[str, Any]]:
    state_data = load_state()
    entries: list[dict[str, Any]] = []
    if selected_student_id:
        entries = get_student_entries(state_data, selected_student_id)
    with chat_container.container():
        st.subheader("Chat history")
        if not selected_student_id:
            st.info("Select a dev student to view their chat history.")
        elif not entries:
            st.info("No chat history yet. Run the tutor to generate one.")
        else:
            topic_labels = [entry.get("topic_name", "Topic") for entry in entries]
            tabs = st.tabs(topic_labels)
            for tab, entry in zip(tabs, entries):
                with tab:
                    run_events = st.session_state.get("run_events", {}).get(
                        selected_student_id, []
                    )
                    filtered_events = [
                        event
                        for event in run_events
                        if entry.get("topic_name") and entry.get("topic_name") in event
                    ]
                    display_events = filtered_events or run_events
                    if display_events:
                        with st.chat_message("assistant"):
                            st.markdown(
                                "**Run events**\n"
                                + "\n".join(f"- {event}" for event in display_events[-8:])
                            )
                    history = entry.get("history", [])
                    for message in history:
                        role = message.get("role", "assistant")
                        display_role = "assistant"
                        if role == "student":
                            display_role = "user"
                        elif role == "tutor":
                            display_role = "assistant"
                        with st.chat_message(display_role):
                            st.markdown(message.get("content", ""))
    return entries


if run_clicked and selected_student_id:
    st.session_state["run_state"][selected_student_id] = "running"
    st.session_state["run_events"][selected_student_id] = []
    run_status_slot.info("⏳ Tutor run in progress...")

    def refresh_chat() -> None:
        render_chat_view()

    try:
        with st.spinner("Running tutor in Docker..."):
            log_lines = run_ai_for_student(
                selected_student_id,
                run_status_slot,
                st.session_state["run_events"][selected_student_id].append,
                refresh_chat,
            )
        st.session_state["run_logs"][selected_student_id] = log_lines
        trace = parse_agent_trace(log_lines)
        st.session_state["agent_traces"][selected_student_id] = trace
        update_agent_traces(AGENT_TRACE_PATH, selected_student_id, trace)
        st.session_state["last_status"][selected_student_id] = "completed"
        st.session_state["run_state"][selected_student_id] = "completed"
        run_status_slot.success("✅ Tutor run completed.")
        render_chat_view()
        st.rerun()
    except Exception as exc:
        st.session_state["last_status"][selected_student_id] = f"error: {exc}"
        st.session_state["run_state"][selected_student_id] = f"error: {exc}"
        run_status_slot.error(f"Run failed: {exc}")

student_entries = render_chat_view()

with right:
    st.subheader("Agent activity")
    trace = (
        st.session_state.get("agent_traces", {}).get(selected_student_id, [])
        if selected_student_id
        else []
    )
    topic_filter = "All"
    topic_choices = ["All"]
    if student_entries:
        topic_choices += [entry.get("topic_name", "Topic") for entry in student_entries]
    if len(topic_choices) > 1:
        topic_filter = st.selectbox("Topic filter", topic_choices)

    if trace:
        if topic_filter != "All":
            trace = [event for event in trace if event.get("topic") == topic_filter]
        last_by_agent: dict[str, dict[str, str]] = {}
        for event in trace:
            last_by_agent[event["agent"]] = event
        for agent_name in [
            "Opener",
            "Detective",
            "Tutor",
            "Shot Clock",
            "Confidence Gate",
        ]:
            if agent_name in last_by_agent:
                event = last_by_agent[agent_name]
                st.markdown(f"**{agent_name}**")
                st.caption(event.get("detail", ""))
        with st.expander("Full agent trace"):
            st.dataframe(trace, use_container_width=True)
    else:
        st.info("Run the tutor to see agent activity.")
