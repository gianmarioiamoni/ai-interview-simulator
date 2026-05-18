# scripts/test_coverage_constrained_reranking.py

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

from services.question_intelligence.reranking.coverage_constrained_reranker import (
    CoverageConstrainedReranker,
)

from services.question_intelligence.coverage.coverage_analyzer import (
    CoverageAnalyzer,
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

    reranker = CoverageConstrainedReranker()

    coverage_analyzer = CoverageAnalyzer()

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
        max_per_topic=1,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("COVERAGE-CONSTRAINED RESULTS")
    print()

    for idx, result in enumerate(
        reranked,
        start=1,
    ):

        print(f"RANK #{idx}")
        print()

        print(result.item.text)

        print()
        print("-" * 80)
        print()

    # -------------------------------------------------
    # COVERAGE
    # -------------------------------------------------

    items = [r.item for r in reranked]

    report = coverage_analyzer.analyze(
        items,
    )

    print()
    print("FINAL COVERAGE")
    print()

    print(
        report.model_dump_json(
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
