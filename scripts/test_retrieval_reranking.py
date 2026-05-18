# scripts/test_retrieval_reranking.py

from infrastructure.vector_store.chroma_question_store import (
    ChromaQuestionStore,
)

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.retrieval_query_builder import (
    RetrievalQueryBuilder,
)

from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)

from services.question_intelligence.reranking.retrieval_reranker import (
    RetrievalReranker,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.interview.interview_type import (
    InterviewType,
)

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)


def main():

    chroma_store = ChromaQuestionStore()

    vector_store = QuestionVectorStore(
        chroma_store,
    )

    retrieval_service = QuestionRetrievalService(
        vector_store,
    )

    query_builder = RetrievalQueryBuilder()

    strategy_resolver = RetrievalStrategyResolver()

    reranker = RetrievalReranker()

    # -------------------------------------------------
    # QUERY
    # -------------------------------------------------

    query = query_builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        area=InterviewArea.TECH_DATABASE,
    )

    strategy = strategy_resolver.resolve(
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        questions_per_area=10,
    )

    # -------------------------------------------------
    # RETRIEVE
    # -------------------------------------------------

    results = retrieval_service.retrieve(
        query=query,
        retrieval_strategy=strategy,
        role=RoleType.BACKEND_ENGINEER.value,
        level=SeniorityLevel.MID.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=InterviewArea.TECH_DATABASE.value,
    )

    # -------------------------------------------------
    # RERANK
    # -------------------------------------------------

    reranked = reranker.rerank(
        items=results,
        target_count=5,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("RERANKED RESULTS")
    print()

    for idx, result in enumerate(reranked, start=1):

        print(f"RANK #{idx}")
        print()

        print(f"QUESTION:")
        print(result.item.text)
        print()

        print(f"semantic_score: {result.semantic_score}")
        print(f"redundancy_penalty: " f"{result.redundancy_penalty}")
        print(f"final_score: {result.final_score}")

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
