"""
Seed script — populates MongoDB with 25 GRE-style questions.

Run once:  python seed_data.py
"""

import asyncio
from database import connect_db, close_db, get_questions_col

QUESTIONS = [
    # ── Algebra (5 questions) ────────────────────────────────────────────────
    {
        "question_id": "ALG001",
        "text": "If 3x - 7 = 14, what is the value of x?",
        "options": {"A": "5", "B": "7", "C": "9", "D": "11"},
        "correct_answer": "B",
        "difficulty": 0.2,
        "topic": "Algebra",
        "tags": ["linear equations", "solving for x"],
    },
    {
        "question_id": "ALG002",
        "text": "Which of the following is a solution to x² - 5x + 6 = 0?",
        "options": {"A": "1", "B": "2", "C": "4", "D": "5"},
        "correct_answer": "B",
        "difficulty": 0.4,
        "topic": "Algebra",
        "tags": ["quadratic equations", "factoring"],
    },
    {
        "question_id": "ALG003",
        "text": "If f(x) = 2x² + 3x - 5, what is f(-2)?",
        "options": {"A": "-7", "B": "-3", "C": "1", "D": "9"},
        "correct_answer": "A",
        "difficulty": 0.5,
        "topic": "Algebra",
        "tags": ["functions", "substitution"],
    },
    {
        "question_id": "ALG004",
        "text": (
            "For all real numbers x, (x + 3)² - (x - 3)² = ?"
        ),
        "options": {"A": "0", "B": "12x", "C": "18", "D": "2x² + 18"},
        "correct_answer": "B",
        "difficulty": 0.65,
        "topic": "Algebra",
        "tags": ["algebraic identities", "difference of squares"],
    },
    {
        "question_id": "ALG005",
        "text": (
            "If log₂(x) = 5, what is the value of log₂(x³)?"
        ),
        "options": {"A": "8", "B": "10", "C": "15", "D": "25"},
        "correct_answer": "C",
        "difficulty": 0.8,
        "topic": "Algebra",
        "tags": ["logarithms", "exponent rules"],
    },
    # ── Geometry (5 questions) ───────────────────────────────────────────────
    {
        "question_id": "GEO001",
        "text": "What is the area of a rectangle with length 8 and width 5?",
        "options": {"A": "13", "B": "26", "C": "40", "D": "80"},
        "correct_answer": "C",
        "difficulty": 0.15,
        "topic": "Geometry",
        "tags": ["area", "rectangles"],
    },
    {
        "question_id": "GEO002",
        "text": (
            "In a right triangle, if one leg is 6 and the hypotenuse is 10, "
            "what is the length of the other leg?"
        ),
        "options": {"A": "4", "B": "6", "C": "8", "D": "12"},
        "correct_answer": "C",
        "difficulty": 0.35,
        "topic": "Geometry",
        "tags": ["Pythagorean theorem", "right triangles"],
    },
    {
        "question_id": "GEO003",
        "text": (
            "A circle has a circumference of 16π. What is its area?"
        ),
        "options": {"A": "16π", "B": "32π", "C": "64π", "D": "128π"},
        "correct_answer": "C",
        "difficulty": 0.5,
        "topic": "Geometry",
        "tags": ["circles", "circumference", "area"],
    },
    {
        "question_id": "GEO004",
        "text": (
            "Two parallel lines are cut by a transversal. If one interior angle "
            "is 65°, what is the measure of its co-interior (same-side) angle?"
        ),
        "options": {"A": "65°", "B": "115°", "C": "125°", "D": "180°"},
        "correct_answer": "B",
        "difficulty": 0.6,
        "topic": "Geometry",
        "tags": ["parallel lines", "transversals", "angles"],
    },
    {
        "question_id": "GEO005",
        "text": (
            "A cone has height 9 and base radius 4. What is its volume? "
            "(V = ⅓πr²h)"
        ),
        "options": {"A": "12π", "B": "36π", "C": "48π", "D": "144π"},
        "correct_answer": "C",
        "difficulty": 0.75,
        "topic": "Geometry",
        "tags": ["volume", "cones", "3D geometry"],
    },
    # ── Vocabulary (5 questions) ─────────────────────────────────────────────
    {
        "question_id": "VOC001",
        "text": "Choose the word most similar in meaning to BENEVOLENT.",
        "options": {
            "A": "Malicious",
            "B": "Indifferent",
            "C": "Kind-hearted",
            "D": "Cautious",
        },
        "correct_answer": "C",
        "difficulty": 0.2,
        "topic": "Vocabulary",
        "tags": ["synonyms", "adjectives"],
    },
    {
        "question_id": "VOC002",
        "text": "Choose the word most nearly OPPOSITE in meaning to LOQUACIOUS.",
        "options": {
            "A": "Verbose",
            "B": "Taciturn",
            "C": "Eloquent",
            "D": "Garrulous",
        },
        "correct_answer": "B",
        "difficulty": 0.45,
        "topic": "Vocabulary",
        "tags": ["antonyms", "adjectives"],
    },
    {
        "question_id": "VOC003",
        "text": (
            "The senator's speech was marked by ________ rhetoric — "
            "passionate and stirring, but ultimately lacking substance."
        ),
        "options": {
            "A": "laconic",
            "B": "turgid",
            "C": "pellucid",
            "D": "bombastic",
        },
        "correct_answer": "D",
        "difficulty": 0.6,
        "topic": "Vocabulary",
        "tags": ["sentence completion", "rhetoric"],
    },
    {
        "question_id": "VOC004",
        "text": (
            "SYCOPHANT : FLATTER :: ICONOCLAST : ?"
        ),
        "options": {
            "A": "worship",
            "B": "challenge",
            "C": "conceal",
            "D": "preserve",
        },
        "correct_answer": "B",
        "difficulty": 0.72,
        "topic": "Vocabulary",
        "tags": ["analogies", "word relationships"],
    },
    {
        "question_id": "VOC005",
        "text": (
            "The philosopher's argument was said to be ________: "
            "it appeared irrefutable to those who accepted its premises, "
            "yet rested on an equivocation."
        ),
        "options": {
            "A": "specious",
            "B": "cogent",
            "C": "pellucid",
            "D": "diffident",
        },
        "correct_answer": "A",
        "difficulty": 0.88,
        "topic": "Vocabulary",
        "tags": ["sentence completion", "critical reasoning"],
    },
    # ── Data Analysis (5 questions) ──────────────────────────────────────────
    {
        "question_id": "DAT001",
        "text": (
            "The ages of five students are: 18, 20, 22, 24, 26. "
            "What is the mean age?"
        ),
        "options": {"A": "20", "B": "21", "C": "22", "D": "23"},
        "correct_answer": "C",
        "difficulty": 0.15,
        "topic": "Data Analysis",
        "tags": ["mean", "descriptive statistics"],
    },
    {
        "question_id": "DAT002",
        "text": (
            "A bag contains 4 red, 3 blue, and 3 green balls. "
            "What is the probability of picking a blue ball at random?"
        ),
        "options": {"A": "1/10", "B": "3/10", "C": "3/7", "D": "1/3"},
        "correct_answer": "B",
        "difficulty": 0.3,
        "topic": "Data Analysis",
        "tags": ["probability", "basic"],
    },
    {
        "question_id": "DAT003",
        "text": (
            "Data set: {2, 4, 4, 4, 5, 5, 7, 9}. "
            "What is the standard deviation? (nearest whole number)"
        ),
        "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
        "correct_answer": "B",
        "difficulty": 0.55,
        "topic": "Data Analysis",
        "tags": ["standard deviation", "statistics"],
    },
    {
        "question_id": "DAT004",
        "text": (
            "In a normal distribution, approximately what percentage of values "
            "lie within one standard deviation of the mean?"
        ),
        "options": {"A": "50%", "B": "68%", "C": "75%", "D": "95%"},
        "correct_answer": "B",
        "difficulty": 0.65,
        "topic": "Data Analysis",
        "tags": ["normal distribution", "empirical rule"],
    },
    {
        "question_id": "DAT005",
        "text": (
            "A study finds r = 0.87 between hours studied and test score. "
            "Which statement best describes this relationship?"
        ),
        "options": {
            "A": "Weak positive correlation",
            "B": "Moderate negative correlation",
            "C": "Strong positive correlation",
            "D": "Perfect positive correlation",
        },
        "correct_answer": "C",
        "difficulty": 0.4,
        "topic": "Data Analysis",
        "tags": ["correlation", "interpretation"],
    },
    # ── Critical Reasoning (5 questions) ────────────────────────────────────
    {
        "question_id": "CRT001",
        "text": (
            "All mammals are warm-blooded. Whales are mammals. "
            "Therefore, whales are __________."
        ),
        "options": {
            "A": "fish",
            "B": "cold-blooded",
            "C": "warm-blooded",
            "D": "amphibians",
        },
        "correct_answer": "C",
        "difficulty": 0.1,
        "topic": "Critical Reasoning",
        "tags": ["deductive reasoning", "syllogism"],
    },
    {
        "question_id": "CRT002",
        "text": (
            "Politician: 'Crime rates fell after we increased police funding. "
            "Therefore, increased funding caused the drop.' "
            "Which flaw is present in this argument?"
        ),
        "options": {
            "A": "Ad hominem",
            "B": "False dichotomy",
            "C": "Post hoc ergo propter hoc",
            "D": "Appeal to authority",
        },
        "correct_answer": "C",
        "difficulty": 0.5,
        "topic": "Critical Reasoning",
        "tags": ["logical fallacies", "causation vs correlation"],
    },
    {
        "question_id": "CRT003",
        "text": (
            "A researcher finds that cities with more hospitals have higher death "
            "rates. She concludes hospitals cause death. "
            "What is the most likely explanation she overlooked?"
        ),
        "options": {
            "A": "Hospitals attract sick people who would die anyway",
            "B": "Death rates are always higher in cities",
            "C": "Researchers are biased against hospitals",
            "D": "The sample size was too small",
        },
        "correct_answer": "A",
        "difficulty": 0.6,
        "topic": "Critical Reasoning",
        "tags": ["confounding variables", "data interpretation"],
    },
    {
        "question_id": "CRT004",
        "text": (
            "Premise 1: No reptile is warm-blooded. "
            "Premise 2: All snakes are reptiles. "
            "Premise 3: Some warm-blooded animals lay eggs. "
            "Which conclusion MUST be true?"
        ),
        "options": {
            "A": "Some egg-laying animals are snakes",
            "B": "No snake is warm-blooded",
            "C": "All egg-layers are reptiles",
            "D": "Some reptiles lay eggs",
        },
        "correct_answer": "B",
        "difficulty": 0.7,
        "topic": "Critical Reasoning",
        "tags": ["syllogism", "logical deduction"],
    },
    {
        "question_id": "CRT005",
        "text": (
            "A study of 500 self-selected online survey respondents finds that "
            "80% prefer Brand X. The company claims: 'Most people prefer Brand X.' "
            "What is the most serious weakness of this claim?"
        ),
        "options": {
            "A": "The sample size is too small",
            "B": "Self-selection bias makes the sample unrepresentative",
            "C": "Online surveys are always inaccurate",
            "D": "80% is not a majority",
        },
        "correct_answer": "B",
        "difficulty": 0.82,
        "topic": "Critical Reasoning",
        "tags": ["sampling bias", "research methodology"],
    },
]


async def seed():
    await connect_db()
    col = get_questions_col()

    existing = await col.count_documents({})
    if existing >= len(QUESTIONS):
        print(f"[Seed] {existing} questions already in DB — skipping.")
        await close_db()
        return

    # Upsert by question_id so re-runs are idempotent
    for q in QUESTIONS:
        await col.update_one(
            {"question_id": q["question_id"]},
            {"$set": q},
            upsert=True,
        )

    total = await col.count_documents({})
    print(f"[Seed] Done — {total} questions in the collection.")
    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
