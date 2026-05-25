# services/interview_planning/phases/planning_validation_phase.py

from services.interview_planning.interview_constraints import InterviewConstraints
from services.interview_selection.selected_question import SelectedQuestion


class PlanningValidationPhase:

    # =====================================================
    # PUBLIC
    # =====================================================

    def execute(
        self,
        selected_questions: list[SelectedQuestion],
        constraints: InterviewConstraints,
    ) -> tuple[list[str], list[str]]:

        satisfied: list[str] = []

        violated: list[str] = []

        # -------------------------------------------------
        # REQUIRED AREAS
        # -------------------------------------------------

        selected_areas = {q.item.area.value for q in selected_questions}

        for area in constraints.required_areas:

            if area in selected_areas:

                satisfied.append(f"required_area:{area}")

            else:

                violated.append(f"required_area:{area}")

        # -------------------------------------------------
        # MINIMUM DIFFICULTY
        # -------------------------------------------------

        average_difficulty = self._calculate_average_difficulty(
            selected_questions=selected_questions,
        )

        if average_difficulty >= constraints.minimum_average_difficulty:

            satisfied.append("minimum_average_difficulty")

        else:

            violated.append("minimum_average_difficulty")

        return (
            satisfied,
            violated,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _calculate_average_difficulty(
        self,
        selected_questions: list[SelectedQuestion],
    ) -> float:

        return sum(q.item.difficulty for q in selected_questions) / max(
            len(selected_questions),
            1,
        )
