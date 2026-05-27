# services/question_ingestion/diagnostics/ingestion_diagnostics_report.py

from pydantic import BaseModel, Field


class IngestionDiagnosticsReport(BaseModel):

    # =====================================================
    # DATASET METADATA
    # =====================================================

    dataset_name: str

    source_type: str

    adapter_name: str

    # =====================================================
    # PIPELINE COUNTS
    # =====================================================

    loaded_records: int = 0

    normalized_records: int = 0

    classified_records: int = 0

    mapped_records: int = 0

    indexed_records: int = 0

    # =====================================================
    # QUALITY / FILTERING
    # =====================================================

    duplicate_records: int = 0

    average_quality_score: float = 0.0

    average_similarity: float = 0.0

    # =====================================================
    # SKIPS
    # =====================================================

    skipped_missing_area: int = 0

    skipped_missing_level: int = 0

    skipped_invalid_role: int = 0

    skipped_unknown: int = 0

    # =====================================================
    # ERRORS
    # =====================================================

    errors: list[str] = Field(default_factory=list)

    success: bool = True

    # =====================================================
    # TIMING
    # =====================================================

    ingestion_duration_seconds: float = 0.0

    
    model_config = {
        "frozen": True,
    }
