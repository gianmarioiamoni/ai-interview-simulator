# services/question_corpus/validations/contracts/corpus_validation_issue.py

from pydantic import BaseModel


class CorpusValidationIssue(BaseModel):

    severity: str

    category: str

    message: str

    question_id: str | None = None

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
