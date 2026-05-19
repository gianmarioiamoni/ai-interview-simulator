# services/question_intelligence/fallback/fallback_retrieval_plan.py

from typing import List

from services.question_intelligence.fallback.retrieval_stage import (
    RetrievalStage,
)


class FallbackRetrievalPlan:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(self) -> List[RetrievalStage]:

        return [
            # ---------------------------------------------
            # STRICT
            # ---------------------------------------------
            RetrievalStage(
                use_role=True,
                use_level=True,
                use_interview_type=True,
                use_area=True,
            ),
            # ---------------------------------------------
            # RELAX LEVEL
            # ---------------------------------------------
            RetrievalStage(
                use_role=True,
                use_level=False,
                use_interview_type=True,
                use_area=True,
            ),
            # ---------------------------------------------
            # RELAX ROLE
            # ---------------------------------------------
            RetrievalStage(
                use_role=False,
                use_level=False,
                use_interview_type=True,
                use_area=True,
            ),
            # ---------------------------------------------
            # AREA ONLY
            # ---------------------------------------------
            RetrievalStage(
                use_role=False,
                use_level=False,
                use_interview_type=False,
                use_area=True,
            ),
        ]
