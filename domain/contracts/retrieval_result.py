# domain/contracts/retrieval_result.py

from pydantic import BaseModel, Field
from typing import List

from domain.contracts.retrieval_document import RetrievalDocument


class RetrievalResult(BaseModel):
    documents: List[RetrievalDocument] = Field(default_factory=list)

    model_config = {"frozen": True}
