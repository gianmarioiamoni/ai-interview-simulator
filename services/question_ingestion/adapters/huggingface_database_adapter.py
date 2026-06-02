# services/question_ingestion/adapters/huggingface_database_adapter.py

from services.question_ingestion.adapters.dataset_adapter import DatasetAdapter
from services.question_ingestion.contracts import RawQuestionRecord


DATABASE_AREA = "technical_database"
DATABASE_ROLE = "backend_engineer"
DATABASE_LEVEL = "mid"


class HuggingFaceDatabaseAdapter(DatasetAdapter):

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
            "area": DATABASE_AREA,
            "role": DATABASE_ROLE,
            "level": DATABASE_LEVEL,
        }

        return RawQuestionRecord(
            source=source,
            source_type=source_type,
            dataset_version=dataset_version,
            canonical_payload=canonical_payload,
            raw_payload=payload,
        )
