# app/domain/policies/navigation_policy.py

from typing import List

from domain.contracts.question import Question
from domain.contracts.question import QuestionDifficulty


class NavigationPolicy:
    @staticmethod
    def select_next_question_index(
        questions: List[Question],
        current_index: int,
    ) -> int:
        # Sequential baseline (safe default)
        next_index = current_index + 1

        if next_index >= len(questions):
            # Stay on last (or you could trigger "completed")
            return current_index

        return next_index

    @staticmethod
    def find_question_by_difficulty(
        questions: List[Question],
        target_difficulty: QuestionDifficulty,
        fallback_index: int,
    ) -> int:
        for i, q in enumerate(questions):
            if q.difficulty == target_difficulty:
                return i

        return fallback_index
