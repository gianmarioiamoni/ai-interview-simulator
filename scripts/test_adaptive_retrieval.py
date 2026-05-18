# scripts/test_adaptive_retrieval.py

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

from services.question_intelligence.policies.adaptive_retrieval_orchestrator import (
    AdaptiveRetrievalOrchestrator,
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

    orchestrator = AdaptiveRetrievalOrchestrator()

    # -------------------------------------------------
    # PROFILE
    # -------------------------------------------------

    role = RoleType.BACKEND_ENGINEER

    level = SeniorityLevel.MID

    # -------------------------------------------------
    # QUERY
    # -------------------------------------------------

    query = query_builder.build(
        role=role,
        level=level,
        area=InterviewArea.TECH_DATABASE,
    )

    strategy = strategy_resolver.resolve(
        area=InterviewArea.TECH_DATABASE,
        level=level,
        questions_per_area=10,
    )

    # -------------------------------------------------
    # RETRIEVE
    # -------------------------------------------------

    results = retrieval_service.retrieve(
        query=query,
        retrieval_strategy=strategy,
        role=role.value,
        level=level.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=InterviewArea.TECH_DATABASE.value,
    )

    print()
    print(f"RETRIEVED: {len(results)}")
    print()

    for r in results:
        print(r.text)

    # -------------------------------------------------
    # OPTIMIZE
    # -------------------------------------------------

    optimized = orchestrator.optimize(
        items=results,
        role=role,
        level=level,
        target_count=5,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("ADAPTIVE RETRIEVAL RESULTS")
    print()

    for idx, result in enumerate(
        optimized,
        start=1,
    ):

        print(f"RANK #{idx}")
        print()

        print(result.item.text)

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
