# services/planning/planner_evaluation_factory.py

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.planning.planner_selection_scoring_engine import (
    PlannerSelectionScoringEngine,
)

from services.planning.contracts.planner_candidate_evaluation import (
    PlannerCandidateEvaluation,
)


class PlannerEvaluationFactory:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._scoring_engine = PlannerSelectionScoringEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
    ) -> PlannerCandidateEvaluation:

        breakdown = self._scoring_engine.score(
            candidate=candidate,
            selected_questions=selected_questions,
        )

        return PlannerCandidateEvaluation(
            candidate=candidate,
            breakdown=breakdown,
            final_score=breakdown.final_score,
        )
