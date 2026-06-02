# services/question_ingestion/adapters/huggingface_backend_adapter.py

from services.question_ingestion.adapters.dataset_adapter import DatasetAdapter
from services.question_ingestion.contracts import RawQuestionRecord


BACKEND_AREA = "technical_case_study"
BACKEND_ROLE = "backend_engineer"
BACKEND_LEVEL = "senior"


class HuggingFaceBackendAdapter(DatasetAdapter):

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
            "area": BACKEND_AREA,
            "role": BACKEND_ROLE,
            "level": BACKEND_LEVEL,
        }

        return RawQuestionRecord(
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
            canonical_payload=canonical_payload,
            raw_payload=payload,
        )
