# services/question_corpus/audit/corpus_merge_audit.py

from collections import Counter
from pathlib import Path

from domain.contracts.corpus import QuestionCorpus

from services.question_corpus.analyzers.corpus_statistics_analyzer import (
    CorpusStatisticsAnalyzer,
)
from services.question_corpus.audit.corpus_merge_audit_report import (
    CorpusMergeAuditReport,
    MergeTotals,
    SourceSummary,
)
from services.question_corpus.contracts.curated_corpus import CuratedCorpus
from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.loaders.json_corpus_loader import JsonCorpusLoader
from services.question_corpus.mappers.curated_question_bank_item_mapper import (
    CuratedQuestionBankItemMapper,
)
from services.question_corpus.validations.corpus_schema_validator import (
    CorpusSchemaValidator,
)
from services.question_corpus.validators.corpus_duplicate_detector import (
    CorpusDuplicateDetector,
)
from services.question_intelligence.balancing.dataset_balancing_engine import (
    DatasetBalancingEngine,
)
from services.question_intelligence.corpus.corpus_diagnostics_engine import (
    CorpusDiagnosticsEngine,
)


class CorpusMergeAudit:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._json_loader = JsonCorpusLoader()
        self._folder_loader = FolderCorpusLoader()
        self._schema_validator = CorpusSchemaValidator()
        self._duplicate_detector = CorpusDuplicateDetector()
        self._statistics_analyzer = CorpusStatisticsAnalyzer()
        self._bank_item_mapper = CuratedQuestionBankItemMapper()
        self._diagnostics_engine = CorpusDiagnosticsEngine()
        self._balancing_engine = DatasetBalancingEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def run(
        self,
        source_paths: list[str],
    ) -> CorpusMergeAuditReport:

        sources: list[SourceSummary] = []
        merged_questions = []

        for source_path in source_paths:

            corpus = self._load_source(
                source_path=source_path,
            )

            sources.append(
                SourceSummary(
                    path=source_path,
                    question_count=len(corpus.questions),
                    areas_distribution=dict(
                        Counter(
                            question.area.value
                            for question in corpus.questions
                        )
                    ),
                )
            )

            merged_questions.extend(corpus.questions)

        merged_corpus = CuratedCorpus(
            questions=merged_questions,
        )

        question_corpus = QuestionCorpus(
            questions=merged_questions,
        )

        schema_validation = self._schema_validator.validate(
            merged_questions,
        )

        near_duplicates_token = self._duplicate_detector.detect(
            merged_corpus,
        )

        statistics = self._statistics_analyzer.analyze(
            question_corpus,
        )

        bank_items = self._bank_item_mapper.map(
            merged_questions,
        )

        diagnostics = self._diagnostics_engine.analyze(
            bank_items,
        )

        balancing = self._balancing_engine.analyze(
            bank_items,
        )

        merge_totals = MergeTotals(
            raw_count=len(merged_questions),
            unique_id_count=len(
                {question.id for question in merged_questions}
            ),
            unique_text_count=diagnostics.unique_questions,
            duplicate_text_count=diagnostics.duplicate_questions,
        )

        return CorpusMergeAuditReport(
            sources=sources,
            merge_totals=merge_totals,
            schema_validation=schema_validation,
            near_duplicates_token=near_duplicates_token,
            statistics=statistics,
            diagnostics=diagnostics,
            balancing=balancing,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _load_source(
        self,
        source_path: str,
    ) -> CuratedCorpus:

        path = Path(source_path)

        if path.is_dir():

            return self._folder_loader.load(
                source_path,
            )

        return self._json_loader.load(
            source_path,
        )
