# Knowunity API Integration Guide

> Complete reference for integrating with the Knowunity Agent Olympics 2026 API.

---

## 🌐 Base URL

```
https://knowunity-agent-olympics-2026-api.vercel.app
```

---

## 🔑 Authentication

Most interaction endpoints require an API key header:

```
x-api-key: sk_team_XXXXXXXX
```

---

## 📚 API Endpoints Overview

### Catalog Endpoints (No Auth Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/students` | GET | List all available students |
| `/students/{id}/topics` | GET | Get topics for a specific student |
| `/subjects` | GET | List all subjects |
| `/topics` | GET | List all topics |

### Interaction Endpoints (Requires `x-api-key`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/interact/start` | POST | Start a new conversation |
| `/interact` | POST | Send tutor message, get student response |

### Evaluation Endpoints (Requires `x-api-key`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/evaluate/mse` | POST | Submit skill level predictions |
| `/evaluate/tutoring` | POST | Get tutoring quality score |
| `/evaluate/leaderboard/*` | GET | View leaderboards |

---

## 📋 Detailed Endpoint Reference

### 1. List Students

```bash
GET /students?set_type=dev
```

**Response:**
```json
{
  "students": [
    {
      "id": "uuid",
      "name": "Max",
      "grade_level": 10
    }
  ]
}
```

**Set Types:**
- `mini_dev` - Small test set (unlimited conversations)
- `dev` - Development set (5 conversations per student-topic)
- `eval` - Evaluation set (1 conversation per student-topic)

---

### 2. Get Student Topics

```bash
GET /students/{student_id}/topics
```

**Response:**
```json
{
  "topics": [
    {
      "id": "uuid",
      "subject_id": "uuid",
      "subject_name": "Mathematics",
      "name": "Fractions",
      "grade_level": 7
    }
  ]
}
```

---

### 3. Start Conversation

```bash
POST /interact/start
Headers: x-api-key: sk_team_XXX
Content-Type: application/json

{
  "student_id": "uuid",
  "topic_id": "uuid"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "student_id": "uuid",
  "topic_id": "uuid",
  "max_turns": 10,
  "conversations_remaining": 4
}
```

> ⚠️ **Important:** You have limited conversations per student-topic pair!

---

### 4. Interact (Send Tutor Message)

```bash
POST /interact
Headers: x-api-key: sk_team_XXX
Content-Type: application/json

{
  "conversation_id": "uuid",
  "tutor_message": "Your teaching message here"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "interaction_id": "uuid",
  "student_response": "Student's reply...",
  "turn_number": 1,
  "is_complete": false
}
```

**Limits:**
- Maximum 10 turns per conversation
- `is_complete: true` means session is done

---

### 5. Submit MSE Predictions

```bash
POST /evaluate/mse
Headers: x-api-key: sk_team_XXX

{
  "predictions": [
    {
      "student_id": "uuid",
      "topic_id": "uuid",
      "predicted_level": 3
    }
  ],
  "set_type": "dev"
}
```

**Response:**
```json
{
  "mse_score": 0.75,
  "num_predictions": 50,
  "submission_number": 1,
  "submissions_remaining": 99
}
```

**Submission Limits:**
- `mini_dev`: Unlimited
- `dev`: 100 submissions
- `eval`: 3 submissions

---

### 6. Evaluate Tutoring

```bash
POST /evaluate/tutoring
Headers: x-api-key: sk_team_XXX

{
  "set_type": "dev"
}
```

**Response:**
```json
{
  "score": 7.5,
  "num_conversations": 50,
  "submission_number": 1,
  "submissions_remaining": 99
}
```

---

## 🔄 Typical Workflow

```python
# 1. Get available students and topics
students = GET /students?set_type=dev
topics = GET /students/{student_id}/topics

# 2. For each student-topic pair:
for student in students:
    for topic in student.topics:
        # Start conversation
        conv = POST /interact/start {student_id, topic_id}
        
        # Tutor loop (max 10 turns)
        while not is_complete:
            tutor_msg = generate_message(state)
            response = POST /interact {conversation_id, tutor_message}
            update_state(response)
        
        # Save prediction
        predictions.append({
            student_id: student.id,
            topic_id: topic.id,
            predicted_level: state.estimated_level
        })

# 3. Submit all predictions
POST /evaluate/mse {predictions, set_type: "dev"}

# 4. Get tutoring score
POST /evaluate/tutoring {set_type: "dev"}
```

---

## ⚠️ Important Constraints

| Constraint | Value | Impact |
|------------|-------|--------|
| Max turns per conversation | 10 | Diagnose + tutor in 10 turns max |
| Dev conversations per pair | 5 | Limited retries |
| Eval conversations per pair | 1 | One shot only! |
| MSE submissions (dev) | 100 | Don't submit too often |
| MSE submissions (eval) | 3 | Be very careful! |

---

## 🧪 Testing Approach

1. **Start with `mini_dev`** - Unlimited conversations for development
2. **Graduate to `dev`** - Real testing with limits
3. **Final submission on `eval`** - Only 3 chances!

---

## 📝 Error Handling

Common errors to handle:

| Status | Meaning | Solution |
|--------|---------|----------|
| 422 | Validation Error | Check request body format |
| 403 | Forbidden | Check API key |
| 429 | Rate Limited | Slow down requests |
| 500 | Server Error | Retry with backoff |
