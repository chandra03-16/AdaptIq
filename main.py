"""
Adaptive Diagnostic Engine — FastAPI Application
=================================================

Endpoints
---------
POST /sessions/start          → create a new test session
GET  /sessions/{id}           → get session status
GET  /sessions/{id}/next      → get the next adaptive question
POST /sessions/{id}/answer    → submit an answer and update ability score
GET  /healthz                 → liveness probe
"""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from database import connect_db, close_db, get_questions_col, get_sessions_col
from models import (
    StartSessionRequest,
    StartSessionResponse,
    NextQuestionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SessionStatusResponse,
    ResponseRecord,
)
from adaptive_engine import select_next_question, compute_ability_update
from ai_insights import generate_study_plan
from seed_data import seed as run_seed


MAX_QUESTIONS = int(os.getenv("MAX_QUESTIONS", "10"))
INITIAL_ABILITY = float(os.getenv("INITIAL_ABILITY", "0.5"))   # display scale


# ── App lifecycle ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await run_seed()          # idempotent — skips if data already present
    yield
    await close_db()


app = FastAPI(
    title="Adaptive Diagnostic Engine",
    version="1.0.0",
    description="1PL IRT-based adaptive GRE test with AI study plans.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper: fetch session or 404 ──────────────────────────────────────────────

async def _get_session(session_id: str) -> dict:
    doc = await get_sessions_col().find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return doc


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/healthz", tags=["Health"])
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post(
    "/sessions/start",
    response_model=StartSessionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sessions"],
    summary="Start a new test session",
)
async def start_session(body: StartSessionRequest):
    """Create a new UserSession with baseline ability = 0.5."""
    session_id = str(uuid.uuid4())
    doc = {
        "session_id": session_id,
        "student_name": body.student_name.strip(),
        "ability_score": INITIAL_ABILITY,
        "questions_answered": 0,
        "responses": [],
        "is_complete": False,
        "started_at": datetime.utcnow(),
        "study_plan": None,
    }
    await get_sessions_col().insert_one(doc)
    return StartSessionResponse(
        session_id=session_id,
        message=f"Session created for {body.student_name}. Good luck!",
    )


@app.get(
    "/sessions/{session_id}",
    response_model=SessionStatusResponse,
    tags=["Sessions"],
    summary="Get current session status",
)
async def get_session(session_id: str):
    doc = await _get_session(session_id)
    return SessionStatusResponse(
        session_id=doc["session_id"],
        student_name=doc["student_name"],
        ability_score=doc["ability_score"],
        questions_answered=doc["questions_answered"],
        responses=[ResponseRecord(**r) for r in doc.get("responses", [])],
        is_complete=doc["is_complete"],
        study_plan=doc.get("study_plan"),
    )


@app.get(
    "/sessions/{session_id}/next",
    response_model=NextQuestionResponse,
    tags=["Questions"],
    summary="Get the next adaptive question",
)
async def next_question(session_id: str):
    """
    Select the unseen question whose difficulty is closest to the student's
    current IRT ability estimate (maximum information selection).
    """
    session = await _get_session(session_id)

    if session["is_complete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already complete.",
        )

    all_questions: List[dict] = await get_questions_col().find({}).to_list(length=None)
    seen_ids = [r["question_id"] for r in session.get("responses", [])]

    question = select_next_question(
        all_questions=all_questions,
        seen_ids=seen_ids,
        current_ability_display=session["ability_score"],
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No more questions available in the pool.",
        )

    return NextQuestionResponse(
        question_id=question["question_id"],
        text=question["text"],
        options=question["options"],
        topic=question["topic"],
        difficulty=question["difficulty"],
        question_number=session["questions_answered"] + 1,
    )


@app.post(
    "/sessions/{session_id}/answer",
    response_model=SubmitAnswerResponse,
    tags=["Questions"],
    summary="Submit an answer and update ability score",
)
async def submit_answer(session_id: str, body: SubmitAnswerRequest):
    """
    1. Look up the correct answer.
    2. Update ability via 1PL IRT Newton–Raphson step.
    3. Append the response record.
    4. If MAX_QUESTIONS reached → mark complete & generate AI study plan.
    """
    if body.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id in URL and body do not match.",
        )

    session = await _get_session(session_id)

    if session["is_complete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already complete.",
        )

    # Fetch the question
    question = await get_questions_col().find_one({"question_id": body.question_id})
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{body.question_id}' not found.",
        )

    # Guard against re-answering the same question
    answered_ids = [r["question_id"] for r in session.get("responses", [])]
    if body.question_id in answered_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This question has already been answered in this session.",
        )

    is_correct = body.selected_answer.upper() == question["correct_answer"].upper()

    # IRT ability update
    new_ability = compute_ability_update(
        current_ability_display=session["ability_score"],
        question_difficulty=question["difficulty"],
        is_correct=is_correct,
    )

    # Build response record
    record = {
        "question_id": body.question_id,
        "topic": question["topic"],
        "difficulty": question["difficulty"],
        "is_correct": is_correct,
        "ability_after": new_ability,
    }

    questions_answered = session["questions_answered"] + 1
    is_complete = questions_answered >= MAX_QUESTIONS

    update_fields: dict = {
        "ability_score": new_ability,
        "questions_answered": questions_answered,
        "is_complete": is_complete,
    }

    study_plan: str | None = None

    if is_complete:
        # Generate personalised AI study plan
        all_responses = session.get("responses", []) + [record]
        response_objs = [ResponseRecord(**r) for r in all_responses]
        try:
            study_plan = generate_study_plan(
                student_name=session["student_name"],
                final_ability=new_ability,
                responses=response_objs,
            )
        except Exception as exc:
            study_plan = f"(Study plan generation failed: {exc})"
        update_fields["study_plan"] = study_plan

    await get_sessions_col().update_one(
        {"session_id": session_id},
        {
            "$set": update_fields,
            "$push": {"responses": record},
        },
    )

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=question["correct_answer"],
        ability_score=new_ability,
        questions_answered=questions_answered,
        is_complete=is_complete,
        study_plan=study_plan,
    )
