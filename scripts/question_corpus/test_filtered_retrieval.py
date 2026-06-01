# scripts/question_corpus/test_filtered_retrieval.py

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
        k=5,
    )

    print("\nFILTERED RETRIEVAL RESULTS\n")

    for index, result in enumerate(results):

        print(f"\nRESULT #{index + 1}\n")

        print(result.document.page_content)

        print("\nSCORING")

        print(f"Semantic: {result.semantic_score}")
        print(f"Quality: {result.quality_score}")
        print(f"Final: {result.final_score}")

        print("\nMETADATA")

        for key, value in result.document.metadata.items():

            print(f"{key}: {value}")


if __name__ == "__main__":

    main()
