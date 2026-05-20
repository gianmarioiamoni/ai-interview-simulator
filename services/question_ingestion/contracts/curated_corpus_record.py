# services/question_ingestion/contracts/curated_corpus_record.py

from pydantic import BaseModel

from services.question_ingestion.contracts import (
    NormalizedQuestionRecord,
)


class CuratedCorpusRecord(BaseModel):

    question: NormalizedQuestionRecord

    semantic_score: float

    matched_categories: list[str]

    matched_terms: list[str]

    source_repository: str

    onboarding_decision: str

    corpus_version: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
