# domain/contracts/evaluation_report.py

from pydantic import BaseModel, Field, model_validator

from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.confidence import Confidence


class EvaluationReport(BaseModel):
    interview_id: str = Field(..., min_length=1)
    total_score: float = Field(..., ge=0.0, le=100.0)
    passed: bool
    feedback: str = Field(..., min_length=1)
    evaluations: list[QuestionEvaluation] = Field(default_factory=list)
    confidence: Confidence

    @model_validator(mode="after")
    def validate_consistency(self) -> "EvaluationReport":
        if not self.evaluations:
            raise ValueError("EvaluationReport must contain at least one evaluation")
        return self

    model_config = {"frozen": True}
