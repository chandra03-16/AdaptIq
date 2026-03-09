"""
Pydantic models for request/response validation and MongoDB documents.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────
# Question document (stored in MongoDB)
# ─────────────────────────────────────────────

class Question(BaseModel):
    question_id: str
    text: str
    options: dict[str, str]          # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer: str              # "A" | "B" | "C" | "D"
    difficulty: float = Field(..., ge=0.1, le=1.0)
    topic: str                       # e.g. "Algebra", "Vocabulary"
    tags: List[str]


# ─────────────────────────────────────────────
# UserSession document (stored in MongoDB)
# ─────────────────────────────────────────────

class ResponseRecord(BaseModel):
    question_id: str
    topic: str
    difficulty: float
    is_correct: bool
    ability_after: float             # ability score after IRT update


class UserSession(BaseModel):
    session_id: str
    student_name: str
    ability_score: float = 0.0       # IRT theta (logit scale, maps to 0-1 for UI)
    questions_answered: int = 0
    responses: List[ResponseRecord] = []
    is_complete: bool = False
    started_at: datetime = Field(default_factory=datetime.utcnow)
    study_plan: Optional[str] = None


# ─────────────────────────────────────────────
# API request/response schemas
# ─────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    student_name: str


class StartSessionResponse(BaseModel):
    session_id: str
    message: str


class NextQuestionResponse(BaseModel):
    question_id: str
    text: str
    options: dict[str, str]
    topic: str
    difficulty: float
    question_number: int             # 1-based counter for UI


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    selected_answer: str             # "A" | "B" | "C" | "D"


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    ability_score: float             # updated ability (0-1 for display)
    questions_answered: int
    is_complete: bool
    study_plan: Optional[str] = None  # populated when is_complete=True


class SessionStatusResponse(BaseModel):
    session_id: str
    student_name: str
    ability_score: float
    questions_answered: int
    responses: List[ResponseRecord]
    is_complete: bool
    study_plan: Optional[str] = None
