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
from src.models import StudentState, Message
from src.services.llm import LLMService
from src.services.knowunity import KnowunityClient
from src.services.database import DatabaseService

logging.basicConfig(level=settings.LOG_LEVEL, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def run_conversation(
    llm: LLMService,
    api: KnowunityClient,
    db: DatabaseService,
    student_id: str,
    topic: dict,
    turns: int
) -> int:
    """Run a single conversation. Returns predicted level."""
    
    topic_id = topic["id"]
    topic_name = topic["name"]
    log.info(f"Starting: {topic_name}")
    
    # Start conversation
    conv = api.start_conversation(student_id, topic_id)
    conv_id = conv["conversation_id"]
    
    # Initialize state
    state = StudentState(
        student_id=student_id,
        topic_id=topic_id,
        topic_name=topic_name
    )
    
    # Turn 0: Generate opener (trap question)
    opener = llm.generate_opener(topic_name)
    log.info(f"[Turn 0] Tutor: {opener[:80]}...")
    
    response = api.interact(conv_id, opener)
    student_msg = response["student_response"]
    log.info(f"[Turn 0] Student: {student_msg[:80]}...")
    
    state.history.append(Message(role="tutor", content=opener))
    state.history.append(Message(role="student", content=student_msg))
    state.turn_count = 1
    
    tutoring_started = False
    level_frozen = False  # Once confident, lock the level
    switch_reason = None  # Track why we switched
    SHOT_CLOCK = 6  # Force switch at this turn no matter what
    
    # Main loop: diagnosis + tutoring
    while state.turn_count < turns and not response.get("is_complete"):
        
        # Check shot clock FIRST (fail-safe)
        if not level_frozen and state.turn_count >= SHOT_CLOCK:
            level_frozen = True
            tutoring_started = True
            switch_reason = "shot_clock"
            log.warning(f">>> SHOT CLOCK: Forcing switch at Turn {SHOT_CLOCK} (Conf={state.confidence:.2f})")
        
        if not level_frozen and state.confidence < 0.75:
            # DIAGNOSIS PHASE
            analysis = llm.analyze(state, student_msg)
            
            # Deterministic confidence smoothing: max +0.2 per turn
            raw_conf = analysis.confidence
            smoothed_conf = min(state.confidence + 0.2, raw_conf)
            smoothed_conf = round(min(0.95, smoothed_conf), 2)
            
            state.estimated_level = analysis.estimated_level
            state.confidence = smoothed_conf
            if analysis.misconception:
                state.misconceptions.append(analysis.misconception)
            
            tutor_msg = analysis.next_message
            log.info(f"[DIAGNOSIS Turn {state.turn_count}] Level={analysis.estimated_level} Conf={smoothed_conf:.2f} (raw={raw_conf:.2f})")
            
            # Level freezing: once confident, lock it
            if state.confidence >= 0.75:
                level_frozen = True
                tutoring_started = True
                switch_reason = "confidence"
                log.info(f">>> Level FROZEN at {state.estimated_level} (confidence={state.confidence:.2f})")
        else:
            # TUTORING PHASE
            tutoring_started = True
            tutor_msg = llm.tutor(state, student_msg)
            log.info(f"[TUTORING Turn {state.turn_count}] Teaching at Level {state.estimated_level}")
        
        # Send to student
        response = api.interact(conv_id, tutor_msg)
        student_msg = response["student_response"]
        log.info(f"[Student Response]: {student_msg[:60]}...")
        
        state.history.append(Message(role="tutor", content=tutor_msg))
        state.history.append(Message(role="student", content=student_msg))
        state.turn_count += 1
    
    log.info(f"=== Session Complete: Level={state.estimated_level}, Confidence={state.confidence:.2f} ===")
    
    # Persist state
    db.save_state(state)
    
    return state.estimated_level


def main():
    parser = argparse.ArgumentParser(description="AI Tutor")
    parser.add_argument("--turns", type=int, default=settings.TURNS_PER_CONVERSATION,
                        help="Messages per conversation (default: 8)")
    parser.add_argument("--max-convos", type=int, default=settings.MAX_CONVERSATIONS,
                        help="Limit total conversations (0 = all)")
    parser.add_argument("--set-type", type=str, default=settings.SET_TYPE)
    parser.add_argument("--student-id", type=str, default=None)
    parser.add_argument("--submit", action="store_true", help="Submit predictions after run")
    args = parser.parse_args()
    
    log.info(f"Config: set_type={args.set_type}, turns={args.turns}, max_convos={args.max_convos or 'all'}")
    
    llm = LLMService()
    api = KnowunityClient()
    db = DatabaseService()
    
    # Get students
    students = api.list_students(args.set_type)
    if args.student_id:
        students = [s for s in students if s["id"] == args.student_id]
    
    log.info(f"Found {len(students)} students")
    
    predictions = []
    convo_count = 0
    
    for student in students:
        sid = student["id"]
        log.info(f"\n=== Student: {student.get('name', sid)} ===")
        
        topics = api.get_topics(sid)
        
        for topic in topics:
            # Check conversation limit
            if args.max_convos > 0 and convo_count >= args.max_convos:
                log.info(f"Reached max conversations limit ({args.max_convos})")
                break
            
            try:
                level = run_conversation(llm, api, db, sid, topic, args.turns)
                predictions.append({
                    "student_id": sid,
                    "topic_id": topic["id"],
                    "predicted_level": level
                })
                convo_count += 1
            except Exception as e:
                log.error(f"Error: {e}")
                predictions.append({
                    "student_id": sid,
                    "topic_id": topic["id"],
                    "predicted_level": 3  # Default fallback
                })
                convo_count += 1
        
        # Also break outer loop if limit reached
        if args.max_convos > 0 and convo_count >= args.max_convos:
            break
    
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


if __name__ == "__main__":
    main()

