#!/usr/bin/env python3
"""AI Tutor - Main orchestrator.

Usage:
    python -m src.main                         # Run all students
    python -m src.main --turns 8               # 8 messages per conversation
    python -m src.main --max-convos 5          # Limit to 5 total conversations
    python -m src.main --set-type dev          # Override set type
    python -m src.main --student-id UUID       # Run single student
"""

import argparse
import json
import logging
from pathlib import Path

from src.config import settings
from src.models import StudentState, Message, DiagnosticEvent
from src.services.llm import LLMService
from src.services.knowunity import KnowunityClient
from src.services.database import DatabaseService
from src.services.trace_store import TraceStore

logging.basicConfig(level=settings.LOG_LEVEL, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def run_conversation(
    llm: LLMService,
    api: KnowunityClient,
    db: DatabaseService,
    trace_events: list[dict[str, str]],
    student_id: str,
    student_name: str,
    topic: dict,
    turns: int,
) -> int:
    """Run a single conversation. Returns predicted level."""

    topic_id = topic["id"]
    topic_name = topic["name"]
    log.info(f"[{student_name}] Starting: {topic_name}")

    # Start conversation
    conv = api.start_conversation(student_id, topic_id)
    conv_id = conv["conversation_id"]

    # Initialize state
    state = StudentState(
        student_id=student_id,
        topic_id=topic_id,
        topic_name=topic_name,
    )

    # Turn 0: Generate opener (trap question)
    opener = llm.generate_opener(topic_name)
    log.info(f"[{student_name}] Tutor: {opener[:60]}...")
    trace_events.append({"agent": "Opener", "detail": opener, "topic": topic_name})

    response = api.interact(conv_id, opener)
    student_msg = response["student_response"]
    log.info(f"[{student_name}] Student: {student_msg[:60]}...")

    state.history.append(Message(role="tutor", content=opener))
    state.history.append(Message(role="student", content=student_msg))
    state.turn_count = 1
    db.save_state(state)

    level_frozen = False  # Once confident, lock the level
    SHOT_CLOCK = 6  # Force switch at this turn no matter what

    # Main loop: diagnosis + tutoring
    while state.turn_count < turns and not response.get("is_complete"):

        # Check shot clock FIRST (fail-safe)
        if not level_frozen and state.turn_count >= SHOT_CLOCK:
            level_frozen = True
            state.level_locked = True
            state.switch_reason = "shot_clock"
            log.warning(
                f"[{student_name}] >>> SHOT CLOCK: Forcing switch at Turn {SHOT_CLOCK} "
                f"(Conf={state.confidence:.2f})"
            )
            trace_events.append(
                {
                    "agent": "Shot Clock",
                    "detail": (
                        f"SHOT CLOCK: Forcing switch at Turn {SHOT_CLOCK} "
                        f"(Conf={state.confidence:.2f})"
                    ),
                    "topic": topic_name,
                }
            )

        if not level_frozen and state.confidence < 0.75:
            # DIAGNOSIS PHASE (with verification in ambiguity zone)
            analysis = llm.analyze_with_verification(state, student_msg)

            # ========== EVIDENCE-BASED LEVEL CALCULATION ==========
            # Use LLM as feature extractor, not judge
            old_level = state.estimated_level
            llm_level = analysis.estimated_level

            # Calculate evidence signal
            signal = (
                1.0 * (1 if analysis.is_correct else 0)
                + 0.5 * (1 if analysis.reasoning_score >= 4 else 0)
                - 0.8 * (1 if analysis.misconception else 0)
            )

            # FIRST 2 TURNS: Collect evidence, set baseline from average
            if state.turn_count == 1:
                state.estimated_level = llm_level
                log.info(
                    f"    [{student_name}] → Initial estimate Level {llm_level} "
                    f"(turn 1)"
                )
            elif state.turn_count == 2:
                # Average of first 2 estimates (variance reduction)
                avg_level = round((old_level + llm_level) / 2)
                state.estimated_level = max(1, min(5, avg_level))
                log.info(
                    f"    [{student_name}] → Baseline set to Level "
                    f"{state.estimated_level} (avg of turns 1-2)"
                )
            # SUBSEQUENT TURNS: Apply asymmetric rules
            elif llm_level > old_level:
                # Promotion: require 2 consecutive votes
                state.promo_votes += 1
                if state.promo_votes >= 2:
                    state.estimated_level = min(old_level + 1, 5)
                    state.promo_votes = 0
                    log.info(
                        f"    [{student_name}] → Promoted to Level "
                        f"{state.estimated_level} (2 votes)"
                    )
            elif llm_level < old_level:
                # Demotion: require strong evidence (wrong + low reasoning)
                if not analysis.is_correct and analysis.reasoning_score <= 2:
                    state.estimated_level = max(old_level - 1, 1)
                    state.promo_votes = 0
                    log.info(
                        f"    [{student_name}] → Demoted to Level "
                        f"{state.estimated_level} (strong evidence)"
                    )
            else:
                # Same level: reset promo votes if consistent
                state.promo_votes = 0

            # ========== CONFIDENCE SMOOTHING (timing only) ==========
            raw_conf = analysis.confidence
            smoothed_conf = min(state.confidence + 0.15, raw_conf)  # slower increase
            smoothed_conf = round(min(0.95, smoothed_conf), 2)
            state.confidence = smoothed_conf

            if analysis.misconception:
                state.misconceptions.append(analysis.misconception)

            tutor_msg = analysis.next_message
            log.info(
                f"[{student_name}] [DIAGNOSIS Turn {state.turn_count}] "
                f"Level={state.estimated_level} Conf={smoothed_conf:.2f} "
                f"(LLM={llm_level}, signal={signal:.1f})"
            )
            trace_events.append(
                {
                    "agent": "Detective",
                    "detail": (
                        f"Level={state.estimated_level} Conf={smoothed_conf:.2f} "
                        f"(LLM={llm_level}, signal={signal:.1f})"
                    ),
                    "topic": topic_name,
                }
            )

            # ========== LOG DIAGNOSTIC EVENT ==========
            event = DiagnosticEvent(
                turn=state.turn_count,
                is_correct=analysis.is_correct,
                reasoning_score=analysis.reasoning_score,
                misconception=analysis.misconception,
                llm_level=llm_level,
                computed_level=state.estimated_level,
                confidence=smoothed_conf,
            )
            state.diagnostic_events.append(event)

            # ========== EARLY EXIT: Skip remaining diagnosis if extremely confident ==========
            # Require 3+ events so finalizer has enough data for stable median
            if (
                analysis.confidence >= 0.85
                and analysis.is_correct
                and analysis.reasoning_score >= 4
                and len(state.diagnostic_events) >= 3
            ):
                level_frozen = True
                state.level_locked = True
                state.switch_reason = "early_exit"
                log.info(
                    f"[{student_name}] >>> EARLY EXIT: High confidence "
                    f"({analysis.confidence:.2f}) + correct + good reasoning"
                )
            # Level freezing: once confident, lock it
            elif state.confidence >= 0.75:
                level_frozen = True
                state.level_locked = True
                state.switch_reason = "confidence"
                log.info(
                    f"[{student_name}] >>> Level FROZEN at {state.estimated_level} "
                    f"(confidence={state.confidence:.2f})"
                )
                trace_events.append(
                    {
                        "agent": "Confidence Gate",
                        "detail": (
                            f"Level FROZEN at {state.estimated_level} "
                            f"(confidence={state.confidence:.2f})"
                        ),
                        "topic": topic_name,
                    }
                )
        else:
            # TUTORING PHASE
            tutor_msg = llm.tutor(state, student_msg)
            log.info(
                f"[{student_name}] [TUTORING Turn {state.turn_count}] Teaching "
                f"at Level {state.estimated_level}"
            )
            trace_events.append(
                {
                    "agent": "Tutor",
                    "detail": f"Teaching at Level {state.estimated_level}",
                    "topic": topic_name,
                }
            )

        # Send to student
        response = api.interact(conv_id, tutor_msg)
        student_msg = response["student_response"]
        log.info(f"[{student_name}] [Student Response]: {student_msg[:60]}...")

        state.history.append(Message(role="tutor", content=tutor_msg))
        state.history.append(Message(role="student", content=student_msg))
        state.turn_count += 1
        db.save_state(state)

    # ========== DETERMINISTIC FINALIZER ==========
    # Use median of last K diagnostic events to stabilize the final level
    if state.diagnostic_events:
        k_events = min(3, len(state.diagnostic_events))  # Last 3 events or fewer
        recent_levels = [e.computed_level for e in state.diagnostic_events[-k_events:]]
        recent_levels.sort()
        median_level = recent_levels[len(recent_levels) // 2]

        # Only adjust if significantly different and not in ambiguity zone
        if state.switch_reason == "shot_clock" or state.confidence < 0.75:
            # In ambiguous cases, trust the median more
            state.estimated_level = median_level
            log.info(
                f"    [FINALIZER] Adjusted to median level {median_level} "
                f"(from last {k_events} events)"
            )

    log.info(
        f"[{student_name}] === Session Complete: Level={state.estimated_level}, "
        f"Confidence={state.confidence:.2f} ==="
    )

    # Persist state
    db.save_state(state)

    return state.estimated_level


def run_batch(
    llm: LLMService,
    api: KnowunityClient,
    db: DatabaseService,
    trace_store: TraceStore,
    args: argparse.Namespace,
) -> list[dict]:
    """Run tutor sessions for the selected dataset and persist traces/predictions."""
    # Get students
    students = api.list_students(args.set_type)
    if args.student_id:
        students = [s for s in students if s["id"] == args.student_id]

    log.info(f"Found {len(students)} students")

    # Build task list: (student, topic)
    tasks = []
    for student in students:
        sid = student["id"]
        topics = api.get_topics(sid)
        for topic in topics:
            tasks.append((student, topic))

    # Apply max_convos limit
    if args.max_convos > 0:
        tasks = tasks[: args.max_convos]

    parallel = getattr(args, "parallel", 1)
    log.info(f"Processing {len(tasks)} conversations (parallel={parallel})")

    import threading

    trace_lock = threading.Lock()
    predictions: list[dict] = []

    def process_task(task):
        student, topic = task
        sid = student["id"]
        name = student.get("name", sid)
        trace_events: list[dict[str, str]] = []
        try:
            log.info(f"=== Student: {name} - {topic['name']} ===")
            level = run_conversation(
                llm, api, db, trace_events, sid, name, topic, args.turns
            )
            result = {
                "student_id": sid,
                "topic_id": topic["id"],
                "predicted_level": level,
            }
        except Exception as e:
            log.error(f"Error for {sid}/{topic['id']}: {e}")
            result = {
                "student_id": sid,
                "topic_id": topic["id"],
                "predicted_level": 3,  # Default fallback
            }
        finally:
            if trace_events:
                with trace_lock:
                    trace_store.append_events(sid, trace_events)
        return result

    if parallel > 1:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            predictions = list(executor.map(process_task, tasks))
    else:
        for task in tasks:
            predictions.append(process_task(task))

    # Save predictions
    Path("data").mkdir(exist_ok=True)
    with open("data/predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    log.info(f"Saved {len(predictions)} predictions to data/predictions.json")

    # Optional: submit
    if args.submit:
        result = api.submit_predictions(predictions, args.set_type)
        log.info(f"MSE Score: {result.get('mse_score')}")

    return predictions


def main():
    parser = argparse.ArgumentParser(description="AI Tutor")
    parser.add_argument(
        "--turns",
        type=int,
        default=settings.TURNS_PER_CONVERSATION,
        help="Messages per conversation (default: 8)",
    )
    parser.add_argument(
        "--max-convos",
        type=int,
        default=settings.MAX_CONVERSATIONS,
        help="Limit total conversations (0 = all)",
    )
    parser.add_argument("--set-type", type=str, default=settings.SET_TYPE)
    parser.add_argument("--student-id", type=str, default=None)
    parser.add_argument(
        "--submit", action="store_true", help="Submit predictions after run"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of parallel conversations (default: 1 = sequential)",
    )
    args = parser.parse_args()

    log.info(
        f"Config: set_type={args.set_type}, turns={args.turns}, "
        f"max_convos={args.max_convos or 'all'}, parallel={args.parallel}"
    )

    llm = LLMService()
    api = KnowunityClient()
    db = DatabaseService()
    trace_store = TraceStore()

    return run_batch(llm, api, db, trace_store, args)


if __name__ == "__main__":
    main()
