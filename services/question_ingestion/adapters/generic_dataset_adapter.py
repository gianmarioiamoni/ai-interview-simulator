# services/question_ingestion/adapters/generic_dataset_adapter.py

from services.question_ingestion.adapters.dataset_adapter import (
    DatasetAdapter,
)

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)


class GenericDatasetAdapter(DatasetAdapter):

    # =====================================================
    # PUBLIC
    # =====================================================

    # TODO:
    # support schema-specific adapters
    # support HuggingFace datasets
    # support semantic field mapping

    def adapt(
        self,
        payload: dict,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> RawQuestionRecord:

        return RawQuestionRecord(
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
            raw_payload=payload,
        )
