# services/question_intelligence/coverage/coverage_analyzer.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.coverage.coverage_bucket import (
    CoverageBucket,
)

from services.question_intelligence.coverage.coverage_report import (
    CoverageReport,
)

from services.question_intelligence.coverage.topic_extractor import (
    TopicExtractor,
)


class CoverageAnalyzer:

    def __init__(self) -> None:

        self._topic_extractor = TopicExtractor()

    # =====================================================
    # PUBLIC
    # =====================================================

    def analyze(
        self,
        items: List[QuestionBankItem],
    ) -> CoverageReport:

        buckets: dict[str, list[str]] = {}

        for item in items:

            topic = self._topic_extractor.extract(
                item.text,
            )

            if topic not in buckets:
                buckets[topic] = []

            buckets[topic].append(item.text)

        coverage_buckets = [
            CoverageBucket(
                topic=topic,
                questions=questions,
            )
            for topic, questions in buckets.items()
        ]

        bucket_sizes = [len(bucket.questions) for bucket in coverage_buckets]

        largest_bucket = max(bucket_sizes)

        distribution_score = round(
            len(coverage_buckets) / len(items),
            2,
        )

        return CoverageReport(
            total_questions=len(items),
            total_topics=len(coverage_buckets),
            largest_topic_size=largest_bucket,
            topic_distribution_score=distribution_score,
            buckets=coverage_buckets,
        )
