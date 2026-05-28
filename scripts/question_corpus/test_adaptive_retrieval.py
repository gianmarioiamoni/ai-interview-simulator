# scripts/question_corpus/test_adaptive_retrieval.py

from services.question_corpus.retrieval.adaptive_retrieval_service import AdaptiveRetrievalService
from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext


def main() -> None:

    retrieval = AdaptiveRetrievalService()

    context = AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="senior",
        target_area="technical_case_study",
        target_question_count=5,
        already_used_domains=[
            "distributed_systems",
            "caching",
        ],
        target_difficulty=5,
    )

    results = retrieval.retrieve(
        query="distributed systems scalability",
        context=context,
    )

    print("\nADAPTIVE RETRIEVAL RESULTS\n")

    for index, result in enumerate(results):

        print(f"\nRESULT #{index + 1}\n")

        print(result.document.page_content)

        print("\nSCORES")

        print(f"Final: {result.final_score}")
        print(f"Diversity: {result.diversity_score}")


if __name__ == "__main__":

    main()
