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

from services.question_ingestion.contracts.ingestion_metadata import (
    IngestionMetadata,
)

from services.question_ingestion.contracts.normalization_result import (
    NormalizationResult,
)

from services.question_ingestion.contracts.normalization_diagnostics import (
    NormalizationDiagnostics,
)


class QuestionNormalizer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def normalize(
        self,
        records: List[RawQuestionRecord],
    ) -> NormalizationResult:

        normalized: List[NormalizedQuestionRecord] = []

        diagnostics = NormalizationDiagnostics(
            total_records=len(records),
        )

        for record in records:

            result, rejection_reason = self._normalize_record(
                record=record,
            )

            if result is None:

                if rejection_reason is not None:
                    diagnostics = diagnostics.model_copy(
                        update={
                            rejection_reason: (
                                getattr(diagnostics, rejection_reason) + 1
                            ),
                        },
                    )

                continue

            normalized.append(result)

            diagnostics = diagnostics.model_copy(
                update={"normalized_records": (diagnostics.normalized_records + 1)}
            )

        return NormalizationResult(
            records=normalized,
            diagnostics=diagnostics,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _normalize_record(
        self,
        record: RawQuestionRecord,
    ) -> tuple[NormalizedQuestionRecord | None, str | None]:

        payload = record.canonical_payload

        # -------------------------------------------------
        # TEXT EXTRACTION
        # -------------------------------------------------

        text = payload.get("text")

        if not text:
            return None, "rejected_missing_text"

        if not isinstance(text, str):
            return None, "rejected_invalid_text"

        text = text.strip()

        # -------------------------------------------------
        # MIN QUALITY
        # -------------------------------------------------

        if len(text) < 15:
            return None, "rejected_too_short"

        # -------------------------------------------------
        # NORMALIZATION
        # -------------------------------------------------

        text = self._normalize_whitespace(
            text,
        )

        return (
            NormalizedQuestionRecord(
                text=text,
                source=record.source,
                ingestion_metadata=IngestionMetadata(
                    source_name=record.source,
                    source_type=record.source_type,
                    dataset_version=record.dataset_version,
                    ingestion_timestamp=(
                        datetime.now(
                            timezone.utc,
                        )
                    ),
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
            ),
            None,
        )

    # =====================================================
    # ROLE EXTRACTION
    # =====================================================

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

    # =====================================================
    # AREA EXTRACTION
    # =====================================================

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

    # =====================================================
    # LEVEL EXTRACTION
    # =====================================================

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
