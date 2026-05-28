# scripts/test_retrieval_pipeline.py

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
    # VECTOR STORE
    # -------------------------------------------------

    chroma_store = ChromaQuestionStore()

    vector_store = QuestionVectorStore(
        chroma_store,
    )

    retrieval_service = QuestionRetrievalService(
        vector_store,
    )

    # -------------------------------------------------
    # QUERY BUILDER
    # -------------------------------------------------

    query_builder = RetrievalQueryBuilder()

    query = query_builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        area=InterviewArea.TECH_DATABASE,
    )

    print()
    print("QUERY:")
    print(query)
    print()

    # -------------------------------------------------
    # RETRIEVE
    # -------------------------------------------------

    strategy_resolver = RetrievalStrategyResolver()

    strategy = strategy_resolver.resolve(
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        questions_per_area=5,
    )

    results = retrieval_service.retrieve(
        query=query,
        retrieval_strategy=strategy,
        role=RoleType.BACKEND_ENGINEER.value,
        level=SeniorityLevel.MID.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=InterviewArea.TECH_DATABASE.value,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("RESULTS:", len(results))
    print()

    for i, item in enumerate(results, start=1):

        print(f"RESULT #{i}")
        print()

        print("TEXT:")
        print(item.text)
        print()

        print("ROLE:", item.role)
        print("AREA:", item.area)
        print("LEVEL:", item.level)
        print("DIFFICULTY:", item.difficulty)

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
