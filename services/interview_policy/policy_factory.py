# services/interview_policy/policy_factory.py

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.interview_policy.interview_policy import (
    InterviewPolicy,
)


class PolicyFactory:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
    ) -> InterviewPolicy:

        # -------------------------------------------------
        # BACKEND
        # -------------------------------------------------

        if role == RoleType.BACKEND_ENGINEER:

            if level == SeniorityLevel.SENIOR:

                return InterviewPolicy(
                    target_average_difficulty=4.5,
                    preferred_areas=[
                        "technical_case_study",
                        "technical_database",
                    ],
                    max_questions_per_area=2,
                    prioritize_architecture=True,
                    prioritize_scalability=True,
                    prioritize_production_experience=True,
                )

            return InterviewPolicy(
                target_average_difficulty=3.5,
                preferred_areas=[
                    "technical_database",
                    "technical_technical_knowledge",
                ],
                max_questions_per_area=2,
                prioritize_architecture=False,
                prioritize_scalability=True,
                prioritize_production_experience=False,
            )

        # -------------------------------------------------
        # FRONTEND
        # -------------------------------------------------

        if role == RoleType.FRONTEND_ENGINEER:

            return InterviewPolicy(
                target_average_difficulty=3.5,
                preferred_areas=[
                    "technical_technical_knowledge",
                ],
                max_questions_per_area=3,
                prioritize_architecture=False,
                prioritize_scalability=False,
                prioritize_production_experience=True,
            )

        # -------------------------------------------------
        # DEVOPS
        # -------------------------------------------------

        if role == RoleType.DEVOPS_ENGINEER:

            return InterviewPolicy(
                target_average_difficulty=4.0,
                preferred_areas=[
                    "technical_case_study",
                ],
                max_questions_per_area=3,
                prioritize_architecture=True,
                prioritize_scalability=True,
                prioritize_production_experience=True,
            )

        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        return InterviewPolicy(
            target_average_difficulty=3.5,
            preferred_areas=[
                "technical_technical_knowledge",
            ],
            max_questions_per_area=2,
            prioritize_architecture=False,
            prioritize_scalability=False,
            prioritize_production_experience=False,
        )
