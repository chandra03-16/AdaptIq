# AdaptIQ — AI-Driven Adaptive Diagnostic Engine

> A 1-Dimension Adaptive Testing prototype for GRE-style questions, built with FastAPI, MongoDB, IRT, and Google Gemini AI.

---

## Table of Contents
1. [Architecture Overview](#architecture)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Setup & Run](#setup--run)
5. [API Documentation](#api-documentation)
6. [Adaptive Algorithm](#adaptive-algorithm-deep-dive)
7. [AI Integration](#ai-integration)
8. [Project Structure](#project-structure)
9. [AI Log](#ai-log)

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Frontend (index.html)               │
│  Pure HTML/CSS/JS SPA — no build step required       │
└────────────────────┬─────────────────────────────────┘
                     │ REST (CORS-enabled)
┌────────────────────▼─────────────────────────────────┐
│              FastAPI Backend (main.py)               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  IRT Engine │  │  AI Insights │  │  DB Layer   │ │
│  │(adaptive_   │  │(ai_insights  │  │(database.py)│ │
│  │ engine.py)  │  │    .py)      │  │             │ │
│  └─────────────┘  └──────┬───────┘  └──────┬──────┘ │
└──────────────────────────┼──────────────────┼────────┘
                           │                  │
               ┌───────────▼───┐    ┌─────────▼────────┐
               │  Gemini API   │    │   MongoDB Local   │
               │ gemini-1.5-   │    │ questions/sessions│
               │    flash      │    │                  │
               └───────────────┘    └──────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Backend | FastAPI + Uvicorn |
| Database | MongoDB (Motor async driver) |
| AI | Google Gemini (`gemini-1.5-flash`) |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Schema Validation | Pydantic v2 |

---

## Prerequisites

- Python 3.11+
- MongoDB Community Server (local `localhost:27017`)
- Google Gemini API key — free, no card required ([aistudio.google.com](https://aistudio.google.com))

---

## Setup & Run

### 1. Clone & enter the repo
```bash
git clone https://github.com/your-username/adaptive-diagnostic-engine
cd adaptive-diagnostic-engine
```

### 2. Install dependencies
```bash
pip install fastapi uvicorn motor pydantic python-dotenv google-generativeai
```

### 3. Configure environment variables
Create a new file named `.env` in the project folder with this content:

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=adaptive_engine
GEMINI_API_KEY=AIzaSy...your key here
MAX_QUESTIONS=10
INITIAL_ABILITY=0.5
```

> Get your free Gemini API key at [aistudio.google.com](https://aistudio.google.com) → API Keys → Create API Key. No credit card required.

### 4. Start the backend
Open a terminal in the project folder and run:
```bash
python -m uvicorn main:app --reload
```

You should see:
```
[DB] Connected to MongoDB at mongodb://localhost:27017
[Seed] Done — 25 questions in the collection.
Uvicorn running on http://127.0.0.1:8000
```

### 5. Serve the frontend
Open a **second terminal** in the same folder and run:
```bash
python -m http.server 3000
```

### 6. Open the app
Go to your browser and visit:
```
http://127.0.0.1:3000/index.html
```

Make sure the API URL box at the top right says `http://127.0.0.1:8000`, enter your name and click **Begin Test**!

> ⚠️ **Important:** Keep both terminals running while using the app. Do not open `index.html` by double-clicking — always use `http://127.0.0.1:3000/index.html`.

---

## API Documentation

### Base URL: `http://localhost:8000`

Interactive docs available at: `http://localhost:8000/docs`

---

### `GET /healthz`
Liveness probe.

**Response:**
```json
{ "status": "ok", "timestamp": "2025-01-15T10:00:00Z" }
```

---

### `POST /sessions/start`
Start a new test session.

**Request body:**
```json
{ "student_name": "Alice" }
```

**Response `201`:**
```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "message": "Session created for Alice. Good luck!"
}
```

---

### `GET /sessions/{session_id}`
Get current session state.

**Response `200`:**
```json
{
  "session_id": "...",
  "student_name": "Alice",
  "ability_score": 0.62,
  "questions_answered": 4,
  "responses": [ ... ],
  "is_complete": false,
  "study_plan": null
}
```

---

### `GET /sessions/{session_id}/next`
Fetch the next adaptive question (selected by IRT maximum information).

**Response `200`:**
```json
{
  "question_id": "ALG003",
  "text": "If f(x) = 2x² + 3x - 5, what is f(-2)?",
  "options": { "A": "-7", "B": "-3", "C": "1", "D": "9" },
  "topic": "Algebra",
  "difficulty": 0.5,
  "question_number": 5
}
```

**Errors:**
- `400` — Session already complete
- `404` — No more questions available

---

### `POST /sessions/{session_id}/answer`
Submit an answer. Updates ability via IRT. Generates AI study plan on last question.

**Request body:**
```json
{
  "session_id": "...",
  "question_id": "ALG003",
  "selected_answer": "A"
}
```

**Response `200`:**
```json
{
  "is_correct": true,
  "correct_answer": "A",
  "ability_score": 0.68,
  "questions_answered": 5,
  "is_complete": false,
  "study_plan": null
}
```

When `is_complete: true`, `study_plan` contains the Gemini-generated markdown study plan.

---

## Adaptive Algorithm Deep Dive

### Model: 1-Parameter Logistic IRT (Rasch Model)

The probability of a correct response is:

```
P(correct | θ, b) = 1 / (1 + exp(-(θ - b)))
```

Where:
- **θ** (theta) = student ability (internal logit scale)
- **b** = question difficulty (internal logit scale)
- At `θ = b`, there is exactly a 50% chance of a correct answer

### Ability Update (Newton–Raphson MLE Step)

After each response:
```
θ_new = θ_old + (r - P) / (P × (1 - P))
```

Where:
- `r = 1` if correct, `r = 0` if incorrect
- `P` = predicted probability from the model above
- `P × (1 - P)` is Fisher information (gradient step size adapts automatically)

The denominator (Fisher information) ensures:
- Large updates when the item was near 50/50 difficulty (high information)
- Small updates when the item was very easy or very hard (low information)

Ability is clamped to `[-3, 3]` logits to prevent extreme estimates from sparse early data.

### Question Selection (Maximum Information)

For each new question, we select the **unseen question whose difficulty is closest to the current ability estimate**. At the 1PL model, Fisher information is maximised exactly at `b = θ`, so this rule maximally reduces ability estimation error per question.

### Scale Mapping

| Scale | Range | Used For |
|-------|-------|---------|
| DB difficulty | `[0.1, 1.0]` | Stored in MongoDB |
| Internal logits | `[-2.0, 2.0]` | IRT computation |
| Display ability | `[0.0, 1.0]` | API responses & UI |

---

## AI Integration

At test completion, the session's performance data is sent to **Google Gemini**:

```python
# Prompt structure
f"""You are an expert GRE tutor. A student just completed an adaptive diagnostic test.
Here is their performance summary:

{summary}   # per-topic accuracy, difficulty reached, final ability

Create a personalised 3-step study plan..."""
```

The generated plan covers:
1. Weakest topics first (derived from per-topic accuracy stats)
2. Specific, actionable study activities
3. Recommended difficulty progression

Model used: `gemini-1.5-flash` (free tier, no credit card needed)

---

## Project Structure

```
adaptive-diagnostic-engine/
├── backend/
│   ├── main.py              # FastAPI app, all route handlers
│   ├── models.py            # Pydantic schemas (Question, UserSession, …)
│   ├── database.py          # Motor async MongoDB client
│   ├── adaptive_engine.py   # 1PL IRT maths & question selection
│   ├── ai_insights.py       # Google Gemini study plan generation
│   ├── seed_data.py         # 25 GRE questions, idempotent seeder
│   └── requirements.txt
├── frontend/
│   └── index.html           # Single-file SPA (pastel blue + pink theme)
├── .env.example             # Template — copy to .env and fill in keys
└── README.md
```

---

## AI Log

### How AI tooling accelerated development

**Code scaffolding**: Claude (Anthropic) generated the initial FastAPI route structure, Pydantic model definitions, and Motor async patterns — saving ~2 hours of boilerplate writing.

**IRT implementation**: The Newton–Raphson MLE update formula and numerical stability guards (clamping, information floor) were refined with AI assistance, cross-checked against psychometrics literature.

**Question authoring**: All 25 GRE-style questions (Algebra, Geometry, Vocabulary, Data Analysis, Critical Reasoning) were authored with AI help to ensure they were GRE-authentic in style and difficulty calibration.

**Prompt engineering**: The Gemini study-plan prompt went through several iterations to produce structured, topic-specific advice rather than generic encouragement.

### Challenges AI could not fully solve

**MongoDB aggregation logic**: Motor's async API differs from pymongo in subtle ways (cursor exhaustion, list coercion). Needed manual debugging of `.to_list(length=None)` vs `.to_list(100)` behaviour.

**IRT numerical edge cases**: When ability approaches the boundary (`θ → ±3`) and difficulty is at the extreme, Fisher information approaches zero causing division instability. The `1e-6` floor guard was discovered empirically, not suggested by the AI.

**Windows CORS + file serving issue**: Browsers block requests from `file://` to `http://` on Windows. The fix — serving the frontend via `python -m http.server 3000` — was discovered through manual debugging. Using `127.0.0.1` instead of `localhost` was also required on Windows.
