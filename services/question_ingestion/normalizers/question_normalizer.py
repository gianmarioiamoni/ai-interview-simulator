# services/question_ingestion/normalizers/question_normalizer.py

from typing import List
from datetime import datetime, timezone

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

        print()
        print(f"PAYLOAD: {payload}")
        print()

        # -------------------------------------------------
        # TEXT EXTRACTION
        # -------------------------------------------------

        # text = payload.get("question")
        text = self._extract_text(
            payload,
        )

        print()
        print(f"TEXT: {text}")
        print()

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
        )

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
