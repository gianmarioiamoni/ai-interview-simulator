# services/question_ingestion/contracts/corpus_onboarding_result.py

from pydantic import BaseModel

from services.question_ingestion.contracts import (
    CorpusValidationResult,
)


class CorpusOnboardingResult(BaseModel):

    repository_name: str

    total_questions: int

    accepted_questions: int

    rejected_questions: int

    average_score: float

    accepted_results: list[CorpusValidationResult]

    rejected_results: list[CorpusValidationResult]

    onboarding_decision: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
