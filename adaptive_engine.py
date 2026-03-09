"""
Adaptive Engine — 1-Parameter Logistic IRT (1PL Rasch Model).

Core maths
----------
The 1PL model gives the probability that a student with ability θ answers a
question with difficulty b correctly:

    P(correct | θ, b) = 1 / (1 + exp(-(θ - b)))

After each response we update θ via Maximum Likelihood Estimation (MLE) using
a single Newton–Raphson step:

    θ_new = θ_old + (r - P) / (P * (1 - P))

where r = 1 if correct, 0 if incorrect.

Ability is stored on the logit scale (roughly -4 to +4) internally but mapped
to a 0–1 range for display.  Difficulty values in the DB are also stored on
the same logit-like scale (0.1–1.0 maps to roughly -2 to +2 logits internally).

Question selection
------------------
We pick the next question from the pool such that its difficulty is *closest*
to the student's current ability (maximum information point of the 1PL model)
and the question has not already been seen in this session.
"""

import math
from typing import List, Optional

# ── Internal logit helpers ────────────────────────────────────────────────────

# DB stores difficulty in [0.1, 1.0].  We map this to logits in [-2, 2] for
# the IRT computation so the maths behaves properly.

_D_MIN, _D_MAX = 0.1, 1.0
_THETA_MIN, _THETA_MAX = -2.0, 2.0


def difficulty_to_logit(d: float) -> float:
    """Map DB difficulty [0.1, 1.0] → logit [-2, 2]."""
    normalised = (d - _D_MIN) / (_D_MAX - _D_MIN)   # 0–1
    return _THETA_MIN + normalised * (_THETA_MAX - _THETA_MIN)


def logit_to_display(theta: float) -> float:
    """Map internal logit [-2, 2] → display ability [0.0, 1.0]."""
    return round((theta - _THETA_MIN) / (_THETA_MAX - _THETA_MIN), 4)


def display_to_logit(display: float) -> float:
    """Map display ability [0.0, 1.0] → internal logit [-2, 2]."""
    return _THETA_MIN + display * (_THETA_MAX - _THETA_MIN)


# ── IRT core ─────────────────────────────────────────────────────────────────

def irt_probability(theta: float, b: float) -> float:
    """P(correct | theta, b) under 1PL model.  Clamped for numerical safety."""
    try:
        return 1.0 / (1.0 + math.exp(-(theta - b)))
    except OverflowError:
        return 0.0 if (theta - b) < 0 else 1.0


def update_ability(theta: float, b: float, is_correct: bool) -> float:
    """
    Single Newton–Raphson step for MLE ability update.

    Returns updated theta (clamped to [-3, 3] to prevent runaway estimates
    in early items when data is sparse).
    """
    p = irt_probability(theta, b)
    r = 1.0 if is_correct else 0.0

    # Guard against p ≈ 0 or p ≈ 1 (information = 0 → division by zero)
    information = p * (1.0 - p)
    if information < 1e-6:
        information = 1e-6

    theta_new = theta + (r - p) / information

    # Clamp to avoid extreme values with only a few items
    return max(-3.0, min(3.0, theta_new))


# ── Question selection ────────────────────────────────────────────────────────

def select_next_question(
    all_questions: List[dict],
    seen_ids: List[str],
    current_ability_display: float,
) -> Optional[dict]:
    """
    Return the unseen question whose difficulty is closest to the student's
    current ability (maximum Fisher information point).
    """
    theta = display_to_logit(current_ability_display)
    unseen = [q for q in all_questions if q["question_id"] not in seen_ids]

    if not unseen:
        return None

    def info_distance(q: dict) -> float:
        b = difficulty_to_logit(q["difficulty"])
        return abs(theta - b)   # 0 = maximum information

    return min(unseen, key=info_distance)


# ── Public entry points ───────────────────────────────────────────────────────

def compute_ability_update(
    current_ability_display: float,
    question_difficulty: float,
    is_correct: bool,
) -> float:
    """
    Given:
      - current_ability_display  [0, 1]
      - question_difficulty      [0.1, 1.0] from DB
      - is_correct               bool

    Returns updated ability in [0, 1] display scale.
    """
    theta = display_to_logit(current_ability_display)
    b = difficulty_to_logit(question_difficulty)
    theta_new = update_ability(theta, b, is_correct)
    return logit_to_display(theta_new)
