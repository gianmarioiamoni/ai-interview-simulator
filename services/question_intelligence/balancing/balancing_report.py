# services/question_intelligence/balancing/balancing_report.py

from pydantic import BaseModel

from services.question_intelligence.balancing.balancing_issue import (
    BalancingIssue,
)


class BalancingReport(BaseModel):

    total_issues: int

    issues: list[BalancingIssue]

    model_config = {
        "frozen": True,
    }
