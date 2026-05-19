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

from services.question_quality.technical_question_filter import (
    TechnicalQuestionFilter,
)

class QuestionNormalizer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def normalize(
        self,
        records: List[RawQuestionRecord],
    ) -> List[NormalizedQuestionRecord]:

        normalized: List[NormalizedQuestionRecord] = []
        technical_filter = TechnicalQuestionFilter()

        for record in records:

            item = self._normalize_record(
                record=record,
                technical_filter=technical_filter,
            )

            if item is not None:
                normalized.append(item)

        return normalized

    # =====================================================
    # INTERNALS
    # =====================================================

    def _normalize_record(
        self,
        record: RawQuestionRecord,
        technical_filter: TechnicalQuestionFilter
    ) -> NormalizedQuestionRecord | None:

        payload = record.canonical_payload

        # -------------------------------------------------
        # TEXT EXTRACTION
        # -------------------------------------------------

        text = payload.get("text")

        # -------------------------------------------------
        # TECHNICAL DOMAIN FILTER
        # -------------------------------------------------

        if not technical_filter.is_technical(text):
            return None
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
                source_type=record.source_type,
                dataset_version=record.dataset_version,
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
