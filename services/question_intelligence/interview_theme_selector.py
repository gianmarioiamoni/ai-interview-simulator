# services/question_intelligence/interview_theme_selector.py

from __future__ import annotations

from collections import Counter

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_intelligence.clustering.semantic_clustering_engine import (
    SemanticClusteringEngine,
)
from services.question_intelligence.coverage.topic_extractor import TopicExtractor
from services.question_intelligence.interview_corpus_theme_stats import (
    compute_technical_thematic_domain_counts,
    load_preview_texts_for_area,
)


class InterviewThemeSelector:

    _TOPIC_ALIGNMENT_BOOST = 2
    _TEXT_ALIGNMENT_BOOST = 3
    _CLUSTER_ALIGNMENT_BOOST = 4

    def __init__(
        self,
        topic_extractor: TopicExtractor | None = None,
        clustering_engine: SemanticClusteringEngine | None = None,
    ) -> None:

        self._topic_extractor = (
            topic_extractor if topic_extractor is not None else TopicExtractor()
        )
        self._clustering_engine = (
            clustering_engine
            if clustering_engine is not None
            else SemanticClusteringEngine()
        )

    def select_anchor(
        self,
        role: RoleType,
        level: SeniorityLevel,
        first_area: InterviewArea,
        preview_items: list[QuestionBankItem] | None = None,
    ) -> str:

        corpus_counts = compute_technical_thematic_domain_counts()
        scores: Counter[str] = Counter(corpus_counts)

        preview_texts = self._collect_preview_texts(
            first_area=first_area,
            preview_items=preview_items,
        )

        self._apply_topic_votes(
            scores=scores,
            preview_texts=preview_texts,
        )

        self._apply_text_votes(
            scores=scores,
            preview_texts=preview_texts,
        )

        if preview_items:
            self._apply_cluster_vote(
                scores=scores,
                preview_items=preview_items,
            )

        _ = role, level

        if not scores:
            corpus_only = compute_technical_thematic_domain_counts()

            if corpus_only:
                return max(corpus_only, key=corpus_only.get)

            return "general"

        return scores.most_common(1)[0][0]

    def _collect_preview_texts(
        self,
        first_area: InterviewArea,
        preview_items: list[QuestionBankItem] | None,
    ) -> list[str]:

        texts = [item.text for item in preview_items] if preview_items else []

        if not texts:
            texts = load_preview_texts_for_area(first_area)

        return texts

    def _apply_topic_votes(
        self,
        scores: Counter[str],
        preview_texts: list[str],
    ) -> None:

        for text in preview_texts:
            topic = self._topic_extractor.extract(text)

            if topic == "other":
                continue

            for theme in list(scores.keys()):
                if self._topic_aligns_with_theme(topic, theme):
                    scores[theme] += self._TOPIC_ALIGNMENT_BOOST

    def _apply_text_votes(
        self,
        scores: Counter[str],
        preview_texts: list[str],
    ) -> None:

        for text in preview_texts:
            lower = text.lower()

            for theme in list(scores.keys()):
                if theme.replace("_", " ") in lower or theme in lower:
                    scores[theme] += self._TEXT_ALIGNMENT_BOOST

    def _apply_cluster_vote(
        self,
        scores: Counter[str],
        preview_items: list[QuestionBankItem],
    ) -> None:

        report = self._clustering_engine.cluster(preview_items[:20])

        if not report.clusters:
            return

        largest = max(
            report.clusters,
            key=lambda cluster: len(cluster.members),
        )

        centroid_text = largest.centroid_text

        topic = self._topic_extractor.extract(centroid_text)

        for theme in list(scores.keys()):
            if theme.replace("_", " ") in centroid_text.lower() or theme in centroid_text.lower():
                scores[theme] += self._CLUSTER_ALIGNMENT_BOOST
                continue

            if topic != "other" and self._topic_aligns_with_theme(topic, theme):
                scores[theme] += self._CLUSTER_ALIGNMENT_BOOST

    def _topic_aligns_with_theme(
        self,
        topic: str,
        theme: str,
    ) -> bool:

        return topic in theme or theme in topic
