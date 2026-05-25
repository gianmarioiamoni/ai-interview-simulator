# services/interview_planning/constraint_based_planner.py

from collections import defaultdict

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.interview_planning.interview_constraints import (
    InterviewConstraints,
)

from services.interview_planning.planning_result import (
    PlanningResult,
)

from services.interview_selection.selected_question import (
    SelectedQuestion,
)

from services.interview_planning.phases.required_area_selection_phase import (
    RequiredAreaSelectionPhase,
)

from services.interview_planning.phases.constraint_fill_phase import (
    ConstraintFillPhase,
)

from services.interview_planning.phases.fallback_completion_phase import (
    FallbackCompletionPhase,
)

from services.interview_planning.phases.planning_validation_phase import (
    PlanningValidationPhase,
)

from services.interview_planning.builders.planner_telemetry_builder import (
    PlannerTelemetryBuilder,
)


class ConstraintBasedPlanner:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._required_area_phase = RequiredAreaSelectionPhase()

        self._constraint_fill_phase = ConstraintFillPhase()

        self._fallback_completion_phase = FallbackCompletionPhase()

        self._validation_phase = PlanningValidationPhase()

        self._telemetry_builder = PlannerTelemetryBuilder()

    # =====================================================
    # PUBLIC
    # =====================================================

    def plan(
        self,
        items: list[QuestionBankItem],
        constraints: InterviewConstraints,
    ) -> PlanningResult:

        selected: list[SelectedQuestion] = []

        area_counts: dict[str, int] = defaultdict(int)

        # -------------------------------------------------
        # REQUIRED AREA SELECTION
        # -------------------------------------------------

        self._required_area_phase.execute(
            items=items,
            constraints=constraints,
            selected=selected,
            area_counts=area_counts,
        )

        # -------------------------------------------------
        # CONSTRAINT FILL
        # -------------------------------------------------

        self._constraint_fill_phase.execute(
            items=items,
            constraints=constraints,
            selected=selected,
            area_counts=area_counts,
        )

        # -------------------------------------------------
        # FALLBACK COMPLETION
        # -------------------------------------------------

        selected_questions = self._fallback_completion_phase.execute(
            selected=selected,
            available=items,
            constraints=constraints,
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        (
            satisfied,
            violated,
        ) = self._validation_phase.execute(
            selected_questions=selected_questions,
            constraints=constraints,
        )

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        average_difficulty = sum(q.item.difficulty for q in selected_questions) / max(
            len(selected_questions),
            1,
        )

        # -------------------------------------------------
        # TELEMETRY
        # -------------------------------------------------

        telemetry = self._telemetry_builder.build(
            selected_questions=selected_questions,
            total_candidates=len(items),
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        return PlanningResult(
            selected_questions=selected_questions,
            satisfied_constraints=satisfied,
            violated_constraints=violated,
            average_difficulty=round(
                average_difficulty,
                2,
            ),
            telemetry=telemetry,
        )
