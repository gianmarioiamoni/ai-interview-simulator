# services/question_ingestion/contracts/corpus_validation_result.py

from pydantic import BaseModel

from services.question_ingestion.contracts import NormalizedQuestionRecord
from services.question_intelligence.quality.contracts import TechnicalFilterResult
from services.question_ingestion.contracts.candidate_question import CandidateQuestion


class CorpusValidationResult(BaseModel):

    raw_question: str

    technical_result: TechnicalFilterResult

    normalized_record: NormalizedQuestionRecord | None

    candidate: CandidateQuestion


    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
