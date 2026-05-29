# services/question_corpus/contracts/retrieval_document.py

from pydantic import BaseModel


class RetrievalDocument(BaseModel):

    document_id: str

    text: str

    metadata: dict[str, str | int | float | list[str]]

    embedding: list[float]

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
