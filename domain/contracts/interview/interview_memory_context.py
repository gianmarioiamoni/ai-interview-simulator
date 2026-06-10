# domain/contracts/interview/interview_memory_context.py

from pydantic import BaseModel, Field

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType

from domain.contracts.interview.retrieval_adaptation_signal import RetrievalAdaptationSignal


class InterviewMemoryContext(BaseModel):

    covered_areas: list[InterviewArea] = Field(default_factory=list)

    covered_concepts: list[str] = Field(default_factory=list)

    weak_dimensions: list[PerformanceDimensionType] = Field(default_factory=list)

    previous_failures: list[str] = Field(default_factory=list)

    retrieval_history: list[str] = Field(default_factory=list)

    follow_up_history: list[str] = Field(default_factory=list)

    retrieval_adaptation: RetrievalAdaptationSignal = Field(default_factory=RetrievalAdaptationSignal)

    
    model_config = {
        "frozen": True,
    }
