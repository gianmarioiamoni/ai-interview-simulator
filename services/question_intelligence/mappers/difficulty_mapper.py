# services/question_intelligence/mappers/difficulty_mapper.py

from domain.contracts.question.question import QuestionDifficulty


def map_corpus_difficulty(value: int | None) -> QuestionDifficulty:
    """Map corpus difficulty integer (1-5) to QuestionDifficulty enum.

    <=2 → EASY, 3 → MEDIUM, >=4 → HARD, None → MEDIUM (fallback).
    """
    if value is None:
        return QuestionDifficulty.MEDIUM
    if value <= 2:
        return QuestionDifficulty.EASY
    if value == 3:
        return QuestionDifficulty.MEDIUM
    return QuestionDifficulty.HARD
