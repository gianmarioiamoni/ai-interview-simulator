# scripts/test_retrieval_diagnostics.py

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

from services.question_intelligence.diagnostics.retrieval_diversity_analyzer import (
    RetrievalDiversityAnalyzer,
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

    # -------------------------------------------------
    # SERVICES
    # -------------------------------------------------

    chroma_store = ChromaQuestionStore()

    vector_store = QuestionVectorStore(
        chroma_store,
    )

    retrieval_service = QuestionRetrievalService(
        vector_store,
    )

    query_builder = RetrievalQueryBuilder()

    strategy_resolver = RetrievalStrategyResolver()

    analyzer = RetrievalDiversityAnalyzer()

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
        questions_per_area=5,
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
    # ANALYZE
    # -------------------------------------------------

    report = analyzer.analyze(
        results,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("RETRIEVAL QUALITY REPORT")
    print()

    print(report.model_dump_json(indent=2))

    print()

    for i, item in enumerate(results, start=1):

        print(f"RESULT #{i}")
        print(item.text)
        print()


if __name__ == "__main__":
    main()
