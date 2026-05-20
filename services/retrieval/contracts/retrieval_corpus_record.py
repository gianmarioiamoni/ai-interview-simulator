# services/retrieval/contracts/retrieval_corpus_record.py

from pydantic import BaseModel

from services.question_ingestion.contracts import (
    CuratedCorpusRecord,
)


class RetrievalCorpusRecord(BaseModel):

    content: str

    retrieval_tags: list[str]

    retrieval_score: float

    source_repository: str

    corpus_version: str

    semantic_categories: list[str]

    original_record: CuratedCorpusRecord

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
