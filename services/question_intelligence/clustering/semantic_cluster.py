# services/question_intelligence/clustering/semantic_cluster.py

from pydantic import BaseModel

from typing import List


class SemanticCluster(BaseModel):

    cluster_id: int

    centroid_text: str

    members: List[str]

    average_similarity: float

    model_config = {
        "frozen": True,
    }
