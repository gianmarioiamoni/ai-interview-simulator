# scripts/question_corpus/test_context_builder.py

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

from services.question_corpus.retrieval.adaptive_context_builder import (
    AdaptiveContextBuilder,
)


def main() -> None:

    memory = InterviewRetrievalMemory(
        covered_domains=[
            "backend",
            "apis",
        ],
        weak_domains=[
            "distributed_systems",
        ],
        average_score=0.52,
        question_count=3,
    )

    builder = AdaptiveContextBuilder()

    context = builder.build(
        memory=memory,
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
        question_count=5,
    )

    print("\nADAPTIVE CONTEXT\n")

    print(context.model_dump())


if __name__ == "__main__":
    main()
