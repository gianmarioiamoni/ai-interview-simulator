# domain/contracts/question/question_bank_item.py

from pydantic import BaseModel, Field

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import Role
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.question.question_provenance import QuestionProvenance

from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


class QuestionBankItem(BaseModel):
    id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)

    interview_type: InterviewType
    role: Role
    area: InterviewArea

    level: SeniorityLevel
    difficulty: int = Field(..., ge=1, le=5)

    ingestion_metadata: IngestionMetadata
    provenance: QuestionProvenance | None = None


    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
