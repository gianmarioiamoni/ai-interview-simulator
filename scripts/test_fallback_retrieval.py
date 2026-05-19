# scripts/test_fallback_retrieval.py

from infrastructure.vector_store.chroma_question_store import (
    ChromaQuestionStore,
)

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.fallback.fallback_retrieval_engine import (
    FallbackRetrievalEngine,
)

from services.question_intelligence.retrieval.retrieval_strategy import (
    RetrievalStrategy,
)

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from domain.contracts.interview.interview_type import (
    InterviewType,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)


def main():

    chroma_store = ChromaQuestionStore()

    vector_store = QuestionVectorStore(
        chroma_store,
    )

    retrieval_service = QuestionRetrievalService(
        vector_store,
    )

    engine = FallbackRetrievalEngine(
        retrieval_service,
    )

    # -------------------------------------------------
    # STRICT QUERY
    # -------------------------------------------------

    results = engine.retrieve(
        query="distributed scalability transactions",
        retrieval_strategy=RetrievalStrategy(
            k=5,
            fetch_k=20,
            use_mmr=True,
            lambda_mult=0.5,
        ),
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("FALLBACK RETRIEVAL RESULTS")
    print()

    print(f"RESULT COUNT: {len(results)}")
    print()

    for idx, item in enumerate(
        results,
        start=1,
    ):

        print(f"RESULT #{idx}")
        print()

        print(item.text)
        print()

        print(f"role: {item.role.type.value}")

        print(f"level: {item.level.value}")

        print(f"area: {item.area.value}")

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
