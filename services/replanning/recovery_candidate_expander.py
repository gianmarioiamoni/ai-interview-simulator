# services/replanning/recovery_candidate_expander.py

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.interview_planning.interview_constraints import InterviewConstraints
from services.planning_validation.recovery_action import RecoveryAction
from services.replanning.contracts.recovery_expansion_result import RecoveryExpansionResult
from services.replanning.retrieval_recovery_service import RetrievalRecoveryService


class RecoveryCandidateExpander:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._retrieval_recovery_service = RetrievalRecoveryService()

    # =====================================================
    # PUBLIC
    # =====================================================

    def expand(
        self,
        items: list[QuestionBankItem],
        constraints: InterviewConstraints,
        action: RecoveryAction,
        role: RoleType,
        level: SeniorityLevel,
    ) -> RecoveryExpansionResult:

        # -------------------------------------------------
        # EXPAND ROLE SCOPE
        # -------------------------------------------------

        if action == RecoveryAction.EXPAND_ROLE_SCOPE:

            recovery_result = self._retrieval_recovery_service.expand_role_scope(
                items=items,
                role=role,
                level=level,
            )

            return RecoveryExpansionResult(
                expanded_items=(recovery_result.expanded_items),
                applied_action=action,
                added_candidates=max(
                    0,
                    len(recovery_result.expanded_items) - len(items),
                ),
                telemetry=recovery_result.telemetry,
            )

        # -------------------------------------------------
        # NO-OP
        # -------------------------------------------------

        return RecoveryExpansionResult(
            expanded_items=items,
            applied_action=action,
            added_candidates=0,
            telemetry=None,
        )
