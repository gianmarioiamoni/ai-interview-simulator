# services/question_ingestion/contracts/normalization_result.py

from pydantic import BaseModel

from services.question_ingestion.contracts import (
    NormalizedQuestionRecord,
)

from services.question_ingestion.contracts.normalization_diagnostics import (
    NormalizationDiagnostics,
)


class NormalizationResult(BaseModel):

    records: list[NormalizedQuestionRecord]

    diagnostics: NormalizationDiagnostics

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
