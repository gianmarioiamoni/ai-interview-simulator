# services/interview_selection/policy_scorer.py

"""
Scores a QuestionBankItem against an InterviewPolicy.

Extracted from AdaptiveInterviewAssembler._policy_score() to give the
scoring vocabulary (keyword sets, area constants, weight increments) a
single home, separating policy interpretation from assembly orchestration.
"""

from domain.contracts.question.question_bank_item import QuestionBankItem
from services.interview_policy.interview_policy import InterviewPolicy

_ARCHITECTURE_AREA = "technical_case_study"

_SCALABILITY_KEYWORDS: frozenset[str] = frozenset(
    {"scaling", "distributed", "replication", "sharding", "consistency"}
)

_PRODUCTION_KEYWORDS: frozenset[str] = frozenset(
    {"production", "deployment", "pipeline", "performance", "monitoring"}
)

_PREFERRED_AREA_WEIGHT = 1.0
_ARCHITECTURE_WEIGHT = 0.5
_SCALABILITY_WEIGHT = 0.5
_PRODUCTION_WEIGHT = 0.5


class PolicyScorer:
    """
    Computes a relevance score for a question item relative to an
    InterviewPolicy. Stateless — safe to share across requests.
    """

    def score(self, item: QuestionBankItem, policy: InterviewPolicy) -> float:
        result = 0.0

        if item.area.value in policy.preferred_areas:
            result += _PREFERRED_AREA_WEIGHT

        if policy.prioritize_architecture and item.area.value == _ARCHITECTURE_AREA:
            result += _ARCHITECTURE_WEIGHT

        if policy.prioritize_scalability:
            lower = item.text.lower()
            if any(k in lower for k in _SCALABILITY_KEYWORDS):
                result += _SCALABILITY_WEIGHT

        if policy.prioritize_production_experience:
            lower = item.text.lower()
            if any(k in lower for k in _PRODUCTION_KEYWORDS):
                result += _PRODUCTION_WEIGHT

        return result
