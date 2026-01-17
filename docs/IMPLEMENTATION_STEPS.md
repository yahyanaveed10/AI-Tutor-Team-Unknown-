# Implementation Steps

> Step-by-step guide to build the AI Tutor system.

---

## 📋 Implementation Checklist

### Phase 0: Setup (30 min)
- [ ] Create project structure
- [ ] Set up `.env` and `requirements.txt`
- [ ] Configure logging
- [ ] Verify API connectivity

### Phase 1: Core Models (20 min)
- [ ] Define `StudentState` model
- [ ] Define `DetectiveOutput` model
- [ ] Define `Message` and `ChatHistory` models
- [ ] Add validation rules

### Phase 2: Configuration (15 min)
- [ ] Create `config.py` with Pydantic Settings
- [ ] Load all environment variables
- [ ] Add sensible defaults

### Phase 3: Services (45 min)
- [ ] Implement `KnowunityClient` service
- [ ] Implement `DatabaseService` (mock mode)
- [ ] Implement `LLMService` with structured outputs

### Phase 4: Core Logic (45 min)
- [ ] Implement phase detection logic
- [ ] Create opener prompt and logic
- [ ] Create detective prompt and analysis
- [ ] Create tutor prompts (per persona)

### Phase 5: Orchestrator (30 min)
- [ ] Build main tutoring loop
- [ ] Handle conversation lifecycle
- [ ] Implement error handling and retries

### Phase 6: Batch Runner (20 min)
- [ ] Create script to run all student-topic pairs
- [ ] Save predictions to file
- [ ] Create submission script

### Phase 7: Testing & Tuning (ongoing)
- [ ] Test on `mini_dev` set
- [ ] Tune prompts based on results
- [ ] Graduate to `dev` set
- [ ] Final submission on `eval`

---

## 📝 Detailed Implementation Guide

### Step 1: Project Setup

```bash
# Create directory structure
mkdir -p src/services src/utils scripts data docs testing

# Create empty __init__.py files
touch src/__init__.py src/services/__init__.py src/utils/__init__.py
```

**Create `requirements.txt`:**
```txt
openai>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
httpx>=0.25.0
```

**Create `.env.example`:**
```bash
# Required
OPENAI_API_KEY=sk-...
KNOWUNITY_X_API_KEY=sk_team_...

# Optional
KNOWUNITY_BASE_URL=https://knowunity-agent-olympics-2026-api.vercel.app
USE_MOCK_DB=true
LOG_LEVEL=INFO
```

---

### Step 2: Configuration Module

**Create `src/config.py`:**

```python
"""Configuration management via environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # Required
    OPENAI_API_KEY: str
    KNOWUNITY_X_API_KEY: str
    
    # Optional with defaults
    KNOWUNITY_BASE_URL: str = "https://knowunity-agent-olympics-2026-api.vercel.app"
    USE_MOCK_DB: bool = True
    LOG_LEVEL: str = "INFO"
    OPENAI_MODEL: str = "gpt-4o"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()
```

---

### Step 3: Data Models

**Create `src/models.py`:**

```python
"""Pydantic models for type-safe data handling."""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Phase(str, Enum):
    OPENER = "opener"
    DIAGNOSIS = "diagnosis"
    TUTORING = "tutoring"


class Message(BaseModel):
    """A single message in the chat history."""
    role: str  # "tutor" or "student"
    content: str
    turn: int


class DetectiveOutput(BaseModel):
    """Structured output from the LLM during diagnosis phase."""
    is_correct: bool = Field(description="Was the student's answer correct?")
    reasoning_score: int = Field(ge=1, le=5, description="Quality of reasoning 1-5")
    misconception: Optional[str] = Field(description="Identified misconception, if any")
    estimated_level: int = Field(ge=1, le=5, description="Estimated skill level 1-5")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in level estimate")
    next_question: str = Field(description="Next diagnostic or teaching message")


class TutorOutput(BaseModel):
    """Structured output from the LLM during tutoring phase."""
    message: str = Field(description="The tutoring message to send")
    level_adjustment: int = Field(default=0, ge=-1, le=1, description="Level adjustment -1/0/+1")


class StudentState(BaseModel):
    """Complete state for a student-topic session."""
    student_id: str
    topic_id: str
    topic_name: str = ""
    turn_count: int = 0
    estimated_level: int = 3  # Start at middle
    confidence: float = 0.0
    phase: Phase = Phase.OPENER
    chat_history: List[Message] = []
    misconceptions: List[str] = []
    conversation_id: Optional[str] = None
```

---

### Step 4: System Prompts

**Create `src/prompts.py`:**

