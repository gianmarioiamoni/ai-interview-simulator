# services/question_intelligence/interview_coherence_metrics.py

from typing import List

from domain.contracts.question.question import Question

from services.question_intelligence.coverage.topic_extractor import TopicExtractor
from services.question_intelligence.interview_theme_memory import get_interview_theme_anchor
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.quality.similarity_engine import SimilarityEngine


class InterviewCoherenceMetrics:

    _COHERENT_THRESHOLD = 0.35
    _FRAGMENTED_THRESHOLD = 0.20

    def __init__(
        self,
        similarity_engine: SimilarityEngine | None = None,
        topic_extractor: TopicExtractor | None = None,
    ) -> None:

        self._similarity_engine = (
            similarity_engine if similarity_engine is not None else SimilarityEngine()
        )
        self._topic_extractor = (
            topic_extractor if topic_extractor is not None else TopicExtractor()
        )

    def compute(
        self,
        questions: List[Question],
        memory: InterviewRetrievalMemory | None = None,
    ) -> dict[str, float | str | bool]:

        similarity = self._similarity_engine.compute_metrics(questions)
        coherence_score = similarity.average_similarity

        theme_anchor = (
            get_interview_theme_anchor(memory)
            if memory is not None
            else None
        )

        theme_consistency = self._compute_theme_consistency(
            questions=questions,
            theme_anchor=theme_anchor,
        )

        domain_continuity = self._compute_domain_continuity(questions)

        return {
            "coherence_score": round(coherence_score, 4),
            "theme_anchor": theme_anchor or "",
            "theme_consistency": round(theme_consistency, 4),
            "domain_continuity": round(domain_continuity, 4),
            "is_coherent": coherence_score >= self._COHERENT_THRESHOLD,
            "is_fragmented": coherence_score < self._FRAGMENTED_THRESHOLD,
        }

    def _compute_theme_consistency(
        self,
        questions: List[Question],
        theme_anchor: str | None,
    ) -> float:

        if not questions or not theme_anchor:
            return 0.0

        aligned = 0
        readable = theme_anchor.replace("_", " ")

        for question in questions:
            lower = question.prompt.lower()
            topic = self._topic_extractor.extract(question.prompt)

            if (
                theme_anchor in lower
                or readable in lower
                or topic in theme_anchor
                or theme_anchor in topic
            ):
                aligned += 1

        return aligned / len(questions)

    def _compute_domain_continuity(
        self,
        questions: List[Question],
    ) -> float:

        if len(questions) < 2:
            return 0.0

        topics = [
            self._topic_extractor.extract(question.prompt)
            for question in questions
        ]

        non_other = [topic for topic in topics if topic != "other"]

        if not non_other:
            return 0.0

        dominant = max(set(non_other), key=non_other.count)
        shared = sum(1 for topic in non_other if topic == dominant)

        return shared / len(questions)
