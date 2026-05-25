# services/interview_planning/phases/fallback_completion_phase.py

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_planning.interview_constraints import InterviewConstraints
from services.interview_selection.selected_question import SelectedQuestion
from services.planning.contracts.planner_candidate_evaluation import PlannerCandidateEvaluation
from services.planning.planner_evaluation_factory import PlannerEvaluationFactory

from app.core.logger import get_logger

logger = get_logger(__name__)


class FallbackCompletionPhase:

    MINIMUM_CANDIDATE_SCORE = 0.0

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._evaluation_factory = PlannerEvaluationFactory()

    # =====================================================
    # PUBLIC
    # =====================================================

    def execute(
        self,
        selected: list[SelectedQuestion],
        available: list[QuestionBankItem],
        constraints: InterviewConstraints,
    ) -> list[SelectedQuestion]:

        # -------------------------------------------------
        # EARLY EXIT
        # -------------------------------------------------

        if len(selected) >= constraints.minimum_total_questions:

            return selected

        selected_ids = {item.item.id for item in selected}

        remaining = []

        for item in available:

            if item.id in selected_ids:
                continue

            remaining.append(item)

        # -------------------------------------------------
        # SORT BY SCORE
        # -------------------------------------------------

        logger.info("Evaluating fallback candidates...")

        current_selected = [s.item for s in selected]

        scored_remaining: list[PlannerCandidateEvaluation] = []

        for candidate in remaining:

            evaluation = self._evaluation_factory.build(
                candidate=candidate,
                selected_questions=current_selected,
            )

            scored_remaining.append(evaluation)

        scored_remaining.sort(
            key=lambda x: x.final_score,
            reverse=True,
        )

        # -------------------------------------------------
        # FILL
        # -------------------------------------------------

        for evaluation in scored_remaining:

            item = evaluation.candidate

            score = evaluation.final_score

            breakdown = evaluation.breakdown

            if len(selected) >= constraints.minimum_total_questions:
                break

            # -------------------------------------------------
            # QUALITY THRESHOLD
            # -------------------------------------------------

            if score < self.MINIMUM_CANDIDATE_SCORE:

                logger.info(f"Rejected low-quality candidate: " f"{item.text}")

                logger.info(f"Score: {score}")

                continue

            logger.info(f"Selected fallback candidate: " f"{item.text}")

            logger.info(f"Score: {score}")

            selected.append(
                SelectedQuestion(
                    item=item,
                    selection_score=score,
                    selection_reason="fallback_completion",
                    score_breakdown=breakdown,
                )
            )

        return selected
