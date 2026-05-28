# services/question_corpus/contracts/corpus_statistics.py

from pydantic import BaseModel


class CorpusStatistics(BaseModel):

    total_questions: int

    total_roles: int

    total_areas: int

    total_domains: int

    average_quality_score: float

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
