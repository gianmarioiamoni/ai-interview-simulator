# services/replanning/recovery_candidate_expander.py

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.interview_planning.interview_constraints import InterviewConstraints
from services.planning_validation.recovery_action import RecoveryAction
from services.replanning.contracts.recovery_expansion_result import RecoveryExpansionResult
from services.replanning.retrieval_recovery_service import RetrievalRecoveryService
from services.replanning.role_expansion_strategy import RoleExpansionStrategy


class RecoveryCandidateExpander:


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

            expanded = self._retrieval_recovery_service.expand_role_scope(
                items=items,
                role=role,
                level=level,
            )

            return RecoveryExpansionResult(
                expanded_items=expanded,
                applied_action=action,
                added_candidates=max(
                    0,
                    len(expanded) - len(items),
                ),
            )

        # -------------------------------------------------
        # NO-OP
        # -------------------------------------------------

        return RecoveryExpansionResult(
            expanded_items=items,
            applied_action=action,
            added_candidates=0,
        )

    # =====================================================
    # ROLE EXPANSION
    # =====================================================

    def _expand_role_scope(
        self,
        items: list[QuestionBankItem],
    ) -> list[QuestionBankItem]:

        # -------------------------------------------------
        # TEMPORARY PLACEHOLDER
        # -------------------------------------------------

        # In A.23 initial version we simply return the
        # original pool. Future steps will integrate
        # retrieval-aware expansion.

        return items
