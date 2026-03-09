"""
AI Insights — generates a personalised 3-step study plan via Google Gemini.

Sends the student's full performance summary (topics, difficulty reached,
accuracy per topic) and asks for a structured, actionable study plan.
"""

import os
from typing import List
import google.generativeai as genai
from models import ResponseRecord


def _build_performance_summary(
    student_name: str,
    final_ability: float,
    responses: List[ResponseRecord],
) -> str:
    """Compose a plain-English performance summary from session data."""
    total = len(responses)
    correct = sum(1 for r in responses if r.is_correct)
    accuracy = round(correct / total * 100, 1) if total else 0

    topic_stats: dict[str, dict] = {}
    for r in responses:
        t = r.topic
        if t not in topic_stats:
            topic_stats[t] = {"correct": 0, "total": 0, "max_difficulty": 0.0}
        topic_stats[t]["total"] += 1
        if r.is_correct:
            topic_stats[t]["correct"] += 1
        topic_stats[t]["max_difficulty"] = max(
            topic_stats[t]["max_difficulty"], r.difficulty
        )

    topic_lines = []
    for topic, stats in topic_stats.items():
        pct = round(stats["correct"] / stats["total"] * 100)
        topic_lines.append(
            f"  • {topic}: {pct}% correct "
            f"(max difficulty attempted: {stats['max_difficulty']:.2f})"
        )

    topic_block = "\n".join(topic_lines) if topic_lines else "  (no topic data)"
    ability_pct = round(final_ability * 100, 1)

    return (
        f"Student: {student_name}\n"
        f"Overall accuracy: {accuracy}% ({correct}/{total} correct)\n"
        f"Final ability estimate: {ability_pct}/100\n\n"
        f"Per-topic breakdown:\n{topic_block}"
    )


def generate_study_plan(
    student_name: str,
    final_ability: float,
    responses: List[ResponseRecord],
) -> str:
    """
    Call Gemini to generate a personalised 3-step study plan.
    Returns the plan as a markdown-formatted string.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    summary = _build_performance_summary(student_name, final_ability, responses)

    prompt = f"""You are an expert GRE tutor. A student just completed an adaptive diagnostic test.
Here is their performance summary:

{summary}

Based on this data, create a **personalised 3-step study plan** that:
1. Addresses their weakest topics first.
2. Suggests specific, actionable study activities (not vague advice).
3. Includes a recommended practice difficulty progression.

Format your response as:
## Step 1 — [Title]
[2-3 sentences of specific advice]

## Step 2 — [Title]
[2-3 sentences of specific advice]

## Step 3 — [Title]
[2-3 sentences of specific advice]

## Encouragement
[One motivating sentence personalised to {student_name}'s result.]

Be concise, specific, and encouraging."""

    response = model.generate_content(prompt)
    return response.text
