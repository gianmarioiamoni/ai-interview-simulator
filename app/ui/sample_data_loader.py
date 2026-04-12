# app/ui/sample_data_loader.py

from typing import List

from domain.contracts.interview.interview_typeimport InterviewType
from domain.contracts.question.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
)
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.coding_spec import CodingSpec  # ✅ NEW


def load_sample_questions(interview_type: InterviewType) -> List[Question]:

    if interview_type == InterviewType.TECHNICAL:
        return _load_technical_questions()

    if interview_type == InterviewType.HR:
        return _load_hr_questions()

    raise ValueError(f"Unsupported interview type: {interview_type}")


# =========================================================
# Technical
# =========================================================


def _load_technical_questions() -> List[Question]:

    return [
        Question(
            id="T1",
            area=InterviewArea.TECH_BACKGROUND,
            type=QuestionType.WRITTEN,
            prompt="Describe your experience designing distributed backend systems.",
            difficulty=QuestionDifficulty.MEDIUM,
        ),
        Question(
            id="T2",
            area=InterviewArea.TECH_CODING,
            type=QuestionType.CODING,
            prompt=(
                "Write a Python function that returns the first non-repeating "
                "character in a string. If none exists, return None."
            ),
            difficulty=QuestionDifficulty.HARD,
            # =====================================================
            # ✅ CODING SPEC (NEW - REQUIRED)
            # =====================================================
            coding_spec=CodingSpec(
                type="function",
                entrypoint="first_non_repeating_char",
                parameters=["s"],
            ),
            # =====================================================
            # TESTS
            # =====================================================
            visible_tests=[
                CodingTestCase(args=["leetcode"], expected="l"),
                CodingTestCase(args=["aabbcc"], expected=None),
            ],
            # =====================================================
            # REFERENCE SOLUTION
            # =====================================================
            reference_solution=(
                "def first_non_repeating_char(s: str):\n"
                "    from collections import Counter\n"
                "    counts = Counter(s)\n"
                "    for char in s:\n"
                "        if counts[char] == 1:\n"
                "            return char\n"
                "    return None"
            ),
        ),
        Question(
            id="T3",
            area=InterviewArea.TECH_DATABASE,
            type=QuestionType.DATABASE,
            prompt=(
                "Given a table Users(id, name, created_at), "
                "write a SQL query to retrieve the 5 most recently created users."
            ),
            difficulty=QuestionDifficulty.MEDIUM,
            db_schema="""
    CREATE TABLE Users(
        id INTEGER PRIMARY KEY,
        name TEXT,
        created_at TEXT
    );
    """,
            db_seed_data="""
    INSERT INTO Users(name, created_at) VALUES
    ('Alice','2024-01-01'),
    ('Bob','2024-02-01'),
    ('Carol','2024-03-01'),
    ('Dave','2024-04-01'),
    ('Eve','2024-05-01'),
    ('Frank','2024-06-01');
    """,
            reference_solution="""
    SELECT *
    FROM Users
    ORDER BY created_at DESC
    LIMIT 5
    """,
            expected_ordered=True,
        ),
    ]


# =========================================================
# HR
# =========================================================


def _load_hr_questions() -> List[Question]:

    return [
        Question(
            id="HR1",
            area=InterviewArea.HR_BACKGROUND,
            type=QuestionType.WRITTEN,
            prompt="Tell me about your professional background.",
            difficulty=QuestionDifficulty.EASY,
        ),
        Question(
            id="HR2",
            area=InterviewArea.HR_SITUATIONAL,
            type=QuestionType.WRITTEN,
            prompt="Describe a challenging situation you handled at work.",
            difficulty=QuestionDifficulty.EASY,
        ),
        Question(
            id="HR3",
            area=InterviewArea.HR_ANALYTICAL,
            type=QuestionType.WRITTEN,
            prompt="How do you approach complex decision-making problems?",
            difficulty=QuestionDifficulty.EASY,
        ),
    ]
