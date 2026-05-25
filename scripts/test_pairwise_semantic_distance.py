# scripts/test_pairwise_semantic_distance.py


from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.user.role import (
    Role,
    RoleType,
)
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.interview_type import InterviewType

from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.interview_orchestration.pairwise_semantic_distance_engine import PairwiseSemanticDistanceEngine


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

    questions = [
        build_question("How would you design " "a distributed cache?"),
        build_question("Explain eventual " "consistency trade-offs."),
        build_question("Explain database " "sharding strategies."),
    ]

    engine = PairwiseSemanticDistanceEngine()

    similarity = engine.calculate_average_similarity(questions)

    print()

    print("PAIRWISE SEMANTIC DISTANCE")

    print()

    print(f"average_similarity: " f"{similarity}")

    print()


if __name__ == "__main__":

    main()
