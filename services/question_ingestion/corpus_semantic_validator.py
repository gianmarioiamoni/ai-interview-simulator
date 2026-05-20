# services/question_ingestion/corpus_semantic_validator.py

from services.question_ingestion.contracts import (
    RawQuestionRecord,
    CorpusValidationResult,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)

from services.question_intelligence.technical_question_filter import (
    TechnicalQuestionFilter,
)


class CorpusSemanticValidator:

    # =====================================================
    # PUBLIC
    # =====================================================

    def validate(
        self,
        questions: list[str],
        source_name: str,
        source_type: str,
        dataset_version: str,
    ) -> list[CorpusValidationResult]:

        filter_service = TechnicalQuestionFilter()

        normalizer = QuestionNormalizer()

        results: list[CorpusValidationResult] = []

        for question in questions:

            # -------------------------------------------------
            # SEMANTIC EVALUATION
            # -------------------------------------------------

            filter_result = filter_service.evaluate(question)

            # -------------------------------------------------
            # RAW RECORD
            # -------------------------------------------------

            raw_record = RawQuestionRecord(
                source=source_name,
                source_type=(source_type),
                dataset_version=(dataset_version),
                raw_payload={
                    "text": question,
                },
                canonical_payload={
                    "text": question,
                },
            )

            # -------------------------------------------------
            # NORMALIZATION
            # -------------------------------------------------

            normalization = normalizer.normalize([raw_record])

            normalized = None

            if normalization.records:
                normalized = normalization.records[0]

            results.append(
                CorpusValidationResult(
                    raw_question=(question),
                    filter_result=(filter_result),
                    normalized_record=(normalized),
                )
            )

        return results
