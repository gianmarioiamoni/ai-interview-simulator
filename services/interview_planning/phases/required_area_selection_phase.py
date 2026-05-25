# services/interview_planning/phases/required_area_selection_phase.py

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_planning.interview_constraints import InterviewConstraints
from services.interview_selection.selected_question import SelectedQuestion
from services.planning.contracts.planner_candidate_evaluation import (
    PlannerCandidateEvaluation,
)
from services.planning.planner_evaluation_factory import PlannerEvaluationFactory


class RequiredAreaSelectionPhase:

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
        items: list[QuestionBankItem],
        constraints: InterviewConstraints,
        selected: list[SelectedQuestion],
        area_counts: dict[str, int],
    ) -> None:

        for area in constraints.required_areas:

            candidates = [item for item in items if item.area.value == area]

            if not candidates:
                continue

            best_evaluation: PlannerCandidateEvaluation | None = None

            current_selected = [s.item for s in selected]

            for candidate in candidates:

                evaluation = self._evaluation_factory.build(
                    candidate=candidate,
                    selected_questions=current_selected,
                )

                if (
                    best_evaluation is None
                    or evaluation.final_score > best_evaluation.final_score
                ):
                    best_evaluation = evaluation

            if best_evaluation is None:
                continue

            selected.append(
                SelectedQuestion(
                    item=best_evaluation.candidate,
                    selection_score=best_evaluation.final_score,
                    selection_reason="required_area_selection",
                    score_breakdown=best_evaluation.breakdown,
                )
            )

            area_counts[area] += 1
