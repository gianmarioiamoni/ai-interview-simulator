# SemanticDeduplicator
#
# Responsibility:
# Removes semantically similar questions using embeddings similarity.

from typing import List
import numpy as np

from domain.contracts.question.question import Question
from infrastructure.embeddings.embedding_factory import get_embedding_model

from app.settings.constants import DEDUPLICATION_THRESHOLD


class SemanticDeduplicator:

    def __init__(self, threshold: float = DEDUPLICATION_THRESHOLD) -> None:
        self._embedding_model = get_embedding_model()
        self._threshold = threshold 

    # ---------------------------------------------------------

    def deduplicate(self, questions: List[Question]) -> List[Question]:

        if not questions:
            return questions

        embeddings = self._embedding_model.embed_documents(
            [q.prompt for q in questions]
        )

        kept_questions: List[Question] = []
        kept_embeddings: List[np.ndarray] = []

        for q, emb in zip(questions, embeddings):

            if not kept_embeddings:
                kept_questions.append(q)
                kept_embeddings.append(np.array(emb))
                continue

            if not self._is_duplicate(np.array(emb), kept_embeddings):
                kept_questions.append(q)
                kept_embeddings.append(np.array(emb))

        return kept_questions

    # ---------------------------------------------------------

    def _is_duplicate(
        self,
        emb: np.ndarray,
        existing_embeddings: List[np.ndarray],
    ) -> bool:

        for e in existing_embeddings:
            similarity = self._cosine_similarity(emb, e)

            if similarity >= self._threshold:
                return True

        return False

    # ---------------------------------------------------------

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
