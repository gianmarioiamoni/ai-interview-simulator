# scripts/test_planner_integrated_retrieval.py

from services.retrieval.contracts import (
    RetrievalPlanningIntent,
)

from services.retrieval.planner_retrieval_service import (
    PlannerRetrievalService,
)


def main() -> None:

    service = PlannerRetrievalService()

    intent = RetrievalPlanningIntent(
        focus_areas=[
            "distributed_systems",
        ],
        required_tags=[
            "distributed_systems",
        ],
        target_level="senior",
        query_text=("distributed systems " "consistency scalability"),
        max_candidates=5,
    )

    results = service.retrieve_candidates(
        intent=intent,
        corpus_path=("datasets/curated/" "tech_interview_handbook.json"),
    )

    print()
    print("PLANNER-INTEGRATED RETRIEVAL")

    print()

    print(f"TOTAL RESULTS: " f"{len(results)}")

    for index, result in enumerate(
        results,
        start=1,
    ):

        symbolic = result.symbolic_result

        print()

        print(f"RESULT #{index}")

        print()

        print(symbolic.record.content)

        print()

        print(f"fused_score: " f"{result.fused_score}")

        print()

        print(f"embedding_similarity: " f"{result.embedding_similarity}")

        print()

        print(f"semantic_overlap: " f"{symbolic.semantic_overlap}")

        print()

        print(f"matched_categories: " f"{symbolic.matched_categories}")

        print()

        print("-" * 80)


if __name__ == "__main__":

    main()
