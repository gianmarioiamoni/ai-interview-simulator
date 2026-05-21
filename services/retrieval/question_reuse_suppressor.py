# services/retrieval/question_reuse_suppressor.py

from services.retrieval.contracts import (
    HybridRetrievalResult,
)

from services.retrieval.retrieval_session_memory import (
    RetrievalSessionMemory,
)


class QuestionReuseSuppressor:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        memory: RetrievalSessionMemory,
        suppression_penalty: float = 0.75,
    ) -> None:

        self._memory = memory

        self._penalty = suppression_penalty

    # =====================================================
    # PUBLIC
    # =====================================================

    def suppress(
        self,
        results: list[HybridRetrievalResult],
    ) -> list[HybridRetrievalResult]:

        adjusted_results = []

        for result in results:

            adjusted = self._adjust_result(result)

            adjusted_results.append(adjusted)

        adjusted_results.sort(
            key=lambda result: (result.fused_score),
            reverse=True,
        )

        return adjusted_results

    # =====================================================
    # INTERNALS
    # =====================================================

    def _adjust_result(
        self,
        result: HybridRetrievalResult,
    ) -> HybridRetrievalResult:

        question = result.symbolic_result.record.content

        if not self._memory.has_seen(question):

            return result

        adjusted_score = result.fused_score - self._penalty

        return result.model_copy(
            update={
                "fused_score": round(
                    adjusted_score,
                    4,
                )
            }
        )
