# services/question_intelligence/coverage/coverage_report.py

from pydantic import BaseModel

from typing import List

from services.question_intelligence.coverage.coverage_bucket import (
    CoverageBucket,
)


class CoverageReport(BaseModel):

    total_questions: int

    total_topics: int

    largest_topic_size: int

    topic_distribution_score: float

    buckets: List[CoverageBucket]

    model_config = {
        "frozen": True,
    }
