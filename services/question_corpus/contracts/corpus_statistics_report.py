# services/question_corpus/contracts/corpus_statistics_report.py

from pydantic import BaseModel


class CorpusStatisticsReport(BaseModel):

    total_questions: int

    roles_distribution: dict[str, int]

    areas_distribution: dict[str, int]

    domains_distribution: dict[str, int]

    difficulty_distribution: dict[int, int]

    average_quality_score: float

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
