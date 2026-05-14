# services/question_intelligence/question_retrieval_service.py

# QuestionRetrievalService
#
# Responsibility:
# Executes semantic retrieval over the Question Bank.
# Applies metadata filtering and returns domain objects.
# Does not expose vector store internals.

from typing import List, Optional

from langchain_core.documents import Document

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)

from services.question_intelligence.retrieval.retrieval_strategy import (
    RetrievalStrategy,
)


class QuestionRetrievalService:

    def __init__(
        self,
        vector_store: QuestionVectorStore,
    ) -> None:

        self._vector_store = vector_store

    # =====================================================
    # PUBLIC API
    # =====================================================

    def retrieve(
        self,
        query: str,
        retrieval_strategy: RetrievalStrategy,
        role: Optional[str] = None,
        level: Optional[str] = None,
        interview_type: Optional[str] = None,
        area: Optional[str] = None,
    ) -> List[QuestionBankItem]:

        metadata_filter = self._build_filter(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
        )

        # -------------------------------------------------
        # MMR
        # -------------------------------------------------

        try:

            if retrieval_strategy.use_mmr:

                documents = self._vector_store.max_marginal_relevance_search(
                    query=query,
                    k=retrieval_strategy.k,
                    fetch_k=retrieval_strategy.fetch_k,
                    lambda_mult=retrieval_strategy.lambda_mult,
                    metadata_filter=metadata_filter,
                )

            else:

                documents = self._vector_store.similarity_search(
                    query=query,
                    k=retrieval_strategy.k,
                    metadata_filter=metadata_filter,
                )

        except Exception:

            # ---------------------------------------------
            # FALLBACK
            # ---------------------------------------------

            documents = self._vector_store.similarity_search(
                query=query,
                k=retrieval_strategy.k,
                metadata_filter=metadata_filter,
            )

        return [self._to_domain(doc) for doc in documents]

    # =====================================================
    # FILTER BUILDER
    # =====================================================

    def _build_filter(
        self,
        role: Optional[str],
        level: Optional[str],
        interview_type: Optional[str],
        area: Optional[str],
    ) -> dict | None:

        filters = {}

        if role:
            filters["role"] = role

        if level:
            filters["level"] = level

        if interview_type:
            filters["interview_type"] = interview_type

        if area:
            filters["area"] = area

        if not filters:
            return None

        return {"$and": [{k: v} for k, v in filters.items()]}

    # =====================================================
    # MAPPER
    # =====================================================

    def _to_domain(self, document: Document) -> QuestionBankItem:

        metadata = document.metadata

        
        return QuestionBankItem(
            id=metadata["id"],
            text=document.page_content,
            interview_type=metadata["interview_type"],
            role={
                "type": metadata["role"],
            },
            area=metadata["area"],
            level=metadata["level"],
            difficulty=metadata["difficulty"],
        )
