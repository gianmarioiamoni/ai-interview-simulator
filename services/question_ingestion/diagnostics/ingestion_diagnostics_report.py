# services/question_ingestion/diagnostics/ingestion_diagnostics_report.py

from pydantic import BaseModel, Field


class IngestionDiagnosticsReport(BaseModel):

    loaded_records: int = 0

    normalized_records: int = 0

    classified_records: int = 0

    mapped_records: int = 0

    indexed_records: int = 0

    skipped_missing_area: int = 0

    skipped_missing_level: int = 0

    skipped_invalid_role: int = 0

    skipped_unknown: int = 0

    model_config = {
        "frozen": True,
    }
