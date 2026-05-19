# services/candidate_pool/candidate_pool_builder.py

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.candidate_pool.candidate_pool import (
    CandidatePool,
)


class CandidatePoolBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        items: list[QuestionBankItem],
        role: RoleType,
        level: SeniorityLevel,
    ) -> CandidatePool:

        eligible = []
        rejected = []

        for item in items:

            if not self._is_role_compatible(
                item,
                role,
            ):

                rejected.append(item)
                continue

            if not self._is_level_compatible(
                item,
                level,
            ):

                rejected.append(item)
                continue

            eligible.append(item)

        return CandidatePool(
            eligible_questions=eligible,
            rejected_questions=rejected,
            total_candidates=len(items),
            eligible_count=len(eligible),
            rejected_count=len(rejected),
        )

    # =====================================================
    # ROLE FILTERING
    # =====================================================

    def _is_role_compatible(
        self,
        item: QuestionBankItem,
        role: RoleType,
    ) -> bool:

        if item.role.type == role:
            return True

        # -------------------------------------------------
        # FULLSTACK
        # -------------------------------------------------

        if role == RoleType.FULLSTACK_ENGINEER:

            return item.role.type in [
                RoleType.BACKEND_ENGINEER,
                RoleType.FRONTEND_ENGINEER,
                RoleType.FULLSTACK_ENGINEER,
            ]

        # -------------------------------------------------
        # BACKEND
        # -------------------------------------------------

        if role == RoleType.BACKEND_ENGINEER:

            return item.role.type in [
                RoleType.BACKEND_ENGINEER,
                RoleType.DEVOPS_ENGINEER,
                RoleType.DATA_ENGINEER,
            ]

        # -------------------------------------------------
        # FRONTEND
        # -------------------------------------------------

        if role == RoleType.FRONTEND_ENGINEER:

            return item.role.type in [
                RoleType.FRONTEND_ENGINEER,
                RoleType.FULLSTACK_ENGINEER,
            ]

        return False

    # =====================================================
    # LEVEL FILTERING
    # =====================================================

    def _is_level_compatible(
        self,
        item: QuestionBankItem,
        level: SeniorityLevel,
    ) -> bool:

        # -------------------------------------------------
        # SENIOR
        # -------------------------------------------------

        if level == SeniorityLevel.SENIOR:

            return item.level in [
                SeniorityLevel.MID,
                SeniorityLevel.SENIOR,
            ]

        # -------------------------------------------------
        # MID
        # -------------------------------------------------

        if level == SeniorityLevel.MID:

            return item.level == SeniorityLevel.MID

        # -------------------------------------------------
        # JUNIOR
        # -------------------------------------------------

        return item.level == SeniorityLevel.JUNIOR
