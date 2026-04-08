# tests/factories/question_factory.py

from domain.contracts.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview_area import InterviewArea


def build_question(
    *,
    qid: str = "q1",
    qtype: QuestionType = QuestionType.CODING,
) -> Question:
    return Question(
        id=qid,
        type=qtype,
        prompt="Write a function",
        area=InterviewArea.TECH_CODING,  
        difficulty=QuestionDifficulty.MEDIUM,
    )
