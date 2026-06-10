# domain/contracts/interview/retrieval_adaptation_signal.py

from pydantic import BaseModel, Field

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.shared.performance_dimension_type import (
    PerformanceDimensionType,
)


class RetrievalAdaptationSignal(BaseModel):

    weak_areas: list[InterviewArea] = Field(default_factory=list)

    weak_dimensions: list[PerformanceDimensionType] = Field(default_factory=list)

    low_confidence: bool = False

    repeated_failures: bool = False

    model_config = {
        "frozen": True,
    }
