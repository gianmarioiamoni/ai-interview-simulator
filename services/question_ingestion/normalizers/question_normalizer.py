# services/question_ingestion/normalizers/question_normalizer.py

from typing import List
from datetime import datetime, timezone

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_ingestion.contracts import (
    RawQuestionRecord,
    NormalizedQuestionRecord,
)

from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata

class QuestionNormalizer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def normalize(
        self,
        records: List[RawQuestionRecord],
    ) -> List[NormalizedQuestionRecord]:

        normalized: List[NormalizedQuestionRecord] = []

        for record in records:

            item = self._normalize_record(record)

            if item is not None:
                normalized.append(item)

        return normalized

    # =====================================================
    # INTERNALS
    # =====================================================

    def _normalize_record(
        self,
        record: RawQuestionRecord,
    ) -> NormalizedQuestionRecord | None:

        payload = record.raw_payload

        # -------------------------------------------------
        # TEXT EXTRACTION
        # -------------------------------------------------

        # text = payload.get("question")
        text = self._extract_text(
            payload,
        )
        # TODO:
        # add structured normalization rejection reporting
        # to track why records are discarded
        if not text:
            return None

        if not isinstance(text, str):
            return None

        text = text.strip()

        # -------------------------------------------------
        # MIN QUALITY
        # -------------------------------------------------

        if len(text) < 15:
            return None

        # -------------------------------------------------
        # NORMALIZATION
        # -------------------------------------------------

        text = self._normalize_whitespace(text)

        return NormalizedQuestionRecord(
            text=text,
            source=record.source,
            ingestion_metadata=IngestionMetadata(
                source_name=record.source,
                source_type="json",
                dataset_version="v1",
                ingestion_timestamp=datetime.now(timezone.utc),
            ),
            role_hint=self._extract_role(
                payload,
            ),
            area_hint=self._extract_area(
                payload,
            ),
            level_hint=self._extract_level(
                payload,
            ),
            difficulty_hint=payload.get(
                "difficulty",
            ),
        )

    def _extract_role(
        self,
        payload: dict,
    ) -> RoleType | None:

        value = payload.get("role")

        if not value:
            return None

        try:
            return RoleType(value)
        except Exception:
            return None

    def _extract_area(
        self,
        payload: dict,
    ) -> InterviewArea | None:

        value = payload.get("area")

        if not value:
            return None

        try:
            return InterviewArea(value)
        except Exception:
            return None

    def _extract_level(
        self,
        payload: dict,
    ) -> SeniorityLevel | None:

        value = payload.get("level")

        if not value:
            return None

        try:
            return SeniorityLevel(value)
        except Exception:
            return None
    # =====================================================
    # HELPERS
    # =====================================================

    def _normalize_whitespace(
        self,
        text: str,
    ) -> str:

        return " ".join(text.split())

    def _extract_text(
        self,
        payload: dict,
    ) -> str | None:

        candidate_fields = [
            "question",
            "prompt",
            "text",
            "content",
            "body",
        ]

        for field in candidate_fields:

            value = payload.get(field)

            if (
                isinstance(value, str)
                and value.strip()
            ):
                return value.strip()

        return None
