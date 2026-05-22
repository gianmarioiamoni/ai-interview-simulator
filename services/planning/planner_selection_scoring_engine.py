# services/planning/planner_selection_scoring_engine.py

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.planning.semantic_cluster_suppressor import SemanticClusterSuppressor
from services.planning.semantic_novelty_bonus_engine import SemanticNoveltyBonusEngine
from services.planning.category_rarity_bonus_engine import CategoryRarityBonusEngine
from services.planning.contracts.planner_score_breakdown import PlannerScoreBreakdown
from services.planning.difficulty_spike_suppressor import DifficultySpikeSuppressor


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

        self._rarity_engine = CategoryRarityBonusEngine()

        self._difficulty_spike_suppressor = DifficultySpikeSuppressor()

    # =====================================================
    # PUBLIC
    # =====================================================

    def score(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
    ) -> PlannerScoreBreakdown:

        rationale: list[str] = []

        # -------------------------------------------------
        # DIFFICULTY SCORE
        # -------------------------------------------------

        difficulty_score = float(candidate.difficulty) * self._difficulty_weight

        rationale.append("difficulty_weighting")

        adjusted_score = difficulty_score

        # -------------------------------------------------
        # CLUSTER SUPPRESSION
        # -------------------------------------------------

        suppressed_score = self._cluster_suppressor.apply_penalty(
            candidate=candidate,
            selected_questions=(selected_questions),
            current_score=(adjusted_score),
        )

        cluster_penalty = round(
            suppressed_score - adjusted_score,
            4,
        )

        if cluster_penalty < 0:

            rationale.append("semantic_cluster_suppression")

        adjusted_score = suppressed_score

        # -------------------------------------------------
        # NOVELTY BONUS
        # -------------------------------------------------

        novelty_score = self._novelty_engine.apply_bonus(
            candidate=candidate,
            selected_questions=(selected_questions),
            current_score=(adjusted_score),
        )

        novelty_bonus = round(
            novelty_score - adjusted_score,
            4,
        )

        if novelty_bonus > 0:

            rationale.append("semantic_novelty_bonus")

        adjusted_score = novelty_score

        # -------------------------------------------------
        # CATEGORY RARITY BONUS
        # -------------------------------------------------

        rarity_score = self._rarity_engine.apply_bonus(
            candidate=candidate,
            selected_questions=selected_questions,
            current_score=adjusted_score,
        )

        category_rarity_bonus = round(
            rarity_score - adjusted_score,
            4,
        )

        if category_rarity_bonus > 0:

            rationale.append("category_rarity_bonus")

        adjusted_score = rarity_score

        # -------------------------------------------------
        # DIFFICULTY SPIKE PENALTY
        # -------------------------------------------------

        spike_score = self._difficulty_spike_suppressor.apply_penalty(
            candidate=candidate,
            selected_questions=selected_questions,
            current_score=adjusted_score,
        )

        difficulty_spike_penalty = round(
            spike_score - adjusted_score,
            4,
        )

        if difficulty_spike_penalty < 0:

            rationale.append("difficulty_spike_suppression")

        adjusted_score = spike_score

        # -------------------------------------------------
        # FINAL SCORE
        # -------------------------------------------------

        final_score = round(
            adjusted_score,
            4,
        )

        return PlannerScoreBreakdown(
            difficulty_score=round(
                difficulty_score,
                4,
            ),
            cluster_penalty=cluster_penalty,
            novelty_bonus=novelty_bonus,
            category_rarity_bonus=category_rarity_bonus,
            final_score=final_score,
            rationale=rationale,
            difficulty_spike_penalty=difficulty_spike_penalty,
        )
