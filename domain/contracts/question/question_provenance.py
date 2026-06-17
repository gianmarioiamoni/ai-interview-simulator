from pydantic import BaseModel

from domain.contracts.question.question_origin_type import (
    QuestionOriginType,
)


class QuestionProvenance(BaseModel):

    origin_type: QuestionOriginType

    source_name: str | None = None

    source_type: str | None = None

    dataset_version: str | None = None

    retrieval_query: str | None = None

    retrieval_score: float | None = None

    generated_by_model: str | None = None

    recovery_expansion: bool = False

    domains: list[str] = []

    model_config = {
        "frozen": True,
    }
