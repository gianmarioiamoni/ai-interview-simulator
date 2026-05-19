# services/question_ingestion/adapters/system_design_dataset_adapter.py

from services.question_ingestion.adapters.dataset_adapter import (
    DatasetAdapter,
)

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)


class SystemDesignDatasetAdapter(DatasetAdapter):

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt(
        self,
        payload: dict,
        source: str,
        source_type: str,
        dataset_version: str,
    ) -> RawQuestionRecord:

        canonical_payload = {
            "text": payload.get("prompt"),
            "role": payload.get("role"),
            "area": payload.get("area"),
            "level": payload.get("level"),
            "difficulty": payload.get("difficulty"),
        }

        return RawQuestionRecord(
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
            canonical_payload=canonical_payload,
            raw_payload=payload,
        )
