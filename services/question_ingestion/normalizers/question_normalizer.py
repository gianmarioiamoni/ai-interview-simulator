# services/question_ingestion/normalizers/question_normalizer.py

from typing import List

from services.question_ingestion.contracts import (
    RawQuestionRecord,
    NormalizedQuestionRecord,
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

        text = payload.get("question")

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
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _normalize_whitespace(
        self,
        text: str,
    ) -> str:

        return " ".join(text.split())
