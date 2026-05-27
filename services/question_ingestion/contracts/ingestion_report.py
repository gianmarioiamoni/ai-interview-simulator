# services/question_ingestion/contracts/ingestion_report.py

from pydantic import BaseModel, Field


class IngestionReport(BaseModel):

    # =====================================================
    # DATASET METADATA
    # =====================================================

    dataset_name: str

    source_type: str

    adapter_name: str

    # =====================================================
    # RAW INGESTION
    # =====================================================

    total_records: int = 0

    adapted_records: int = 0

    normalized_records: int = 0

    mapped_records: int = 0

    # =====================================================
    # QUALITY
    # =====================================================

    valid_records: int = 0

    rejected_records: int = 0

    duplicate_records: int = 0

    average_quality_score: float = 0.0

    average_similarity: float = 0.0

    # =====================================================
    # INDEXING
    # =====================================================

    indexed_records: int = 0

    # =====================================================
    # ERRORS
    # =====================================================

    errors: list[str] = Field(default_factory=list)

    # =====================================================
    # TIMING
    # =====================================================

    ingestion_duration_seconds: float = 0.0

    # =====================================================
    # STATUS
    # =====================================================

    success: bool = True

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
