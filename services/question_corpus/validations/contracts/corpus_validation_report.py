# services/question_corpus/validations/corpus_validation_report.py

from pydantic import BaseModel

from services.question_corpus.validations.contracts.corpus_validation_issue import CorpusValidationIssue


class CorpusValidationReport(BaseModel):

    total_questions: int

    total_issues: int

    issues: list[CorpusValidationIssue]

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
