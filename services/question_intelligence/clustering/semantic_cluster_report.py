# services/question_intelligence/clustering/semantic_cluster_report.py

from pydantic import BaseModel

from typing import List

from services.question_intelligence.clustering.semantic_cluster import (
    SemanticCluster,
)


class SemanticClusterReport(BaseModel):

    total_documents: int

    total_clusters: int

    largest_cluster_size: int

    average_cluster_size: float

    clusters: List[SemanticCluster]

    model_config = {
        "frozen": True,
    }
