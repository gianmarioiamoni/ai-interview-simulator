# services/question_corpus/validators/corpus_validator.py

from services.question_corpus.contracts.curated_corpus import CuratedCorpus
from services.question_corpus.validations.contracts.corpus_validation_report import CorpusValidationReport
from services.question_corpus.validators.corpus_duplicate_detector import CorpusDuplicateDetector


class CorpusValidator:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._duplicate_detector = CorpusDuplicateDetector()

    # =====================================================
    # PUBLIC
    # =====================================================

    def validate(
        self,
        corpus: CuratedCorpus,
    ) -> CorpusValidationReport:

        issues = []

        duplicate_issues = self._duplicate_detector.detect(
            corpus,
        )

        issues.extend(duplicate_issues)

        return CorpusValidationReport(
            total_questions=len(corpus.questions),
            total_issues=len(issues),
            issues=issues,
        )
