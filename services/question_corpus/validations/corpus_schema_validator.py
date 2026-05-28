# services/question_corpus/validation/corpus_schema_validator.py

from collections import Counter

from domain.contracts.corpus.curated_question import CuratedQuestion

from services.question_corpus.validations.contracts.corpus_validation_issue import CorpusValidationIssue
from services.question_corpus.validations.contracts.corpus_validation_report import CorpusValidationReport


class CorpusSchemaValidator:

    MIN_QUALITY_SCORE = 0.5

    # =====================================================
    # PUBLIC
    # =====================================================

    def validate(
        self,
        questions: list[CuratedQuestion],
    ) -> CorpusValidationReport:

        issues: list[CorpusValidationIssue] = []

        issues.extend(
            self._validate_duplicate_ids(
                questions,
            )
        )

        issues.extend(
            self._validate_duplicate_texts(
                questions,
            )
        )

        issues.extend(
            self._validate_quality_scores(
                questions,
            )
        )

        issues.extend(
            self._validate_domains(
                questions,
            )
        )

        errors = len([issue for issue in issues if issue.severity == "error"])

        warnings = len([issue for issue in issues if issue.severity == "warning"])

        return CorpusValidationReport(
            total_questions=len(questions),
            total_issues=len(issues),
            errors=errors,
            warnings=warnings,
            issues=issues,
        )

    # =====================================================
    # VALIDATIONS
    # =====================================================

    def _validate_duplicate_ids(
        self,
        questions: list[CuratedQuestion],
    ) -> list[CorpusValidationIssue]:

        issues: list[CorpusValidationIssue] = []

        counts = Counter(q.id for q in questions)

        for question_id, count in counts.items():

            if count <= 1:
                continue

            issues.append(
                CorpusValidationIssue(
                    severity="error",
                    category="duplicate_id",
                    message=f"Duplicate ID detected: {question_id}",
                    question_id=question_id,
                )
            )

        return issues

    def _validate_duplicate_texts(
        self,
        questions: list[CuratedQuestion],
    ) -> list[CorpusValidationIssue]:

        issues: list[CorpusValidationIssue] = []

        normalized_texts = [q.question.strip().lower() for q in questions]

        counts = Counter(normalized_texts)

        for text, count in counts.items():

            if count <= 1:
                continue

            issues.append(
                CorpusValidationIssue(
                    severity="warning",
                    category="duplicate_text",
                    message=f"Duplicate question text detected: {text[:80]}",
                )
            )

        return issues

    def _validate_quality_scores(
        self,
        questions: list[CuratedQuestion],
    ) -> list[CorpusValidationIssue]:

        issues: list[CorpusValidationIssue] = []

        for question in questions:

            if question.quality_score >= self.MIN_QUALITY_SCORE:
                continue

            issues.append(
                CorpusValidationIssue(
                    severity="warning",
                    category="low_quality",
                    message=(f"Low quality question: " f"{question.quality_score}"),
                    question_id=question.id,
                )
            )

        return issues

    def _validate_domains(
        self,
        questions: list[CuratedQuestion],
    ) -> list[CorpusValidationIssue]:

        issues: list[CorpusValidationIssue] = []

        for question in questions:

            if question.domains:
                continue

            issues.append(
                CorpusValidationIssue(
                    severity="error",
                    category="missing_domains",
                    message="Question has no semantic domains",
                    question_id=question.id,
                )
            )

        return issues
