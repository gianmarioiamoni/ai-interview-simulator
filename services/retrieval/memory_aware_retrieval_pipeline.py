# services/retrieval/memory_aware_retrieval_pipeline.py

from services.retrieval.contracts import (
    HybridRetrievalResult,
)

from services.retrieval.diversity_aware_reranker import (
    DiversityAwareReranker,
)

from services.retrieval.question_reuse_suppressor import (
    QuestionReuseSuppressor,
)

from services.retrieval.retrieval_session_memory import (
    RetrievalSessionMemory,
)

from services.retrieval.semantic_cooldown_reranker import (
    SemanticCooldownReranker,
)


class MemoryAwareRetrievalPipeline:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        memory: RetrievalSessionMemory,
    ) -> None:

        self._memory = memory

        self._diversity_reranker = DiversityAwareReranker()

        self._reuse_suppressor = QuestionReuseSuppressor(
            memory=memory,
        )

        self._semantic_cooldown = SemanticCooldownReranker(
            memory=memory,
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def process(
        self,
        results: list[HybridRetrievalResult],
    ) -> list[HybridRetrievalResult]:

        # -------------------------------------------------
        # DIVERSITY RERANKING
        # -------------------------------------------------

        diversified = self._diversity_reranker.rerank(results)

        # -------------------------------------------------
        # EXACT REUSE SUPPRESSION
        # -------------------------------------------------

        suppressed = self._reuse_suppressor.suppress(diversified)

        # -------------------------------------------------
        # SEMANTIC COOLDOWN
        # -------------------------------------------------

        cooled = self._semantic_cooldown.rerank(suppressed)

        # -------------------------------------------------
        # MEMORY UPDATE
        # -------------------------------------------------

        self._update_memory(cooled)

        return cooled

    # =====================================================
    # INTERNALS
    # =====================================================

    def _update_memory(
        self,
        results: list[HybridRetrievalResult],
    ) -> None:

        for result in results:

            content = result.symbolic_result.record.content

            self._memory.remember(content)