```python
"""System prompts for the AI Tutor."""

PROMPT_OPENER = """You are an expert tutor about to assess a student's knowledge of {topic}.

Your task: Generate ONE diagnostic "trap question" that reveals the student's understanding level.

Rules:
1. Do NOT greet the student or say hello
2. Ask a conceptual question that tests understanding, not memorization
3. The question should distinguish between surface knowledge and deep understanding
4. Make it appropriate for a {grade_level} grade student

Examples of good trap questions:
- "Which is bigger: 1/3 or 1/4? Explain your reasoning."
- "If I push a box but it doesn't move, did I do work? Why?"
- "Can two different chemical reactions produce the same product?"

Generate only the question, nothing else."""

PROMPT_DETECTIVE = """You are a Council of Educational Experts analyzing a student's response.

Topic: {topic}
Grade Level: {grade_level}
Turn: {turn}/{max_turns}

Previous conversation:
{chat_history}

Student's latest response: "{student_response}"

Analyze this response and provide:

1. CORRECTNESS: Is the answer factually correct?
2. REASONING DEPTH (1-5):
   - 1: No reasoning, just guessing
   - 2: Some reasoning, major gaps
   - 3: Reasonable logic, minor errors
   - 4: Strong reasoning, shows understanding
   - 5: Expert-level explanation

3. MISCONCEPTIONS: Identify any flawed mental models

4. LEVEL ESTIMATE (1-5):
   - Level 1: Fundamental gaps, needs to start from basics
   - Level 2: Knows basics, struggles with application
   - Level 3: Solid understanding, occasional errors
   - Level 4: Strong grasp, handles complexity well
   - Level 5: Mastery level, could teach others

5. CONFIDENCE: How confident are you in this estimate? (0.0-1.0)
   - Consider consistency with previous responses
   - Higher turns should yield higher confidence

6. NEXT QUESTION: Generate a follow-up that either:
   - Further diagnoses if confidence < 0.8
   - Begins teaching if confident enough

Be analytical and precise. Your goal is to accurately assess the student's true level."""

PROMPT_TUTOR_SCAFFOLDING = """You are a patient, encouraging tutor for a Level {level} student (struggling learner).

Topic: {topic}
Identified Misconceptions: {misconceptions}

Student's message: "{student_message}"

Teaching approach for Level {level}:
- Use simple, clear explanations
- Provide step-by-step guidance
- Give concrete examples and analogies
- Encourage and celebrate small wins
- Never make them feel bad for not knowing

Chat history:
{chat_history}

Respond in a warm, supportive way that builds their confidence while teaching."""

PROMPT_TUTOR_SOCRATIC = """You are a Socratic tutor for a Level {level} student (advanced learner).

Topic: {topic}
Identified Strengths: High reasoning ability

Student's message: "{student_message}"

Teaching approach for Level {level}:
- Ask thought-provoking questions
- Push them to discover answers themselves
- Challenge their assumptions
- Connect to advanced concepts
- Avoid giving direct answers; guide discovery

Chat history:
{chat_history}

Respond with questions that deepen their understanding and push their thinking."""

PROMPT_TUTOR_BALANCED = """You are a balanced tutor for a Level {level} student (solid learner).

Topic: {topic}
Identified Misconceptions: {misconceptions}

Student's message: "{student_message}"

Teaching approach for Level {level}:
- Mix explanation with questions
- Build on what they know
- Correct misconceptions gently
- Provide moderate challenge
- Keep engagement high

Chat history:
{chat_history}

Respond in a way that maintains their interest while strengthening understanding."""
```

---

### Step 5: Services

**See `ARCHITECTURE.md` for detailed service specifications.**

Key implementation notes:

1. **LLMService**: Use `client.beta.chat.completions.parse()` for structured outputs
2. **DatabaseService**: Start with JSON mock, add Sheets later if needed
3. **KnowunityClient**: Simple HTTP wrapper with error handling

---

### Step 6: Main Orchestrator

**See `ARCHITECTURE.md` for the main loop structure.**

Key decision points:
```python
def determine_phase(state: StudentState) -> Phase:
    if state.turn_count == 0:
        return Phase.OPENER
    elif state.turn_count < 6 and state.confidence < 0.8:
        return Phase.DIAGNOSIS
    else:
        return Phase.TUTORING
```

---

## 🎯 Success Criteria

Before considering the implementation complete:

1. ✅ Can run a full conversation with a student
2. ✅ Correctly diagnoses level within 6 turns
3. ✅ Adapts teaching style based on level
4. ✅ Persists state between turns
5. ✅ Can batch-run all students and submit predictions
6. ✅ MSE score < 1.5 on dev set
7. ✅ Tutoring score > 6 on dev set

---

## 🐛 Debugging Tips

1. **Enable verbose logging**: `LOG_LEVEL=DEBUG`
2. **Test one student first**: Use `scripts/test_single.py`
3. **Check structured outputs**: Log the raw LLM response
4. **Verify API responses**: Use the smoke test script
