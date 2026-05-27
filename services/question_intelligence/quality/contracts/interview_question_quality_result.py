# services/question_intelligence/quality/contracts/interview_question_quality_result.py

from pydantic import BaseModel

from services.question_intelligence.quality.contracts.quality_decision import QualityDecision


class InterviewQuestionQualityResult(BaseModel):

    decision: QualityDecision

    score: float

    quality_signals: list[str]

    penalties: list[str]

    is_context_dependent: bool

    is_interview_style: bool

    is_actionable: bool

    model_config = {
        "frozen": True,
    }
