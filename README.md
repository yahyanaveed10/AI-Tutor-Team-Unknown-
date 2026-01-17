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

# 3. Run a test session (1 student, 8 turns)
python -m src.main --turns 8 --max-convos 1 --set-type mini_dev
```

---

## 🏗️ Architecture: "The Peer-Reviewed Detective"

Our system uses a **Phase-based State Machine** to ensure 100% score stability:

- **Phase A: The Opener** (Turn 0) - Deploys a "Conceptual Trap" to reveal misconceptions.
- **Phase B: The Detective** (Turns 1-5) - Analyzes reasoning using Bayesian-smoothed confidence updates.
- **Phase C: The Tutor** (Post-Diagnosis) - Scales tone and depth across **Coach**, **Professor**, and **Colleague** personas.

> **Safety Layers**: Includes a deterministic **Shot-Clock** that forces tutoring at Turn 6 to guarantee a quality score even with silent students.

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
```

---

## 🚀 CLI Usage

```bash
# Standard run (all students in dev set)
python -m src.main --set-type dev

# Debug a specific student
python -m src.main --student-id <UUID> --turns 10

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
│   ├── models.py        # Pydantic data contracts
│   ├── prompts.py       # XML-tagged GPT-5.2 prompts
│   ├── config.py        # Config management (pydantic-settings)
│   └── services/
│       ├── llm.py       # New OpenAI Responses API integration
│       ├── knowunity.py # API client for K12 Student simulation
│       └── database.py  # State persistence (JSON)
├── data/
│   ├── state.json       # Detailed turn-by-turn logs
│   └── predictions.json # Final output for submission
└── docs/                # [Click here for Technical Docs](./docs/README.md)
```

---

## 📖 In-Depth Strategy

For technical details on **Confidence Smoothing**, **Persona Scaling**, and **Trap Question Logic**, see our [Strategy Guide](./docs/STRATEGY.md) and [Architecture Deep-Dive](./docs/ARCHITECTURE.md).