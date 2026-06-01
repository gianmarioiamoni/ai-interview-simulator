# scripts/question_corpus/test_full_adaptive_loop.py

from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory
from services.question_corpus.question_retrieval_runtime import QuestionRetrievalRuntime
from services.question_corpus.retrieval.interview_memory_updater import InterviewMemoryUpdater


def main() -> None:

    runtime = QuestionRetrievalRuntime()

    updater = InterviewMemoryUpdater()

    memory = InterviewRetrievalMemory()

    # =====================================================
    # ITERATION 1
    # =====================================================

    results = runtime.retrieve_questions_from_memory(
        query="distributed systems scalability",
        memory=memory,
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
        question_count=3,
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

    results = runtime.retrieve_questions_from_memory(
        query="distributed systems scalability",
        memory=memory,
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
        question_count=3,
    )

    print("\nSECOND ITERATION\n")

    for result in results:

        print("\n---\n")

        print(result.document.page_content)

        print("\nAdaptive Score")

        print(result.adaptive_score)


if __name__ == "__main__":

    main()
