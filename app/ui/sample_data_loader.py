# app/ui/sample_data_loader.py

from typing import List

from domain.contracts.interview_type import InterviewType
from domain.contracts.question import Question, QuestionType
from domain.contracts.interview_area import InterviewArea


# =========================================================
# Public API
# =========================================================


def load_sample_questions(interview_type: InterviewType) -> List[Question]:
    
    # Temporary bootstrap question loader.
    # NOTE: In the final architecture, question generation must be delegated to the graph layer.

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
            id="T1",
            area=InterviewArea.TECH_BACKGROUND,
            type=QuestionType.WRITTEN,
            prompt="Describe your experience with backend architectures.",
            difficulty=2,
        ),
        Question(
            id="T2",
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            type=QuestionType.WRITTEN,
            prompt="Explain the difference between synchronous and asynchronous systems.",
            difficulty=2,
        ),
        Question(
            id="T3",
            area=InterviewArea.TECH_CASE_STUDY,
            type=QuestionType.WRITTEN,
            prompt="How would you design a scalable microservices architecture?",
            difficulty=3,
        ),
    ]


# =========================================================
# HR Interview Questions
# =========================================================


def _load_hr_questions() -> List[Question]:

    return [
        Question(
            id="HR1",
            area=InterviewArea.HR_BACKGROUND,
            type=QuestionType.WRITTEN,
            prompt="Tell me about your professional background.",
            difficulty=1,
        ),
        Question(
            id="HR2",
            area=InterviewArea.HR_SITUATIONAL,
            type=QuestionType.WRITTEN,
            prompt="Describe a challenging situation you handled at work.",
            difficulty=1,
        ),
        Question(
            id="HR3",
            area=InterviewArea.HR_ANALYTICAL,
            type=QuestionType.WRITTEN,
            prompt="How do you approach complex decision-making problems?",
            difficulty=1,
        ),
    ]
