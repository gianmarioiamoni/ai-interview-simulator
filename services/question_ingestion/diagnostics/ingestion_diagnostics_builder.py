# services/question_ingestion/diagnostics/ingestion_diagnostics_builder.py

from typing import List

from services.question_ingestion.contracts import (
    RawQuestionRecord,
    NormalizedQuestionRecord,
)

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_ingestion.diagnostics.ingestion_diagnostics_report import (
    IngestionDiagnosticsReport,
)


class IngestionDiagnosticsBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        raw_records: List[RawQuestionRecord],
        normalized_records: List[NormalizedQuestionRecord],
        classified_records: List[NormalizedQuestionRecord],
        mapped_items: List[QuestionBankItem],
        indexed_records: int,
    ) -> IngestionDiagnosticsReport:

        skipped = len(classified_records) - len(mapped_items)

        return IngestionDiagnosticsReport(
            loaded_records=len(raw_records),
            normalized_records=len(normalized_records),
            classified_records=len(classified_records),
            mapped_records=len(mapped_items),
            indexed_records=indexed_records,
            skipped_unknown=max(skipped, 0),
        )
