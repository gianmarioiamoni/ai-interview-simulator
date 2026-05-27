# services/question_ingestion/corpus_onboarding_service.py

from statistics import mean

from services.question_ingestion.contracts import (
    GitHubDocument,
    CorpusOnboardingResult,
)

from services.question_ingestion.github_markdown_extractor import GitHubMarkdownExtractor
from services.question_ingestion.corpus_semantic_validator import CorpusSemanticValidator


class CorpusOnboardingService:

    # =====================================================
    # PUBLIC
    # =====================================================

    def onboard(
        self,
        document: GitHubDocument,
    ) -> CorpusOnboardingResult:

        extractor = GitHubMarkdownExtractor()

        validator = CorpusSemanticValidator()

        # -------------------------------------------------
        # EXTRACTION
        # -------------------------------------------------

        questions = extractor.extract_questions(
            document=document,
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        results = validator.validate(
            questions=questions,
            source_name=(document.repository),
            source_type="github",
            dataset_version="v1",
        )

        # -------------------------------------------------
        # SPLIT
        # -------------------------------------------------

        accepted = [result for result in results if (result.filter_result.is_technical)]

        rejected = [
            result for result in results if not (result.filter_result.is_technical)
        ]

        # -------------------------------------------------
        # SCORING
        # -------------------------------------------------

        scores = [result.filter_result.score for result in accepted]

        average_score = 0.0

        if scores:

            average_score = round(
                mean(scores),
                2,
            )

        # -------------------------------------------------
        # DECISION
        # -------------------------------------------------

        decision = self._make_decision(
            accepted_count=(len(accepted)),
            average_score=(average_score),
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        return CorpusOnboardingResult(
            repository_name=(document.repository),
            total_questions=(len(results)),
            accepted_questions=(len(accepted)),
            rejected_questions=(len(rejected)),
            average_score=(average_score),
            accepted_results=(accepted),
            rejected_results=(rejected),
            onboarding_decision=(decision),
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _make_decision(
        self,
        accepted_count: int,
        average_score: float,
    ) -> str:

        if accepted_count < 3:
            return "reject"

        if average_score < 0.35:
            return "reject"

        if average_score < 0.5:
            return "review"

        return "approve"
