# services/question_intelligence/policies/retrieval_policy_resolver.py

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.policies.retrieval_policy import (
    RetrievalPolicy,
)


class RetrievalPolicyResolver:

    # =====================================================
    # PUBLIC
    # =====================================================

    def resolve(
        self,
        role: RoleType,
        level: SeniorityLevel,
    ) -> RetrievalPolicy:

        # -------------------------------------------------
        # SENIOR BACKEND
        # -------------------------------------------------

        if role == RoleType.BACKEND_ENGINEER and level == SeniorityLevel.SENIOR:

            return RetrievalPolicy(
                max_questions_per_topic=1,
                redundancy_threshold=0.50,
                target_diversity=0.90,
                prioritize_scalability=True,
                prioritize_fundamentals=False,
                prioritize_system_design=True,
            )

        # -------------------------------------------------
        # JUNIOR FRONTEND
        # -------------------------------------------------

        if role == RoleType.FRONTEND_ENGINEER and level == SeniorityLevel.JUNIOR:

            return RetrievalPolicy(
                max_questions_per_topic=2,
                redundancy_threshold=0.65,
                target_diversity=0.60,
                prioritize_scalability=False,
                prioritize_fundamentals=True,
                prioritize_system_design=False,
            )

        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        return RetrievalPolicy(
            max_questions_per_topic=2,
            redundancy_threshold=0.55,
            target_diversity=0.75,
            prioritize_scalability=False,
            prioritize_fundamentals=True,
            prioritize_system_design=False,
        )
