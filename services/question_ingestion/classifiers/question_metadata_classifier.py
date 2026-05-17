# services/question_ingestion/classifiers/question_metadata_classifier.py

from typing import List

from services.question_ingestion.contracts import (
    NormalizedQuestionRecord,
)

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from services.question_intelligence.retrieval.retrieval_role_hints import (
    ROLE_HINTS,
)

from services.question_intelligence.retrieval.retrieval_area_hints import (
    AREA_HINTS,
)

from services.question_intelligence.retrieval.retrieval_level_hints import (
    LEVEL_HINTS,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)


class QuestionMetadataClassifier:

    # =====================================================
    # PUBLIC
    # =====================================================

    def classify(
        self,
        records: List[NormalizedQuestionRecord],
    ) -> List[NormalizedQuestionRecord]:

        enriched: List[NormalizedQuestionRecord] = []

        for record in records:

            enriched.append(
                record.model_copy(
                    update={
                        "role_hint": self._infer_role(record.text),
                        "area_hint": self._infer_area(record.text),
                        "level_hint": self._infer_level(record.text),
                        "difficulty_hint": self._infer_difficulty(record.text),
                    }
                )
            )

        return enriched

    # =====================================================
    # ROLE
    # =====================================================

    def _infer_role(
        self,
        text: str,
    ) -> RoleType | None:

        lower = text.lower()

        best_match = None
        best_score = 0

        for role, hints in ROLE_HINTS.items():

            score = sum(
                1 for hint in hints
                if hint.lower() in lower
            )

            if score > best_score:
                best_score = score
                best_match = role

        if best_match is None:
            return None

        return best_match

    # =====================================================
    # AREA
    # =====================================================

    def _infer_area(
        self,
        text: str,
    ) -> InterviewArea | None:

        lower = text.lower()

        best_match = None
        best_score = 0

        for area, hints in AREA_HINTS.items():

            score = sum(
                1 for hint in hints
                if hint.lower() in lower
            )

            if score > best_score:
                best_score = score
                best_match = area

        if best_match is None:
            return None

        return best_match

    # =====================================================
    # LEVEL
    # =====================================================

    def _infer_level(
        self,
        text: str,
    ) -> SeniorityLevel | None:

        lower = text.lower()

        senior_score = sum(
            1 for hint in LEVEL_HINTS[SeniorityLevel.SENIOR]
            if hint.lower() in lower
        )


        if senior_score > 0:
            return SeniorityLevel.SENIOR

        return SeniorityLevel.MID

    # =====================================================
    # DIFFICULTY
    # =====================================================

    def _infer_difficulty(
        self,
        text: str,
    ) -> int:

        lower = text.lower()

        hard_terms = [
            "distributed",
            "scalability",
            "optimization",
            "consistency",
            "concurrency",
        ]

        medium_terms = [
            "api",
            "database",
            "react",
            "graphql",
        ]

        if any(k in lower for k in hard_terms):
            return 5

        if any(k in lower for k in medium_terms):
            return 3

        return 2
