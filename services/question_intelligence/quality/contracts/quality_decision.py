# services/question_intelligence/quality/contracts/quality_decision.py

from enum import Enum


class QualityDecision(str, Enum):

    APPROVE = "approve"

    REVIEW = "review"

    REJECT = "reject"
