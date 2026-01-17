# 🧠 AI Tutor - Team Unknown

> **Winner-ready AI Tutor Engine** for the Knowunity Agent Olympics 2026.
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

## 🏗️ Architecture: "The Peer-Reviewed Detective"

Multi-Agent Orchestration with **GPT-5.2 prompt patterns**:

| Agent | Role | GPT-5.2 Pattern |
|-------|------|-----------------|
| **Opener** | Trap question | `<discriminative_power>` |
| **Detective** | Analyze evidence | `<calibration_rules>`, `<self_check>` |
| **Verifier** | Double-check | Fast gpt-5.2 (medium reasoning) |
| **Tutor** | Adaptive teaching | Persona-based prompts |
| **Finalizer** | Median of last 3 | Deterministic stabilization |

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

## ⚙️ Configuration

Edit `.env`:
```bash
OPENAI_API_KEY=sk-...
KNOWUNITY_X_API_KEY=sk_team_...
SET_TYPE=mini_dev
```

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
│   ├── state_{id}.json  # Per-student state (parallel-safe)
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
| [STRATEGY.md](./docs/STRATEGY.md) | MSE-reducing signal processing |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design & flow |

---

## 🎯 MSE-Reducing Features

1. **Asymmetric Updates** - 2 votes for promotion, strong evidence for demotion
2. **Confidence Smoothing** - Max +0.15/turn
3. **Verifier** - Ambiguity zone (0.50-0.65) double-check
4. **Early Exit** - Skip diagnosis when confidence ≥0.85 + 3 events
5. **Deterministic Finalizer** - Median of last 3 events
6. **GPT-5.2 Calibration** - `<calibration_rules>` + `<self_check>`