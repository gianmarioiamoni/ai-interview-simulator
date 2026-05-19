# services/question_intelligence/corpus/corpus_diagnostics_engine.py

from collections import Counter

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.corpus.corpus_diagnostics_report import (
    CorpusDiagnosticsReport,
)


class CorpusDiagnosticsEngine:

    # =====================================================
    # PUBLIC
    # =====================================================

    def analyze(
        self,
        items: list[QuestionBankItem],
    ) -> CorpusDiagnosticsReport:

        texts = [item.text for item in items]

        unique_texts = set(texts)

        duplicate_questions = len(texts) - len(unique_texts)

        duplicate_ratio = 0.0

        if texts:

            duplicate_ratio = duplicate_questions / len(texts)

        role_distribution = Counter(item.role.type.value for item in items)

        level_distribution = Counter(item.level.value for item in items)

        area_distribution = Counter(item.area.value for item in items)

        source_distribution = Counter(
            item.ingestion_metadata.source_name for item in items
        )

        return CorpusDiagnosticsReport(
            total_questions=len(texts),
            unique_questions=len(unique_texts),
            duplicate_questions=(duplicate_questions),
            duplicate_ratio=round(
                duplicate_ratio,
                2,
            ),
            role_distribution=dict(role_distribution),
            level_distribution=dict(level_distribution),
            area_distribution=dict(area_distribution),
            source_distribution=dict(source_distribution),
        )
