# Project Structure

> Clean, modular file organization for the AI Tutor system.

---

## 📁 Directory Layout

```
AI-Tutor-Team-Unknown-/
│
├── 📄 .env.example          # Environment template
├── 📄 .env                   # Your local config (gitignored)
├── 📄 .gitignore             # Git ignore rules
├── 📄 README.md              # Project overview
├── 📄 requirements.txt       # Python dependencies
│
├── 📁 docs/                  # 📚 Documentation
│   ├── README.md             # Docs index
│   ├── STRATEGY.md           # The teaching strategy
│   ├── ARCHITECTURE.md       # System design
│   ├── API_INTEGRATION.md    # Knowunity API guide
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── IMPLEMENTATION_STEPS.md # Step-by-step guide
│   └── ENVIRONMENT.md        # Environment setup
│
├── 📁 src/                   # 🧠 Source Code
│   ├── __init__.py
│   ├── main.py               # Orchestrator / Entry point
│   ├── models.py             # Pydantic data models
│   ├── prompts.py            # LLM system prompts
│   ├── config.py             # Configuration loader
│   │
│   ├── 📁 services/          # Business logic
│   │   ├── __init__.py
│   │   ├── llm.py            # OpenAI interactions
│   │   ├── database.py       # State persistence
│   │   └── knowunity.py      # Knowunity API client
│   │
│   └── 📁 utils/             # Helper utilities
│       ├── __init__.py
│       └── logging.py        # Logging configuration
│
├── 📁 scripts/               # 🔧 Utility Scripts
│   ├── run_batch.py          # Batch evaluation runner
│   ├── submit_predictions.py # Submit to MSE endpoint
│   └── test_single.py        # Test single conversation
│
├── 📁 data/                  # 💾 Local Data (gitignored)
│   ├── state_*.json          # Turn-by-turn chat history (per student-topic)
│   ├── agent_traces.json     # Agent activity traces saved by CLI runs
│   └── predictions.json      # Saved predictions
│
└── 📁 testing/               # 🧪 Tests
    ├── api_smoke_test.py     # API connectivity test
    └── test_*.py             # Unit tests
```

---

## 📄 File Responsibilities

### Root Files

| File | Purpose |
|------|---------|
| `.env.example` | Template for environment variables |
| `.env` | Your actual configuration (never commit!) |
| `requirements.txt` | Python package dependencies |
| `README.md` | Project introduction |

### Source Files (`src/`)

| File | Responsibility |
|------|----------------|
| `main.py` | Entry point, orchestrates the tutoring flow |
| `models.py` | Pydantic schemas for type safety |
| `prompts.py` | All LLM system prompts |
| `config.py` | Loads and validates .env configuration |

### Services (`src/services/`)

| File | Responsibility |
|------|----------------|
| `llm.py` | OpenAI API interactions, structured outputs |
| `database.py` | State persistence (mock JSON or Google Sheets) |
| `knowunity.py` | Knowunity API client wrapper |

### Scripts (`scripts/`)

| File | Purpose |
|------|---------|
| `run_batch.py` | Run tutor on all student-topic pairs |
| `submit_predictions.py` | Format and submit predictions to API |
| `test_single.py` | Debug a single conversation |

---

## 🔄 Import Structure

```python
# In main.py
from src.config import settings
from src.models import StudentState, DetectiveOutput
from src.prompts import PROMPT_OPENER, PROMPT_DETECTIVE, PROMPT_TUTOR
from src.services.llm import LLMService
from src.services.database import DatabaseService
from src.services.knowunity import KnowunityClient

# Usage
llm = LLMService(api_key=settings.OPENAI_API_KEY)
db = DatabaseService(mock_mode=settings.USE_MOCK_DB)
knowunity = KnowunityClient(api_key=settings.KNOWUNITY_X_API_KEY)
```

---

## 📝 Design Principles

### 1. **Separation of Concerns**
Each file has one clear responsibility:
- `llm.py` only talks to OpenAI
- `database.py` only handles persistence
- `main.py` only coordinates

### 2. **Configuration via Environment**
All secrets and settings in `.env`:
```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    KNOWUNITY_X_API_KEY: str
    USE_MOCK_DB: bool = True
    
    class Config:
        env_file = ".env"
```

### 3. **Type Safety with Pydantic**
All data structures are typed:
```python
# models.py
class StudentState(BaseModel):
    student_id: str
    turn_count: int = 0
    estimated_level: int = 3
    confidence: float = 0.0
```

### 4. **Testability**
Services accept dependencies via constructor:
```python
# Easy to mock in tests
llm = LLMService(client=mock_openai_client)
```

---

## 📦 Minimal Dependencies

We keep dependencies lean:

```txt
# requirements.txt
fastapi>=0.100.0      # Optional: only if webhook needed
uvicorn>=0.23.0       # Optional: only if webhook needed
openai>=1.0.0         # LLM interactions
pydantic>=2.0.0       # Data validation
python-dotenv>=1.0.0  # Environment loading
httpx>=0.25.0         # Async HTTP client
```

---

## 🚫 What Goes in .gitignore

```gitignore
# Environment
.env

# Local data
data/
*.json

# Python
__pycache__/
*.pyc
.venv/
venv/

# IDE
.idea/
.vscode/
*.swp
```
