# Environment Setup Guide

> Complete guide to configuring your development environment.

---

## 🔧 Prerequisites

- **Python 3.10+** (3.11 recommended)
- **pip** package manager
- **Git** for version control
- **OpenAI API Key** with GPT-4o access
- **Knowunity API Key** (provided by hackathon)

---

## 📝 Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from template
cp .env.example .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-abc123...` |
| `KNOWUNITY_X_API_KEY` | Hackathon team API key | `sk_team_Ipf9tZ...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KNOWUNITY_BASE_URL` | `https://knowunity-agent-olympics-2026-api.vercel.app` | API endpoint |
| `USE_MOCK_DB` | `true` | Use local JSON instead of Google Sheets |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `MAX_RETRIES` | `3` | API retry attempts |
| `TIMEOUT_SECONDS` | `30` | API request timeout |

---

## 📦 Complete `.env.example`

```bash
# ============================================
# AI Tutor - Environment Configuration
# ============================================
# Copy this file to .env and fill in your values
# NEVER commit .env to git!

# --------------------------------------------
# REQUIRED: API Keys
# --------------------------------------------

# OpenAI API Key (get from platform.openai.com)
OPENAI_API_KEY=sk-proj-your-key-here

# Knowunity Hackathon API Key (provided by organizers)
KNOWUNITY_X_API_KEY=sk_team_your-team-key

# --------------------------------------------
# OPTIONAL: API Configuration
# --------------------------------------------

# Knowunity API base URL (usually don't change this)
# KNOWUNITY_BASE_URL=https://knowunity-agent-olympics-2026-api.vercel.app

# OpenAI model to use
# OPENAI_MODEL=gpt-4o

# --------------------------------------------
# OPTIONAL: Database Configuration
# --------------------------------------------

# Use local JSON file instead of Google Sheets
USE_MOCK_DB=true

# Path to Google credentials (if not using mock)
# GOOGLE_CREDENTIALS_JSON=/path/to/credentials.json

# Google Sheet name for state storage
# SHEET_NAME=AI-Tutor-State

# --------------------------------------------
# OPTIONAL: Application Settings
# --------------------------------------------

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# API request timeout in seconds
TIMEOUT_SECONDS=30

# Maximum retry attempts for failed API calls
MAX_RETRIES=3
```

---

## 🐍 Python Environment Setup

### Option 1: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Conda

```bash
# Create conda environment
conda create -n ai-tutor python=3.11

# Activate
conda activate ai-tutor

# Install dependencies
pip install -r requirements.txt
```

---

## ✅ Verify Setup

### 1. Check Python Version

```bash
python --version
# Should be 3.10+
```

### 2. Check Environment Variables

```bash
python -c "from src.config import settings; print('✅ Config loaded')"
```

### 3. Test API Connectivity

```bash
python testing/api_smoke_test.py
```

### 4. Test OpenAI Connection

```bash
python -c "
from openai import OpenAI
from src.config import settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)
response = client.chat.completions.create(
    model='gpt-4o',
    messages=[{'role': 'user', 'content': 'Hi'}],
    max_tokens=10
)
print('✅ OpenAI connected:', response.choices[0].message.content)
"
```

---

## 🔒 Security Best Practices

1. **Never commit `.env`** - It's in `.gitignore`
2. **Use `.env.example`** - Template without real values
3. **Rotate keys if exposed** - Regenerate immediately
4. **Use environment-specific files** - `.env.dev`, `.env.prod` if needed

---

## 🐛 Troubleshooting

### "Missing OPENAI_API_KEY"

1. Ensure `.env` file exists in project root
2. Check the key is not quoted with spaces: `OPENAI_API_KEY=sk-...` not `OPENAI_API_KEY = "sk-..."`
3. Restart your terminal/IDE after changing `.env`

### "Connection timeout"

1. Check your internet connection
2. Increase `TIMEOUT_SECONDS`
3. Try with a VPN if API is blocked

### "Invalid API Key"

1. Verify the key is correct (no extra spaces)
2. Check the key hasn't expired
3. Ensure you have GPT-4o access for OpenAI

---

## 📊 Environment for Different Stages

### Development (Local)
```bash
USE_MOCK_DB=true
LOG_LEVEL=DEBUG
```

### Testing (mini_dev set)
```bash
USE_MOCK_DB=true
LOG_LEVEL=INFO
```

### Production (eval set)
```bash
USE_MOCK_DB=false  # Use persistent storage
LOG_LEVEL=WARNING
```
