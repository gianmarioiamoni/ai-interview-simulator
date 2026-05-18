# scripts/test_hybrid_retrieval.py

from infrastructure.vector_store.chroma_question_store import (
    ChromaQuestionStore,
)

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.hybrid.hybrid_retrieval_engine import (
    HybridRetrievalEngine,
)

from services.question_intelligence.retrieval.retrieval_strategy import (
    RetrievalStrategy,
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

    # -------------------------------------------------
    # RETRIEVE CANDIDATES
    # -------------------------------------------------

    candidates = retrieval_service.retrieve(
        query="Explain SQL transactions and indexing",
        retrieval_strategy=RetrievalStrategy(
            k=20,
            fetch_k=40,
            use_mmr=True,
            lambda_mult=0.5,
        ),
        role=RoleType.BACKEND_ENGINEER.value,
        level=SeniorityLevel.MID.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=InterviewArea.TECH_DATABASE.value,
    )

    # -------------------------------------------------
    # HYBRID SEARCH
    # -------------------------------------------------

    engine = HybridRetrievalEngine(
        candidates,
    )

    results = engine.search(
        query="Explain SQL transactions and indexing",
        top_k=5,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("HYBRID RETRIEVAL RESULTS")
    print()

    for idx, result in enumerate(
        results,
        start=1,
    ):

        print(f"RANK #{idx}")
        print()

        print(result.text)
        print()

        print(f"semantic_score: " f"{result.semantic_score}")

        print(f"keyword_score: " f"{result.keyword_score}")

        print(f"final_score: " f"{result.final_score}")

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
