# services/replanning/recovery_replanner.py

from copy import deepcopy

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.interview_planning.interview_constraints import InterviewConstraints
from services.interview_planning.constraint_based_planner import ConstraintBasedPlanner
from services.planning_validation.planning_validator import PlanningValidator
from services.planning_validation.recovery_action import RecoveryAction
from services.replanning.replanning_result import ReplanningResult
from services.replanning.recovery_candidate_expander import RecoveryCandidateExpander
from services.replanning.contracts.replanning_artifacts import ReplanningArtifacts


class RecoveryReplanner:

    MAX_ATTEMPTS = 3

    # =====================================================
    # PUBLIC
    # =====================================================

    def replan(
        self,
        items: list[QuestionBankItem],
        constraints: InterviewConstraints,
        role: RoleType,
        level: SeniorityLevel,
    ) -> ReplanningResult:

        planner = ConstraintBasedPlanner()

        validator = PlanningValidator()

        expander = RecoveryCandidateExpander()

        current_constraints = deepcopy(constraints)

        applied_actions: list[RecoveryAction] = []

        final_planning = None

        final_validation = None

        latest_expansion_telemetry = None

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1,
        ):

            planning_result = planner.plan(
                items=items,
                constraints=(current_constraints),
            )

            validation_result = validator.validate(
                result=planning_result,
                constraints=(current_constraints),
            )

            final_planning = planning_result

            final_validation = validation_result

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            if validation_result.is_valid:

                break

            # -------------------------------------------------
            # RECOVERY
            # -------------------------------------------------

            for action in validation_result.suggested_recovery_actions:

                if action in applied_actions:
                    continue

                # -------------------------------------------------
                # EXPAND CANDIDATES
                # -------------------------------------------------

                expansion_result = expander.expand(
                    items=items,
                    action=action,
                    role=role,
                    level=level,
                )

                items = expansion_result.expanded_items

                # real telemetry is not overwritten if recovery is not successful
                if (
                    expansion_result.telemetry is not None
                    and expansion_result.telemetry.recovery_successful
                ):

                    latest_expansion_telemetry = expansion_result.telemetry

                # -------------------------------------------------
                # APPLY RECOVERY ACTION
                # -------------------------------------------------

                self._apply_recovery_action(
                    constraints=(current_constraints),
                    action=action,
                )

                applied_actions.append(action)

                break

        # -------------------------------------------------
        # ARTIFACTS
        # -------------------------------------------------

        artifacts = ReplanningArtifacts(
            planner_telemetry=(final_planning.telemetry),
            retrieval_expansion_telemetry=(latest_expansion_telemetry),
            recovery_attempts=attempt,
            applied_actions=applied_actions,
        )

        return ReplanningResult(
            final_planning_result=final_planning,
            final_validation_result=(final_validation),
            applied_recovery_actions=(applied_actions),
            total_attempts=attempt,
            artifacts=artifacts,
        )

    # =====================================================
    # RECOVERY
    # =====================================================

    def _apply_recovery_action(
        self,
        constraints: InterviewConstraints,
        action: RecoveryAction,
    ) -> None:

        # -------------------------------------------------
        # RELAX DIFFICULTY
        # -------------------------------------------------

        if action == RecoveryAction.RELAX_DIFFICULTY:

            constraints.minimum_average_difficulty = max(
                1.0,
                constraints.minimum_average_difficulty - 1.0,
            )

        # -------------------------------------------------
        # REDUCE QUESTIONS
        # -------------------------------------------------

        elif action == RecoveryAction.REDUCE_REQUIRED_QUESTIONS:

            constraints.minimum_total_questions = max(
                1,
                constraints.minimum_total_questions - 1,
            )

        # -------------------------------------------------
        # RELAX AREA LIMITS
        # -------------------------------------------------

        elif action == RecoveryAction.RELAX_AREA_LIMITS:

            constraints.max_questions_per_area += 1
