# services/question_ingestion/adapters/huggingface_dataset_adapter.py

from services.question_ingestion.adapters.dataset_adapter import DatasetAdapter
from services.question_ingestion.contracts import RawQuestionRecord


class HuggingFaceDatasetAdapter(DatasetAdapter):

    AREA: str
    ROLE: str
    LEVEL: str

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

        instruction = payload.get("instruction", "")

        if not isinstance(instruction, str):
            instruction = str(instruction)

        instruction = instruction.strip()

        canonical_payload = {
            "text": instruction,
            "area": self.AREA,
            "role": self.ROLE,
            "level": self.LEVEL,
        }

        return RawQuestionRecord(
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
            canonical_payload=canonical_payload,
            raw_payload=payload,
        )
