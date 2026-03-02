# app/ui/sample_data_loader.py

from typing import List

from domain.contracts.interview_type import InterviewType
from domain.contracts.question import Question


# =========================================================
# Public API
# =========================================================


def load_sample_questions(interview_type: InterviewType) -> List[Question]:
   
    # Temporary sample question loader.
    # NOTE: This is a UI-level bootstrap utility.
    # In production, question generation must be handled by the graph layer.

    if interview_type == InterviewType.TECHNICAL:
        return _load_technical_questions()

    if interview_type == InterviewType.HR:
        return _load_hr_questions()

    raise ValueError(f"Unsupported interview type: {interview_type}")


# =========================================================
# Technical Interview Questions
# =========================================================


def _load_technical_questions() -> List[Question]:

    return [
        Question(
            question_id="T1",
            text="Explain the difference between REST and GraphQL.",
        ),
        Question(
            question_id="T2",
            text="What is the difference between synchronous and asynchronous programming?",
        ),
        Question(
            question_id="T3",
            text="How would you design a scalable microservices architecture?",
        ),
    ]


# =========================================================
# HR Interview Questions
# =========================================================


def _load_hr_questions() -> List[Question]:

    return [
        Question(
            question_id="HR1",
            text="Tell me about a challenging situation you handled at work.",
        ),
        Question(
            question_id="HR2",
            text="How do you deal with conflict in a team?",
        ),
        Question(
            question_id="HR3",
            text="Where do you see yourself in five years?",
        ),
    ]
