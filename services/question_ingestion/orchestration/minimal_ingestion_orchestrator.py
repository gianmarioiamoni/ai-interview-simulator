# services/question_ingestion/orchestration/minimal_ingestion_orchestrator.py

from domain.contracts.corpus.curated_question import CuratedQuestion

from services.question_ingestion.classifiers.question_metadata_classifier import (
    QuestionMetadataClassifier,
)
from services.question_ingestion.contracts.normalized_question_record import (
    NormalizedQuestionRecord,
)
from services.question_ingestion.contracts.question_metadata import QuestionMetadata
from services.question_ingestion.contracts.raw_question_record import RawQuestionRecord
from services.question_ingestion.mappers.curated_question_mapper import (
    CuratedQuestionMapper,
    CuratedQuestionMappingError,
)
from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)


class MinimalIngestionOrchestrator:

    def __init__(
        self,
        normalizer: QuestionNormalizer | None = None,
        classifier: QuestionMetadataClassifier | None = None,
        mapper: CuratedQuestionMapper | None = None,
    ) -> None:

        self._normalizer = normalizer if normalizer is not None else QuestionNormalizer()

        self._classifier = (
            classifier if classifier is not None else QuestionMetadataClassifier()
        )

        self._mapper = mapper if mapper is not None else CuratedQuestionMapper()

    # =====================================================
    # PUBLIC
    # =====================================================

    def ingest(
        self,
        raw_records: list[RawQuestionRecord],
    ) -> list[CuratedQuestion]:

        normalization = self._normalizer.normalize(raw_records)

        classified = self._classifier.classify(normalization.records)

        curated_questions: list[CuratedQuestion] = []

        for record in classified:

            mapped = self._map_record(record)

            if mapped is not None:
                curated_questions.append(mapped)

        return curated_questions

    # =====================================================
    # INTERNALS
    # =====================================================

    def _map_record(
        self,
        record: NormalizedQuestionRecord,
    ) -> CuratedQuestion | None:

        metadata = QuestionMetadata(
            role=record.role_hint,
            area=record.area_hint,
            level=record.level_hint,
            difficulty=record.difficulty_hint,
        )

        try:
            return self._mapper.map(
                record=record,
                metadata=metadata,
            )

        except CuratedQuestionMappingError:
            return None
