# services/question_intelligence/balancing/balancing_issue.py

from pydantic import BaseModel


class BalancingIssue(BaseModel):

    dimension: str

    value: str

    count: int

    severity: str

    recommendation: str

    model_config = {
        "frozen": True,
    }
