# domain/contracts/retrieval_document.py

# Retrieval document contract
#
# This contract defines the structure of a retrieval document that can be used in the interview simulator.
# It is used to store the retrieval document in the database and to retrieve it when needed.
#
# The retrieval document is associated with a question and contains the retrieval document.
# The retrieval document also contains the content and the metadata.
#

from pydantic import BaseModel, Field

from domain.contracts.retrieval_metadata import RetrievalMetadata


class RetrievalDocument(BaseModel):
    id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: RetrievalMetadata

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
