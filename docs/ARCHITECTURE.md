# System Architecture

> A clean, modular design for our AI Tutor system.

---

## 🏗️ High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KNOWUNITY API                                      │
│                    (Student Simulation Endpoint)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              main.py                                         │
│                         (Orchestrator)                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  API Client     │  │  Tutor Agent    │  │  Submission Generator      │  │
│  │  (Knowunity)    │  │  (Core Logic)   │  │  (Batch Evaluation)        │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
          │ services/   │   │   models.py │   │  prompts.py │
          │  llm.py     │   │  (Pydantic) │   │  (System    │
          │  sheets.py  │   │             │   │   Prompts)  │
          └─────────────┘   └─────────────┘   └─────────────┘
                │
                ▼
    ┌───────────────────────┐
    │    OpenAI API         │
    │    (gpt-4o)           │
    └───────────────────────┘
```

---

## 📦 Component Breakdown

### 1. **main.py** - The Orchestrator

The central controller that:
- Connects to the Knowunity API
- Manages conversation flow
- Coordinates between services
- Handles the main tutoring loop

```python
# Simplified flow
async def tutor_session(student_id: str, topic_id: str):
    # 1. Start conversation
    conv = await knowunity.start_conversation(student_id, topic_id)
    
    # 2. Initialize or retrieve state
    state = db.get_or_create_state(student_id, topic_id)
    
    # 3. Main tutoring loop
    while not conv.is_complete:
        # Generate tutor message based on phase
        tutor_msg = await llm.generate_response(state, last_student_msg)
        
        # Send to student, get response
        response = await knowunity.interact(conv.id, tutor_msg)
        
        # Update state
        state = await llm.analyze_and_update(state, response)
        db.save_state(state)
    
    # 4. Return final prediction
    return state.estimated_level
```

### 2. **services/llm.py** - The Brain

Handles all LLM interactions:
- Phase determination (Opener/Diagnosis/Tutoring)
- Structured output generation
- Detective analysis
- Tutor response generation

**Key Design Decision:** Uses OpenAI's structured outputs (Pydantic parsing) for reliable, type-safe responses.

### 3. **services/database.py** - State Persistence

Provides a unified interface for state storage:
- **Mock Mode**: Uses local `db.json` for development
- **Production Mode**: Can connect to Google Sheets or other backends

**Why Abstraction?** Easy to swap backends without changing core logic.

### 4. **models.py** - Data Contracts

Pydantic models ensuring type safety:

```python
class DetectiveOutput(BaseModel):
    """What the LLM returns during diagnosis phase"""
    is_correct: bool
    reasoning_score: int  # 1-5
    misconception: Optional[str]
    estimated_level: int  # 1-5
    confidence: float  # 0.0-1.0
    next_question: str

class StudentState(BaseModel):
    """Internal state we track for each student"""
    student_id: str
    topic_id: str
    turn_count: int
    estimated_level: int
    confidence: float
    chat_history: List[Message]
    misconceptions: List[str]
```

### 5. **prompts.py** - System Prompts

Centralized prompt storage for:
- Opener prompts (trap questions)
- Detective prompts (analysis)
- Tutor prompts (per persona)

**Why Separate?** Easy to iterate and tune prompts without touching logic.

---

## 🔄 Request Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       SINGLE TURN FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. RECEIVE          2. HYDRATE           3. DETERMINE              │
│  Student Response    Load State           Phase                     │
│       │                  │                    │                     │
│       ▼                  ▼                    ▼                     │
│  ┌─────────┐        ┌─────────┐          ┌─────────┐               │
│  │ Knowunity│        │Database │          │ Router  │               │
│  │ Response │───────▶│  State  │─────────▶│ Logic   │               │
│  └─────────┘        └─────────┘          └─────────┘               │
│                                               │                     │
│                          ┌────────────────────┼────────────────┐    │
│                          ▼                    ▼                ▼    │
│                     Phase A              Phase B           Phase C  │
│                     OPENER              DIAGNOSIS         TUTORING  │
│                          │                    │                │    │
│                          ▼                    ▼                ▼    │
│                     Generate            Analyze &         Teach at  │
│                     Trap Q              Update Level      Level     │
│                          │                    │                │    │
│                          └────────────────────┴────────────────┘    │
│                                               │                     │
│  4. PERSIST          5. RESPOND                                     │
│  Save State          Return Message                                 │
│       │                  │                                          │
│       ▼                  ▼                                          │
│  ┌─────────┐        ┌─────────┐                                    │
│  │Database │        │ Knowunity│                                    │
│  │  Save   │        │  Send   │                                    │
│  └─────────┘        └─────────┘                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Environment Configuration

All sensitive configuration via `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for GPT-4o |
| `KNOWUNITY_X_API_KEY` | ✅ | Hackathon API key |
| `KNOWUNITY_BASE_URL` | ❌ | API URL (has default) |
| `LOG_LEVEL` | ❌ | Logging verbosity |
| `USE_MOCK_DB` | ❌ | Force mock database mode |

---

## 🧪 Testing Strategy

```
tests/
├── test_models.py        # Pydantic model validation
├── test_llm.py           # LLM service (mocked)
├── test_database.py      # Database operations
├── test_integration.py   # End-to-end flow
└── conftest.py           # Pytest fixtures
```

---

## 📊 Observability

Every step is logged for transparency:

```python
import logging

logger = logging.getLogger("ai_tutor")

# Log at key decision points
logger.info(f"Turn {turn}: Phase={phase}, Level={level}, Confidence={conf}")
logger.debug(f"Detective Output: {detective_output.model_dump_json()}")
```

---

## 🚀 Deployment Options

1. **Local Development**: `python main.py`
2. **Production**: FastAPI + Uvicorn (if webhook needed)
3. **Batch Mode**: `python run_batch.py` for evaluation
