# scripts/test_question_quality.py

from infrastructure.vector_store.chroma_question_store import (
    ChromaQuestionStore,
)

from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)

from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.quality.question_quality_scorer import (
    QuestionQualityScorer,
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

    scorer = QuestionQualityScorer()

    # -------------------------------------------------
    # RETRIEVE
    # -------------------------------------------------

    items = retrieval_service.retrieve(
        query="backend scalability optimization",
        retrieval_strategy=RetrievalStrategy(
            k=10,
            fetch_k=20,
            use_mmr=True,
            lambda_mult=0.5,
        ),
        role=RoleType.BACKEND_ENGINEER.value,
        level=SeniorityLevel.MID.value,
        interview_type=InterviewType.TECHNICAL.value,
        area=InterviewArea.TECH_DATABASE.value,
    )

    # -------------------------------------------------
    # SCORE
    # -------------------------------------------------

    scored = [
        scorer.score(
            item,
            SeniorityLevel.SENIOR,
        )
        for item in items
    ]

    scored.sort(
        key=lambda s: (s.breakdown.final_score),
        reverse=True,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("QUESTION QUALITY REPORT")
    print()

    for idx, scored_question in enumerate(
        scored,
        start=1,
    ):

        print(f"RANK #{idx}")
        print()

        print(scored_question.item.text)
        print()

        print(
            scored_question.breakdown.model_dump_json(
                indent=2,
            )
        )

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
