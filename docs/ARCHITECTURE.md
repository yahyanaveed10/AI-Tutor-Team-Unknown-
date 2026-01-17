# System Architecture

> A clean, modular design for our AI Tutor system.

---

## 🏗️ High-Level Component View

```mermaid
graph TB
    subgraph "Knowunity Platform"
    API[K12 Student API]
    end

    subgraph "AI Tutor Engine (Local)"
    Main[main.py: Orchestrator]
    LLM[services/llm.py: Brain]
    DB[services/database.py: State]
    Models[models.py: Data Schema]
    Prompts[prompts.py: Prompt Store]
    end

    subgraph "OpenAI Cloud"
    GPT5[GPT-5.2-pro]
    end

    Main --> API
    Main --> LLM
    Main --> DB
    LLM --> GPT5
    LLM --> Models
    LLM --> Prompts
    DB -.-> StateFile[(data/state.json)]
```

---

## 🔄 Interaction Sequence

The following diagram illustrates a single interaction loop, highlighting the transition from diagnosis to tutoring.

```mermaid
sequenceDiagram
    participant S as Student (Knowunity API)
    participant C as Controller (main.py)
    participant L as LLM Service (gpt-5.2-pro)
    participant D as State Store (JSON)

    Note over C, D: Session Start
    C->>L: generate_opener(topic)
    L-->>C: "Trap Question"
    C->>S: POST /interact/start
    
    Loop for 8nd-10th Turns
        S-->>C: Student Response
        C->>D: Load StudentState
        
        alt Diagnosis Mode (unfrozen)
            C->>L: analyze(state, response)
            L-->>C: {level, conf, misconception, next_msg}
            C->>C: Apply Smoothing (max +0.2)
            C->>C: Check Shot-Clock (Turn 6)
        else Tutoring Mode (level frozen)
            C->>L: tutor(state, response)
            L-->>C: student-facing pedagogic content
        end
        
        C->>D: Save Updated State
        C->>S: POST /interact (message)
    end
```

---

## 🛠️ The Technical Stack

### 1. **gpt-5.2-pro** (The "Brain")
We utilize the advanced reasoning capabilities of `gpt-5.2-pro` for all phases:
- **Reasoning Effort**: Set to `high` for diagnosis and `medium` for tutoring to balance depth vs latency.
- **Responses API**: Direct integration with the New OpenAI Responses API for optimized instruction following.

### 2. **Pydantic & JSON Schema** (The "Glue")
The **Detective** doesn't just return text; it returns a strict `DetectiveOutput` JSON.
- **Reliability**: Eliminates the need for fragile regex parsing.
- **Type Safety**: Ensure the controller always gets valid `confidence` and `estimated_level` integers.

### 3. **Deterministic State Machine** (The "Controller")
While the LLM provides signals, the **Python Controller** makes the life-or-death decisions:
- **Confidence Smoothing**: Prevents a single lucky guess from inflating confidence.
- **Level Freezing**: Locks the diagnosis once `confidence >= 0.75` to prevent late-game drift.
- **Shot Clock**: Guarantees tutoring starts by Turn 6, even if signals are weak.

---

## ✍️ Prompt Engineering Patterns

Our `prompts.py` utilizes modern patterns to maximize LLM performance:

### XML-like Tagging
We use `<task>`, `<context>`, and `<constraints>` tags to clearly demarcate instructions. This helps `gpt-5.2` prioritize system goals over user-injected text.

### Zero-Shot Chain of Thought
The `DETECTIVE` prompt is instructed to:
- Evaluate **Correctness**
- Measure **Depth**
- Identify **Misconceptions**
- *Before* outputting the final level and confidence.

### Level-Adaptive Personas
We don't use a single "Tutor" persona. Instead, we scale the tone and Socratic depth:
- **Coach (L1-2)**: High scaffolding, simple vocabulary, positive reinforcement.
- **Professor (L3-4)**: Socratic method, conceptual challenges, deep-dives.
- **Colleague (L5)**: High-level peer discussion, edge cases, minimal scaffolding.

---

## 📊 State Management (`StudentState`)

We persist the full state in `data/state.json` after every turn.

| Field | Purpose |
|-------|---------|
| `history` | List of `Message` objects for LLM context |
| `turn_count` | Limits diagnostic turns vs tutoring turns |
| `estimated_level` | The "Golden Metric" for the MSE score |
| `confidence` | Used to trigger the phase transition |
| `misconceptions` | Key list of items the Tutor must address |
