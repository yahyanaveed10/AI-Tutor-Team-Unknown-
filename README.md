# 🧠 AI Tutor - Team Unknown

AI Tutor Engine** for the Knowunity Agent Olympics 2026.
> Built to infer student understanding level (1-5) and teach adaptively using **GPT-5.2-pro**.

---

## ⚡ Quick Start

```bash
# 1. Setup
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# 2. Configure
cp .env.example .env   # Add your API keys

# 3. Run (parallel, auto-submit)
python -m src.main --set-type mini_dev --turns 10 --parallel 5 --submit
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
- Includes a submit panel with confirmation and on-screen submission history.

---

## 🏗️ Architecture: "The Peer-Reviewed Detective"

Multi-Agent Orchestration with **GPT-5.2 prompt patterns**:
| Agent | Role | Trigger / Pattern |
|-------|------|-------------------|
| **Opener** | Trap question | Turn 0 + `<discriminative_power>` |
| **Detective** | Analyze evidence | Turns 1-5 + `<calibration_rules>`, `<self_check>` |
| **Verifier** | Double-check | Ambiguity zone (0.55-0.75), fast gpt-5.2 |
| **Tutor** | Adaptive teaching | After level frozen |
| **Finalizer** | Median of last 3 | Deterministic stabilization |

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
# Parallel processing (5 students at once)
python -m src.main --set-type mini_dev --parallel 5 --submit

# Debug single student
python -m src.main --student-id <UUID> --turns 12

# Limit total conversations
python -m src.main --max-convos 3

# Analyze submission history
python scripts/analyze_submissions.py
```

### Key Flags
| Flag | Description |
|------|-------------|
| `--parallel N` | Run N students concurrently |
| `--submit` | Submit predictions + log history |
| `--max-convos N` | Limit to N conversations |
| `--turns N` | Messages per session |
| `--set-type` | `mini_dev` / `dev` / `eval` |

---

## 📂 Project Structure

```
├── src/
│   ├── main.py          # Orchestrator (parallel + feedback loop)
│   ├── models.py        # Pydantic models
│   ├── prompts.py       # GPT-5.2 optimized prompts
│   └── services/
│       ├── llm.py       # LLM agents + Verifier
│       ├── knowunity.py # API client
│       └── database.py  # Per-student state files
├── data/
│   ├── state_*.json     # Turn-by-turn chat + diagnostic events (per student-topic)
│   ├── agent_traces.json # Agent activity traces saved by CLI runs
│   ├── predictions.json # Final predictions
│   └── submission_history.json  # MSE tracking
├── scripts/
│   └── analyze_submissions.py   # MSE trend analysis
└── docs/
    ├── AGENTS.md        # Agent documentation
    ├── STRATEGY.md      # MSE-reducing strategies
    └── ARCHITECTURE.md  # System design
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [AGENTS.md](./docs/AGENTS.md) | All 5 agents and their GPT-5.2 prompts |
| [STRATEGY.md](./docs/STRATEGY.md) | MSE-reducing signal processing & calibration |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, sequence diagrams, technical stack |

---

## 🎯 MSE-Reducing Features

1. **Asymmetric Updates** - 2 votes for promotion, strong evidence for demotion
2. **Confidence Smoothing** - Max +0.15/turn
3. **Verifier** - Ambiguity zone (0.50-0.65) double-check
4. **Early Exit** - Skip diagnosis when confidence ≥0.85 + 3 events
5. **Deterministic Finalizer** - Median of last 3 events
6. **GPT-5.2 Calibration** - `<calibration_rules>` + `<self_check>`
