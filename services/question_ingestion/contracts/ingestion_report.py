# services/question_ingestion/contracts/ingestion_report.py

from pydantic import BaseModel


class IngestionReport(BaseModel):

    total_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0

    duplicate_records: int = 0

    ingestion_duration_seconds: float = 0.0

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
