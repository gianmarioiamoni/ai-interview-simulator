# domain/contracts/question/question_provenance.py

from pydantic import BaseModel, Field

from domain.contracts.question.question_origin_type import (
    QuestionOriginType,
)


class QuestionProvenance(BaseModel):

    origin_type: QuestionOriginType

    source_name: str | None = None

    source_version: str | None = None

    retrieval_strategy: str | None = None

    generator_model: str | None = None

    humanized: bool = False

    transformation_history: list[str] = Field(
        default_factory=list,
    )

    model_config = {
        "frozen": True,
    }
