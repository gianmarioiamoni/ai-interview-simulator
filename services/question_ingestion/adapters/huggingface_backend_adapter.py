# services/question_ingestion/adapters/huggingface_backend_adapter.py

from services.question_ingestion.adapters.huggingface_dataset_adapter import (
    HuggingFaceDatasetAdapter,
)


BACKEND_AREA = "technical_case_study"
BACKEND_ROLE = "backend_engineer"
BACKEND_LEVEL = "senior"


class HuggingFaceBackendAdapter(HuggingFaceDatasetAdapter):

    AREA = BACKEND_AREA
    ROLE = BACKEND_ROLE
    LEVEL = BACKEND_LEVEL
