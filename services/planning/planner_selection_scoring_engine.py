# services/planning/planner_selection_scoring_engine.py

from domain.contracts.question.question_bank_item import QuestionBankItem
from services.planning.semantic_cluster_suppressor import SemanticClusterSuppressor
from services.planning.semantic_novelty_bonus_engine import SemanticNoveltyBonusEngine


class PlannerSelectionScoringEngine:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        difficulty_weight: float = 1.0,
        semantic_penalty_weight: float = 1.0,
    ) -> None:

        self._difficulty_weight = difficulty_weight

        self._semantic_penalty_weight = semantic_penalty_weight

        self._cluster_suppressor = SemanticClusterSuppressor()

        self._novelty_engine = SemanticNoveltyBonusEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def score(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
    ) -> float:

        # -------------------------------------------------
        # BASE SCORE
        # -------------------------------------------------

        base_score = float(candidate.difficulty) * self._difficulty_weight

        # -------------------------------------------------
        # SEMANTIC BALANCING
        # -------------------------------------------------

        adjusted_score = self._cluster_suppressor.apply_penalty(
            candidate=candidate,
            selected_questions=(selected_questions),
            current_score=(base_score),
        )

        # -------------------------------------------------
        # NOVELTY BONUS
        # -------------------------------------------------

        adjusted_score = self._novelty_engine.apply_bonus(
            candidate=candidate,
            selected_questions=selected_questions,
            current_score=adjusted_score,
        )

        
        return round(
            adjusted_score,
            4,
        )
