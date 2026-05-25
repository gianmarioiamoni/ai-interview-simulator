# services/retrieval/semantic_cooldown_reranker.py

from sentence_transformers.util import cos_sim

from services.retrieval.contracts import HybridRetrievalResult
from services.retrieval.retrieval_session_memory import RetrievalSessionMemory
from services.embedding.embedding_model_provider import EmbeddingModelProvider


class SemanticCooldownReranker:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        memory: RetrievalSessionMemory,
        similarity_threshold: float = 0.80,
        cooldown_penalty: float = 0.40,
    ) -> None:

        self._memory = memory

        self._threshold = similarity_threshold

        self._penalty = cooldown_penalty

        self._model = EmbeddingModelProvider.get_model()

    # =====================================================
    # PUBLIC
    # =====================================================

    def rerank(
        self,
        results: list[HybridRetrievalResult],
    ) -> list[HybridRetrievalResult]:

        adjusted = []

        recent_questions = self._memory.get_recent_questions()

        for result in results:

            reranked = self._apply_cooldown(
                result=result,
                history=recent_questions,
            )

            adjusted.append(reranked)

        adjusted.sort(
            key=lambda result: (result.fused_score),
            reverse=True,
        )

        return adjusted

    # =====================================================
    # INTERNALS
    # =====================================================

    def _apply_cooldown(
        self,
        result: HybridRetrievalResult,
        history: list[str],
    ) -> HybridRetrievalResult:

        content = result.symbolic_result.record.content

        for previous in history:

            similarity = self._similarity(
                content,
                previous,
            )

            if similarity >= self._threshold:

                adjusted_score = result.fused_score - self._penalty

                return result.model_copy(
                    update={
                        "fused_score": round(
                            adjusted_score,
                            4,
                        )
                    }
                )

        return result

    def _similarity(
        self,
        first: str,
        second: str,
    ) -> float:

        embeddings = self._model.encode(
            [first, second],
            convert_to_tensor=True,
        )

        similarity = cos_sim(
            embeddings[0],
            embeddings[1],
        )

        return float(similarity.item())
