# services/question_intelligence/quality/contracts/diversity_report.py

from pydantic import BaseModel


class DiversityReport(BaseModel):

    diversity_score: float
