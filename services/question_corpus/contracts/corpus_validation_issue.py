# services/question_corpus/contracts/corpus_validation_issue.py

from pydantic import BaseModel


class CorpusValidationIssue(BaseModel):

    question_id: str

    issue_type: str

    description: str

    severity: str

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
