# services/question_corpus/retrieval/diversity_reranker.py

from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from infrastructure.embeddings.embedding_similarity_engine import EmbeddingSimilarityEngine

from app.core.logger import get_logger

logger = get_logger(__name__)


class DiversityReranker:

    REDUNDANCY_WEIGHT = 0.45

    REDUNDANCY_CAP = 0.25

    def __init__(
        self,
    ) -> None:

        self._similarity_engine = EmbeddingSimilarityEngine()

    def rerank(
        self,
        candidates: list[RetrievalCandidate],
        top_k: int,
    ) -> list[RetrievalCandidate]:

        selected: list[RetrievalCandidate] = []

        remaining = candidates.copy()

        while remaining and len(selected) < top_k:

            best_candidate = None

            best_score = -999.0

            for candidate in remaining:

                redundancy_penalty = self._compute_redundancy_penalty(
                    candidate,
                    selected,
                )

                diversity_score = candidate.final_score - redundancy_penalty

                logger.debug(
                    "diversity_rerank: doc=%s penalty=%.3f",
                    candidate.document.metadata.get("document_id", "unknown"),
                    redundancy_penalty,
                )

                if diversity_score > best_score:

                    best_candidate = candidate

                    best_score = diversity_score

            if best_candidate is None:
                break

            selected.append(
                best_candidate.model_copy(
                    update={
                        "diversity_score": round(
                            best_score,
                            3,
                        ),
                        "adaptive_score": round(
                            best_score,
                            3,
                        ),
                    }
                )
            )

            remaining.remove(
                best_candidate,
            )

        return selected

    def _compute_redundancy_penalty(
        self,
        candidate: RetrievalCandidate,
        selected: list[RetrievalCandidate],
    ) -> float:

        if not selected:
            return 0.0

        similarities = []

        for existing in selected:

            if candidate.embedding is None or existing.embedding is None:
                continue

            similarity = self._similarity_engine.similarity(
                candidate.embedding,
                existing.embedding,
            )

            similarities.append(
                similarity,
            )

            logger.debug("similarity: %.4f", similarity)

        if not similarities:
            return 0.0

        max_similarity = max(
            similarities,
        )

        return min(
            max_similarity * self.REDUNDANCY_WEIGHT,
            self.REDUNDANCY_CAP,
        )
