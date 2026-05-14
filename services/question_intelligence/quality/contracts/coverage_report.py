# services/question_intelligence/quality/contracts/coverage_report.py

from pydantic import BaseModel


class CoverageReport(BaseModel):

    area_coverage_score: float
    difficulty_balance_score: float
