# services/question_ingestion/adapters/huggingface_database_adapter.py

from services.question_ingestion.adapters.huggingface_dataset_adapter import (
    HuggingFaceDatasetAdapter,
)


DATABASE_AREA = "technical_database"
DATABASE_ROLE = "backend_engineer"
DATABASE_LEVEL = "mid"


class HuggingFaceDatabaseAdapter(HuggingFaceDatasetAdapter):

    AREA = DATABASE_AREA
    ROLE = DATABASE_ROLE
    LEVEL = DATABASE_LEVEL
