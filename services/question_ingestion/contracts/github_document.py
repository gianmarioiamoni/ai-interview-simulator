# services/question_ingestion/contracts/github_document.py

from pydantic import BaseModel


class GitHubDocument(BaseModel):

    path: str

    content: str

    repository: str

    branch: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
