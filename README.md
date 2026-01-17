# 🧠 AI Tutor - Team Unknown

> **Winner-ready AI Tutor Engine** for the Knowunity Agent Olympics 2026.
> Built to infer student understanding level (1-5) and teach adaptively using **gpt-5.2-pro**.

---

## ⚡ Quick Start

```bash
# 1. Setup with uv (fast!)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your OpenAI and Knowunity API keys

# 3. Run a test session (3 students, 10 turns)
python -m src.main --turns 10 --max-convos 3 --set-type mini_dev --submit
```

---

## 🐳 Docker

```bash
# Build image
make docker-build

# Run a test session (1 student, 8 turns)
make docker-run ARGS="--turns 8 --max-convos 1 --set-type mini_dev"

# Standard run (all students in dev set)
make docker-run ARGS="--set-type dev"

# Debug a specific student
make docker-run ARGS="--student-id <UUID> --turns 10"

# Limit total conversations (for quick testing)
make docker-run ARGS="--max-convos 3"

# Submit final predictions to leaderboard
make docker-run ARGS="--submit"

# Run the Streamlit UI (uses Docker for tutor runs)
make docker-ui
```

---

## 🖥️ Streamlit UI

```bash
# Install deps
pip install -r requirements.txt

# Run UI (host)
streamlit run frontend/streamlit_app.py

# Run UI in Docker
make docker-ui
```

- Uses dev students only and runs the tutor via `make docker-run`.
- Requires Docker running and a valid `.env`.
- Includes a Pitch Mode toggle for demo-friendly agent summaries.

---

## 🏗️ Architecture: "The Peer-Reviewed Detective"

Our system uses a **Multi-Agent Orchestration** pattern with 5 specialized agents:

| Agent | Role | When Called |
|-------|------|-------------|
| **Opener** | Deploy trap question | Turn 0 |
| **Detective** | Analyze & extract evidence | Turns 1-5 |
| **Verifier** | Double-check correctness | Ambiguity zone (0.55-0.75) |
| **Tutor** | Adaptive teaching | After level frozen |
| **Finalizer** | Median of last 3 events | End of session |

> **MSE-Reducing Features**: Asymmetric level updates, confidence smoothing, verifier in ambiguity zone, deterministic finalizer.

---

## ⚙️ Configuration

Edit `.env` for persistent settings:
```bash
OPENAI_API_KEY=sk-...
KNOWUNITY_X_API_KEY=sk_team_...

# System Controls
SET_TYPE=mini_dev               # mini_dev | dev | eval
TURNS_PER_CONVERSATION=8         # Messages per session
MAX_CONVERSATIONS=0              # 0 = All students, or limit to X

# UI Controls
# Comma-separated dev student IDs for the Streamlit UI allowlist
DEV_STUDENT_IDS=1c6afe74-c388-4eb1-b82e-8326d95e29a3,2ee4a025-4845-47f4-a634-3c9e423a4b0e,2b9da93c-5616-49ca-999c-a894b9d004a3
# Optional JSON override for dev students (list or {"students": [...]})
DEV_STUDENTS_JSON=[{"id":"1c6afe74-c388-4eb1-b82e-8326d95e29a3","name":"Alex Test","grade_level":8},{"id":"2ee4a025-4845-47f4-a634-3c9e423a4b0e","name":"Sam Struggle","grade_level":9},{"id":"2b9da93c-5616-49ca-999c-a894b9d004a3","name":"Maya Advanced","grade_level":11}]
# Dataset type used by the Streamlit UI for listing + runs (mini_dev | dev | eval)
DEV_SET_TYPE=mini_dev
```

---

## 🚀 CLI Usage

```bash
# Standard run (all students in dev set)
python -m src.main --set-type dev

# Debug a specific student with more turns
python -m src.main --student-id <UUID> --turns 12

# Limit total conversations (for quick testing)
python -m src.main --max-convos 3

# Submit final predictions to leaderboard
python -m src.main --submit
```

---

## 📂 Project Structure

```bash
├── src/
│   ├── main.py          # Orchestrator & State Machine
│   ├── models.py        # Pydantic models (DiagnosticEvent, StudentState)
│   ├── prompts.py       # Agent prompts (Opener, Detective, Tutor)
│   ├── config.py        # Config management (pydantic-settings)
│   └── services/
│       ├── llm.py       # LLM agents + Verifier
│       ├── knowunity.py # API client for K12 Student simulation
│       └── database.py  # State persistence (JSON)
├── data/
│   ├── state_*.json     # Turn-by-turn chat + diagnostic events (per student-topic)
│   ├── agent_traces.json # Agent activity traces saved by CLI runs
│   └── predictions.json # Final output for submission
└── docs/
    ├── AGENTS.md        # Detailed agent documentation
    ├── STRATEGY.md      # MSE-reducing signal processing
    └── ARCHITECTURE.md  # System design & flow
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [AGENTS.md](./docs/AGENTS.md) | All 5 agents, their purpose, and when they are called |
| [STRATEGY.md](./docs/STRATEGY.md) | MSE-reducing signal processing & calibration |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, sequence diagrams, technical stack |
