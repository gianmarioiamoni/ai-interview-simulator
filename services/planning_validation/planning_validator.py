# services/planning_validation/planning_validator.py

from services.interview_planning.interview_constraints import (
    InterviewConstraints,
)

from services.interview_planning.planning_result import (
    PlanningResult,
)

from services.planning_validation.validation_result import (
    ValidationResult,
)

from services.planning_validation.recovery_action import (
    RecoveryAction,
)


class PlanningValidator:

    # =====================================================
    # PUBLIC
    # =====================================================

    def validate(
        self,
        result: PlanningResult,
        constraints: InterviewConstraints,
    ) -> ValidationResult:

        violations = []

        recovery_actions = []

        # -------------------------------------------------
        # TOTAL QUESTIONS
        # -------------------------------------------------

        if len(result.selected_questions) < constraints.minimum_total_questions:

            violations.append("minimum_total_questions")

            recovery_actions.append(RecoveryAction.REDUCE_REQUIRED_QUESTIONS)

            recovery_actions.append(RecoveryAction.EXPAND_ROLE_SCOPE)

        # -------------------------------------------------
        # MIN DIFFICULTY
        # -------------------------------------------------

        if result.average_difficulty < constraints.minimum_average_difficulty:

            violations.append("minimum_average_difficulty")

            recovery_actions.append(RecoveryAction.RELAX_DIFFICULTY)

        # -------------------------------------------------
        # REQUIRED AREAS
        # -------------------------------------------------

        for area in constraints.required_areas:

            if f"required_area:{area}" not in result.satisfied_constraints:

                violations.append(f"required_area:{area}")

                recovery_actions.append(RecoveryAction.RELAX_AREA_LIMITS)

        return ValidationResult(
            is_valid=(len(violations) == 0),
            violated_constraints=(sorted(list(set(violations)))),
            suggested_recovery_actions=(
                sorted(
                    list(set(recovery_actions)),
                    key=lambda x: x.value,
                )
            ),
        )
