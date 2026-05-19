# services/question_ingestion/adapters/huggingface_qa_adapter.py

from services.question_ingestion.adapters.dataset_adapter import (
    DatasetAdapter,
)

from services.question_ingestion.contracts import (
    RawQuestionRecord,
)


class HuggingFaceQAAdapter(DatasetAdapter):

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
            "text": (
                payload.get("question")
                or payload.get("prompt")
                or payload.get("instruction")
                or ""
            ),
            "role": "backend_engineer",
            "area": ("technical_technical_knowledge"),
            "level": "mid",
            "difficulty": 3,
        }

        return RawQuestionRecord(
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
            canonical_payload=canonical_payload,
            raw_payload=payload,
        )
