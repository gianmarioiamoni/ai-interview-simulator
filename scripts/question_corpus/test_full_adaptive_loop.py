# scripts/question_corpus/test_full_adaptive_loop.py

from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory
from services.question_corpus.retrieval.adaptive_context_builder import AdaptiveContextBuilder
from services.question_corpus.retrieval.adaptive_retrieval_service import AdaptiveRetrievalService
from services.question_corpus.retrieval.interview_memory_updater import InterviewMemoryUpdater


def main() -> None:

    retrieval = AdaptiveRetrievalService()

    updater = InterviewMemoryUpdater()

    context_builder = AdaptiveContextBuilder()

    memory = InterviewRetrievalMemory()

    # =====================================================
    # ITERATION 1
    # =====================================================

    context = context_builder.build(
        memory=memory,
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
        question_count=3,
    )

    results = retrieval.retrieve(
        query="distributed systems scalability",
        context=context,
    )

    first = results[0]

    print("\nFIRST QUESTION\n")

    print(first.document.page_content)

    memory = updater.update(
        memory=memory,
        candidate=first,
        evaluation_score=0.45,
    )

    # =====================================================
    # ITERATION 2
    # =====================================================

    context = context_builder.build(
        memory=memory,
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
        question_count=3,
    )

    results = retrieval.retrieve(
        query="distributed systems scalability",
        context=context,
    )

    print("\nSECOND ITERATION\n")

    for result in results:

        print("\n---\n")

        print(result.document.page_content)

        print("\nAdaptive Score")

        print(result.adaptive_score)


if __name__ == "__main__":
    main()
