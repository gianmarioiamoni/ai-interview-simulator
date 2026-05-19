# services/question_intelligence/corpus/corpus_diagnostics_report.py

from pydantic import BaseModel


class CorpusDiagnosticsReport(BaseModel):

    total_questions: int

    unique_questions: int

    duplicate_questions: int

    duplicate_ratio: float

    role_distribution: dict[str, int]

    level_distribution: dict[str, int]

    area_distribution: dict[str, int]

    source_distribution: dict[str, int]

    model_config = {
        "frozen": True,
    }
