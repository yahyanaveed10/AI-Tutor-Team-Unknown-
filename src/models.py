"""Pydantic models for type safety."""

from pydantic import BaseModel, Field
from typing import List, Optional


class DetectiveOutput(BaseModel):
    """LLM output during diagnosis."""
    is_correct: bool
    reasoning_score: int = Field(ge=1, le=5)
    misconception: Optional[str] = None
    estimated_level: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0.0, le=1.0)
    next_message: str


class DiagnosticEvent(BaseModel):
    """Per-turn diagnostic evidence for finalizer."""
    turn: int
    is_correct: bool
    reasoning_score: int = Field(ge=1, le=5)
    misconception: Optional[str] = None
    llm_level: int = Field(ge=1, le=5)  # What LLM suggested
    computed_level: int = Field(ge=1, le=5)  # What we actually set
    confidence: float = Field(ge=0.0, le=1.0)


class Message(BaseModel):
    role: str
    content: str


class StudentState(BaseModel):
    """Session state for a student-topic pair."""
    student_id: str
    topic_id: str
    topic_name: str = ""
    turn_count: int = 0
    estimated_level: int = 3
    confidence: float = 0.0
    history: List[Message] = []
    misconceptions: List[str] = []
    promo_votes: int = 0  # Asymmetric: require 2 votes to promote
    diagnostic_events: List[DiagnosticEvent] = []  # Per-turn evidence log
    level_locked: bool = False
    switch_reason: Optional[str] = None  # "confidence" | "shot_clock"
