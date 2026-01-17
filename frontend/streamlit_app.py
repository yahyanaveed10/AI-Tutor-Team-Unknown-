"""Streamlit UI for AI Tutor dev runs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ui_utils import parse_agent_trace

DATA_PATH = ROOT_DIR / "data" / "state.json"
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
    student_id: str, log_container: st.delta_generator.DeltaGenerator | None = None
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
            if log_container:
                log_container.code("\n".join(log_lines[-200:]))

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Run failed with exit code {process.returncode}")

    return log_lines


st.set_page_config(page_title="AI Tutor Dev Console", layout="wide")
init_state()

st.title("AI Tutor Dev Console")
st.caption("Dev-only student selection with dockerized tutor runs.")

run_log_slot = st.empty()

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

if run_clicked and selected_student_id:
    try:
        with st.spinner("Running tutor in Docker..."):
            log_lines = run_ai_for_student(selected_student_id, run_log_slot)
        st.session_state["run_logs"][selected_student_id] = log_lines
        st.session_state["agent_traces"][selected_student_id] = parse_agent_trace(
            log_lines
        )
        st.session_state["last_status"][selected_student_id] = "completed"
        st.rerun()
    except Exception as exc:
        st.session_state["last_status"][selected_student_id] = f"error: {exc}"
        run_log_slot.error(f"Run failed: {exc}")

state_data = load_state()
student_entries: list[dict[str, Any]] = []
if selected_student_id:
    student_entries = get_student_entries(state_data, selected_student_id)

left, right = st.columns([2, 1], gap="large")

with left:
    st.subheader("Chat history")
    if not selected_student_id:
        st.info("Select a dev student to view their chat history.")
    elif not student_entries:
        st.info("No chat history yet. Run the tutor to generate one.")
    else:
        topic_labels = [entry.get("topic_name", "Topic") for entry in student_entries]
        tabs = st.tabs(topic_labels)
        for tab, entry in zip(tabs, student_entries):
            with tab:
                history = entry.get("history", [])
                for message in history:
                    with st.chat_message(message.get("role", "assistant")):
                        st.markdown(message.get("content", ""))

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

    st.subheader("Run log")
    log_lines = (
        st.session_state.get("run_logs", {}).get(selected_student_id, [])
        if selected_student_id
        else []
    )
    if log_lines:
        st.code("\n".join(log_lines[-200:]), language="text")
    else:
        st.caption("No logs captured yet.")
