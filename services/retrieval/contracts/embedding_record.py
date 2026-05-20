# services/retrieval/contracts/embedding_record.py

from pydantic import BaseModel

from services.retrieval.contracts import (
    RetrievalCorpusRecord,
)


class EmbeddingRecord(BaseModel):

    content: str

    embedding: list[float]

    retrieval_record: RetrievalCorpusRecord

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
