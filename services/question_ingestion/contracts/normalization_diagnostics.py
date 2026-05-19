# services/question_ingestion/contracts/normalization_diagnostics.py

from pydantic import BaseModel


class NormalizationDiagnostics(BaseModel):

    total_records: int = 0

    normalized_records: int = 0

    filtered_non_technical: int = 0

    rejected_missing_text: int = 0

    rejected_invalid_text: int = 0

    rejected_too_short: int = 0

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
