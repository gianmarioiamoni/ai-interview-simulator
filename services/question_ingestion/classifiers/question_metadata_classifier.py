# services/question_ingestion/classifiers/question_metadata_classifier.py

from typing import List

from services.question_ingestion.contracts import (
    NormalizedQuestionRecord,
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
    ) -> str | None:

        lower = text.lower()

        if any(
            k in lower
            for k in [
                "react",
                "frontend",
                "css",
                "browser",
                "ui",
            ]
        ):
            return "frontend_engineer"

        if any(
            k in lower
            for k in [
                "api",
                "database",
                "backend",
                "microservice",
                "sql",
            ]
        ):
            return "backend_engineer"

        return None

    # =====================================================
    # AREA
    # =====================================================

    def _infer_area(
        self,
        text: str,
    ) -> str | None:

        lower = text.lower()

        if any(
            k in lower
            for k in [
                "database",
                "sql",
                "index",
                "join",
            ]
        ):
            return "technical_database"

        if any(
            k in lower
            for k in [
                "architecture",
                "scalability",
                "distributed",
                "microservice",
            ]
        ):
            return "technical_case_study"

        if any(
            k in lower
            for k in [
                "react",
                "api",
                "rest",
                "graphql",
            ]
        ):
            return "technical_technical_knowledge"

        return None

    # =====================================================
    # LEVEL
    # =====================================================

    def _infer_level(
        self,
        text: str,
    ) -> str | None:

        lower = text.lower()

        advanced_terms = [
            "distributed",
            "scalability",
            "optimization",
            "performance",
            "architecture",
        ]

        if any(k in lower for k in advanced_terms):
            return "senior"

        return "mid"

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
