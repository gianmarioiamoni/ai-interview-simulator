# services/question_intelligence/clustering/semantic_clustering_engine.py

from typing import List

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.semantic.embedding_similarity_engine import (
    EmbeddingSimilarityEngine,
)

from services.question_intelligence.clustering.semantic_cluster import (
    SemanticCluster,
)

from services.question_intelligence.clustering.semantic_cluster_report import (
    SemanticClusterReport,
)


class SemanticClusteringEngine:

    #DEFAULT_THRESHOLD = 0.72
    DEFAULT_THRESHOLD = 0.55

    def __init__(self) -> None:

        self._similarity_engine = EmbeddingSimilarityEngine()

    # =====================================================
    # PUBLIC
    # =====================================================

    def cluster(
        self,
        items: List[QuestionBankItem],
        threshold: float = DEFAULT_THRESHOLD,
    ) -> SemanticClusterReport:

        clusters: List[List[QuestionBankItem]] = []

        for item in items:

            assigned = False

            for cluster in clusters:

                centroid = cluster[0]

                similarity = self._similarity_engine.similarity(
                    item.text,
                    centroid.text,
                )

                if similarity >= threshold:

                    cluster.append(item)

                    assigned = True

                    break

            if not assigned:

                clusters.append([item])

        semantic_clusters: List[SemanticCluster] = []

        for idx, cluster in enumerate(clusters):

            similarities = []

            centroid = cluster[0]

            for member in cluster[1:]:

                sim = self._similarity_engine.similarity(
                    centroid.text,
                    member.text,
                )

                similarities.append(sim)

            avg_similarity = (
                sum(similarities) / len(similarities) if similarities else 1.0
            )

            semantic_clusters.append(
                SemanticCluster(
                    cluster_id=idx + 1,
                    centroid_text=centroid.text,
                    members=[item.text for item in cluster],
                    average_similarity=round(
                        avg_similarity,
                        2,
                    ),
                )
            )

        cluster_sizes = [len(c.members) for c in semantic_clusters]

        return SemanticClusterReport(
            total_documents=len(items),
            total_clusters=len(semantic_clusters),
            largest_cluster_size=max(cluster_sizes),
            average_cluster_size=round(
                sum(cluster_sizes) / len(cluster_sizes),
                2,
            ),
            clusters=semantic_clusters,
        )
