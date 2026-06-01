# scripts/question_corpus/test_diversity_retrieval.py

from services.question_corpus.contracts.retrieval_filters import RetrievalFilters
from services.question_corpus.question_retrieval_runtime import QuestionRetrievalRuntime


def main() -> None:

    runtime = QuestionRetrievalRuntime()

    filters = RetrievalFilters(
        role="backend_engineer",
        seniority="senior",
        area="technical_case_study",
    )

    results = runtime.search_with_filters(
        query="distributed systems scalability",
        filters=filters,
        k=10,
    )

    print("\nDIVERSITY RETRIEVAL RESULTS\n")

    for index, result in enumerate(results):

        print(f"\nRESULT #{index + 1}\n")

        print(result.document.page_content)

        print("\nFINAL SCORE")

        print(result.final_score)

        print(f"Diversity: {result.diversity_score}")


if __name__ == "__main__":

    main()
