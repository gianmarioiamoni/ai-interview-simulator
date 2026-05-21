# scripts/test_semantic_cluster_suppression.py

from services.planning.semantic_cluster_suppressor import (
    SemanticClusterSuppressor,
)

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from domain.contracts.user.role import (
    Role,
    RoleType,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from domain.contracts.interview.interview_type import (
    InterviewType,
)

from services.question_ingestion.contracts.ingestion_metadata import (
    IngestionMetadata,
)


def build_question(
    text: str,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=text,
        text=text,
        interview_type=(InterviewType.TECHNICAL),
        role=(Role(type=(RoleType.BACKEND_ENGINEER))),
        area=(InterviewArea.TECH_CASE_STUDY),
        level=(SeniorityLevel.MID),
        difficulty=5,
        ingestion_metadata=(
            IngestionMetadata(
                source_name="test",
                source_type="test",
                dataset_version="v1",
                ingestion_timestamp=("2026-01-01T00:00:00Z"),
            )
        ),
    )


def main() -> None:

    selected = [build_question("How would you design " "a distributed cache?")]

    candidate = build_question(
        "How would you architect " "a distributed caching layer?"
    )

    suppressor = SemanticClusterSuppressor()

    original_score = 1.8

    adjusted = suppressor.apply_penalty(
        candidate=candidate,
        selected_questions=selected,
        current_score=(original_score),
    )

    print()

    print("SEMANTIC CLUSTER SUPPRESSION")

    print()

    print(f"original_score: " f"{original_score}")

    print(f"adjusted_score: " f"{adjusted}")

    print()


if __name__ == "__main__":

    main()
