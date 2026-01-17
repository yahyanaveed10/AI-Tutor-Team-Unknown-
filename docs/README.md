# AI Tutor - Team Unknown

> **Knowunity Agent Olympics 2026 - Munich Hackathon**

## 🎯 Mission

Build an intelligent AI tutor that can:
1. **Diagnose** a student's skill level (1-5) through strategic questioning
2. **Adapt** teaching style based on the diagnosed level
3. **Track** student progress across sessions

---

## 📖 Documentation Index

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design & component overview |
| [STRATEGY.md](./STRATEGY.md) | The "Peer-Reviewed Detective" approach |
| [API_INTEGRATION.md](./API_INTEGRATION.md) | Knowunity API integration guide |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | File structure & module breakdown |
| [IMPLEMENTATION_STEPS.md](./IMPLEMENTATION_STEPS.md) | Step-by-step implementation guide |
| [ENVIRONMENT.md](./ENVIRONMENT.md) | Environment variables & configuration |

---

## 🚀 Quick Start

```bash
# 1. Clone and navigate
cd AI-Tutor-Team-Unknown-

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run the tutor agent
python main.py
```

---

## 🏗️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | Async API handling |
| LLM | OpenAI GPT-4o | Structured outputs via Pydantic |
| Database | JSON (Mock) / Google Sheets | Student state persistence |
| Validation | Pydantic | Type-safe data models |
| Config | python-dotenv | Environment management |

---

## 📊 Evaluation Metrics

The hackathon evaluates on two dimensions:

1. **MSE Score** (Skill Level Prediction)
   - Lower is better
   - Measures accuracy of level prediction (1-5)

2. **Tutoring Quality Score** (1-10)
   - Higher is better
   - Measures quality of teaching interactions

---

## 👥 Team Unknown

Built with ❤️ at the Knowunity Agent Olympics 2026, Munich.
