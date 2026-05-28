# services/question_ingestion/corpus_semantic_validator.py

from services.question_ingestion.contracts import (
    RawQuestionRecord,
    CorpusValidationResult,
)

from services.question_ingestion.contracts.candidate_question import CandidateQuestion
from services.question_ingestion.normalizers.question_normalizer import QuestionNormalizer
from services.question_ingestion.contextual_question_rewriter import ContextualQuestionRewriter
from services.question_intelligence.technical_question_filter import TechnicalQuestionFilter
from services.question_intelligence.quality.interview_question_quality_filter import InterviewQuestionQualityFilter


class CorpusSemanticValidator:

    # =====================================================
    # PUBLIC
    # =====================================================

    def validate(
        self,
        questions: list[CandidateQuestion],
        source_name: str,
        source_type: str,
        dataset_version: str,
    ) -> list[CorpusValidationResult]:

        technical_filter = TechnicalQuestionFilter()

        interview_filter = InterviewQuestionQualityFilter()

        normalizer = QuestionNormalizer()

        rewriter = ContextualQuestionRewriter()

        results: list[CorpusValidationResult] = []

        for candidate in questions:

            # -------------------------------------------------
            # CONTEXTUAL REWRITE
            # -------------------------------------------------

            rewritten = rewriter.rewrite(candidate)

            # -------------------------------------------------
            # SEMANTIC EVALUATION
            # -------------------------------------------------

            technical_result = technical_filter.evaluate(
                rewritten,
            )

            interview_result = interview_filter.evaluate(
                rewritten,
            )

            is_accepted = technical_result.is_technical

            # -------------------------------------------------
            # RAW RECORD
            # -------------------------------------------------

            raw_record = RawQuestionRecord(
                source=source_name,
                source_type=source_type,
                dataset_version=dataset_version,
                raw_payload={
                    "text": rewritten,
                },
                canonical_payload={
                    "text": rewritten,
                },
            )

            # -------------------------------------------------
            # NORMALIZATION
            # -------------------------------------------------

            normalization = normalizer.normalize(
                [raw_record],
            )

            normalized = None

            if normalization.records and is_accepted:

                normalized = normalization.records[0]

            # -------------------------------------------------
            # ENRICH CANDIDATE
            # -------------------------------------------------

            candidate.semantic_domains = technical_result.matched_categories

            candidate.contextualized_text = rewritten

            candidate.quality_score = interview_result.score

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            results.append(
                CorpusValidationResult(
                    raw_question=rewritten,
                    technical_result=technical_result,
                    normalized_record=normalized,
                )
            )

        return results
