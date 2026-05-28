# services/question_ingestion/corpus_semantic_validator.py

from services.question_ingestion.contracts import (
    RawQuestionRecord,
    CorpusValidationResult,
)

from services.question_ingestion.normalizers.question_normalizer import QuestionNormalizer
from services.question_intelligence.technical_question_filter import TechnicalQuestionFilter
from services.question_intelligence.quality.interview_question_quality_filter import InterviewQuestionQualityFilter
from services.question_intelligence.quality.contracts.quality_decision import QualityDecision
from services.question_ingestion.contracts.candidate_question import CandidateQuestion


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

        results: list[CorpusValidationResult] = []

        for candidate in questions:

            # -------------------------------------------------
            # SEMANTIC EVALUATION
            # -------------------------------------------------

            technical_result = technical_filter.evaluate(candidate.text)
            interview_result = interview_filter.evaluate(candidate.text)

            is_accepted = (
                technical_result.is_technical
                and interview_result.decision != QualityDecision.REJECT
            )

            # -------------------------------------------------
            # RAW RECORD
            # -------------------------------------------------

            raw_record = RawQuestionRecord(
                source=source_name,
                source_type=(source_type),
                dataset_version=(dataset_version),
                raw_payload={
                    "text": candidate.text,
                },
                canonical_payload={
                    "text": candidate.text,
                },
            )

            # -------------------------------------------------
            # NORMALIZATION
            # -------------------------------------------------

            normalization = normalizer.normalize([raw_record])

            normalized = None

            if normalization.records and is_accepted:
                normalized = normalization.records[0]

            results.append(
                CorpusValidationResult(
                    raw_question=(candidate.text),
                    technical_result=(technical_result),
                    normalized_record=(normalized),
                )
            )

        return results
