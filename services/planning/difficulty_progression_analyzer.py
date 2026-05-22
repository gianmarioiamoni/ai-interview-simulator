# services/planning/difficulty_progression_analyzer.py

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class DifficultyProgressionAnalyzer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def calculate_progression_score(
        self,
        questions: list[QuestionBankItem],
    ) -> float:

        if len(questions) < 2:
            return 1.0

        ordered_pairs = 0

        for idx in range(len(questions) - 1):

            current = questions[idx].difficulty

            next_question = questions[idx + 1].difficulty

            if current <= next_question:

                ordered_pairs += 1

        return round(
            ordered_pairs / (len(questions) - 1),
            4,
        )
