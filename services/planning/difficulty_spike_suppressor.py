# services/planning/difficulty_spike_suppressor.py

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class DifficultySpikeSuppressor:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        max_allowed_jump: int = 2,
        spike_penalty: float = 0.4,
    ) -> None:

        self._max_allowed_jump = max_allowed_jump

        self._spike_penalty = spike_penalty

    # =====================================================
    # PUBLIC
    # =====================================================

    def apply_penalty(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
        current_score: float,
    ) -> float:

        if not selected_questions:

            return current_score

        previous = selected_questions[-1].difficulty

        current = candidate.difficulty

        jump = abs(current - previous)

        if jump <= self._max_allowed_jump:

            return current_score

        adjusted = current_score - self._spike_penalty

        return round(
            adjusted,
            4,
        )
