# services/question_intelligence/question_retrieval_service.py

# QuestionRetrievalService
#
# Responsibility:
# Executes semantic retrieval over the Question Bank.
# Applies metadata filtering and returns domain objects.
# Public API is preserved; retrieval backend is routed through question_corpus runtime.

from typing import List, Optional

from langchain_core.documents import Document

from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from services.question_intelligence.adapters.retrieval_strategy_context_adapter import (
    RetrievalStrategyContextAdapter,
)
from services.question_intelligence.question_vector_store import QuestionVectorStore
from services.question_intelligence.retrieval.retrieval_strategy import RetrievalStrategy
from services.question_corpus.mappers.retrieval_candidate_mapper import (
    RetrievalCandidateMapper,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.question_retrieval_runtime import QuestionRetrievalRuntime
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


class QuestionRetrievalService:

    def __init__(
        self,
        vector_store: QuestionVectorStore | None = None,
        context_adapter: RetrievalStrategyContextAdapter | None = None,
        question_retrieval_runtime: QuestionRetrievalRuntime | None = None,
        retrieval_candidate_mapper: RetrievalCandidateMapper | None = None,
    ) -> None:

        # Legacy vector store dependency retained for compatibility; not used by retrieve().
        self._vector_store = vector_store

        self._context_adapter = (
            context_adapter
            if context_adapter is not None
            else RetrievalStrategyContextAdapter()
        )

        self._question_retrieval_runtime = (
            question_retrieval_runtime
            if question_retrieval_runtime is not None
            else QuestionRetrievalRuntime()
        )

        self._retrieval_candidate_mapper = (
            retrieval_candidate_mapper
            if retrieval_candidate_mapper is not None
            else RetrievalCandidateMapper()
        )

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
        memory: InterviewRetrievalMemory | None = None,
    ) -> List[QuestionBankItem]:

        context = self._context_adapter.adapt(
            query=query,
            retrieval_strategy=retrieval_strategy,
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            memory=memory,
        )

        candidates = self._question_retrieval_runtime.retrieve_questions(
            query=query,
            context=context,
        )

        return self._retrieval_candidate_mapper.map(
            candidates=candidates,
        )

    # =====================================================
    # LEGACY — FILTER BUILDER (question_bank / ChromaQuestionStore path)
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
    # LEGACY — MAPPER (question_bank / ChromaQuestionStore path)
    # =====================================================

    def _to_domain(
        self,
        document: Document,
    ) -> QuestionBankItem:

        metadata = document.metadata

        ingestion_metadata = IngestionMetadata(
            source_name=metadata.get(
                "source_name",
                "vector_store",
            ),
            source_type=metadata.get(
                "source_type",
                "retrieval",
            ),
            dataset_version=metadata.get(
                "dataset_version",
                "unknown",
            ),
            ingestion_timestamp=metadata.get(
                "ingestion_timestamp",
                "",
            ),
        )

        provenance = QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name=ingestion_metadata.source_name,
            source_type=ingestion_metadata.source_type,
            dataset_version=ingestion_metadata.dataset_version,
        )

        return QuestionBankItem(
            id=metadata["id"],
            text=document.page_content,
            interview_type=metadata["interview_type"],
            role=Role(type=RoleType(metadata["role"])),
            area=metadata["area"],
            level=metadata["level"],
            difficulty=metadata["difficulty"],
            ingestion_metadata=ingestion_metadata,
            provenance=provenance,
        )