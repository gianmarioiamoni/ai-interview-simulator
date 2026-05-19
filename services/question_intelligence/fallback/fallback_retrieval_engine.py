# services/question_intelligence/fallback/fallback_retrieval_engine.py

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.interview.interview_type import (
    InterviewType,
)

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.retrieval.retrieval_strategy import (
    RetrievalStrategy,
)

from services.question_intelligence.fallback.fallback_retrieval_plan import (
    FallbackRetrievalPlan,
)


class FallbackRetrievalEngine:

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
    ) -> None:

        self._retrieval_service = retrieval_service

        self._plan = FallbackRetrievalPlan()

    # =====================================================
    # PUBLIC
    # =====================================================

    def retrieve(
        self,
        query: str,
        retrieval_strategy: RetrievalStrategy,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
    ):

        stages = self._plan.build()

        for stage in stages:

            results = self._retrieval_service.retrieve(
                query=query,
                retrieval_strategy=(retrieval_strategy),
                role=(role.value if stage.use_role else None),
                level=(level.value if stage.use_level else None),
                interview_type=(
                    interview_type.value if stage.use_interview_type else None
                ),
                area=(area.value if stage.use_area else None),
            )

            if results:
                return results

        return []
