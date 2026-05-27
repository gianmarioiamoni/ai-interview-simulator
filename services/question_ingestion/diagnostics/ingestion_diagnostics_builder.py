# services/question_ingestion/diagnostics/ingestion_diagnostics_builder.py

from typing import List

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.question_ingestion.contracts import (
    RawQuestionRecord,
    NormalizedQuestionRecord,
)
from services.question_ingestion.diagnostics.ingestion_diagnostics_report import IngestionDiagnosticsReport


class IngestionDiagnosticsBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        dataset_name: str,
        source_type: str,
        adapter_name: str,
        raw_records: List[RawQuestionRecord],
        normalized_records: List[NormalizedQuestionRecord],
        classified_records: List[NormalizedQuestionRecord],
        mapped_items: List[QuestionBankItem],
        indexed_records: int,
        duplicate_records: int,
        average_quality_score: float,
        average_similarity: float,
        ingestion_duration_seconds: float,
        errors: list[str] | None = None,
        success: bool = True,
    ) -> IngestionDiagnosticsReport:

        skipped = len(classified_records) - len(mapped_items)

        return IngestionDiagnosticsReport(
            dataset_name=dataset_name,
            source_type=source_type,
            adapter_name=adapter_name,
            loaded_records=len(raw_records),
            normalized_records=len(normalized_records),
            classified_records=len(classified_records),
            mapped_records=len(mapped_items),
            indexed_records=indexed_records,
            duplicate_records=duplicate_records,
            average_quality_score=average_quality_score,
            average_similarity=average_similarity,
            skipped_unknown=max(skipped, 0),
            ingestion_duration_seconds=ingestion_duration_seconds,
            errors=errors or [],
            success=success,
        )
