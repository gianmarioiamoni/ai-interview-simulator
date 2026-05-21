# services/planning/category_rarity_bonus_engine.py

from collections import Counter

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class CategoryRarityBonusEngine:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        rarity_bonus: float = 0.25,
    ) -> None:

        self._bonus = rarity_bonus

    # =====================================================
    # PUBLIC
    # =====================================================

    def apply_bonus(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
        current_score: float,
    ) -> float:

        if not selected_questions:
            return current_score

        category_counts = self._build_category_counts(selected_questions)

        candidate_category = candidate.area.value

        category_frequency = category_counts.get(
            candidate_category,
            0,
        )

        # -------------------------------------------------
        # BONUS FOR UNDERREPRESENTED
        # CATEGORIES
        # -------------------------------------------------

        if category_frequency == 0:

            boosted = current_score + self._bonus

            return round(
                boosted,
                4,
            )

        return current_score

    # =====================================================
    # INTERNALS
    # =====================================================

    def _build_category_counts(
        self,
        questions: list[QuestionBankItem],
    ) -> Counter:

        return Counter(question.area.value for question in questions)
