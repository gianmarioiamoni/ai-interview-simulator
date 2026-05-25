# services/interview_planning/phases/constraint_fill_phase.py

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_planning.interview_constraints import InterviewConstraints

from services.interview_selection.selected_question import SelectedQuestion

from services.planning.planner_evaluation_factory import (
    PlannerEvaluationFactory,
)


class ConstraintFillPhase:

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

        selected_ids = {q.item.id for q in selected}

        remaining = sorted(
            [item for item in items if item.id not in selected_ids],
            key=lambda q: q.difficulty,
            reverse=True,
        )

        for item in remaining:

            area = item.area.value

            # -------------------------------------------------
            # EXCLUDED AREAS
            # -------------------------------------------------

            if area in constraints.excluded_areas:
                continue

            # -------------------------------------------------
            # AREA LIMIT
            # -------------------------------------------------

            if area_counts[area] >= constraints.max_questions_per_area:
                continue

            current_selected = [s.item for s in selected]

            evaluation = self._evaluation_factory.build(
                candidate=item,
                selected_questions=current_selected,
            )

            selected.append(
                SelectedQuestion(
                    item=item,
                    selection_score=evaluation.final_score,
                    selection_reason="constraint_fill",
                    score_breakdown=evaluation.breakdown,
                )
            )

            area_counts[area] += 1

            if len(selected) >= constraints.minimum_total_questions:
                break
