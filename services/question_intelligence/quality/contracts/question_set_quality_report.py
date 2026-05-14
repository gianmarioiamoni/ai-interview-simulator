# services/question_intelligence/quality/contracts/question_set_quality_report.py

from pydantic import BaseModel

from services.question_intelligence.quality.contracts.similarity_metrics import (
    SimilarityMetrics,
)

from services.question_intelligence.quality.contracts.diversity_report import (
    DiversityReport,
)

from services.question_intelligence.quality.contracts.coverage_report import (
    CoverageReport,
)


class QuestionSetQualityReport(BaseModel):

    similarity: SimilarityMetrics
    diversity: DiversityReport
    coverage: CoverageReport
