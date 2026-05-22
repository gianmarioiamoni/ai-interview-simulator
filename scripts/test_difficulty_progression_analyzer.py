# scripts/test_difficulty_progression_analyzer.py

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.interview.interview_type import (
    InterviewType,
)

from domain.contracts.user.role import (
    Role,
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_ingestion.contracts.ingestion_metadata import (
    IngestionMetadata,
)

from services.planning.difficulty_progression_analyzer import (
    DifficultyProgressionAnalyzer,
)


def build_question(
    question_id: str,
    difficulty: int,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=question_id,
        text=f"Question difficulty {difficulty}",
        interview_type=InterviewType.TECHNICAL,
        role=Role(
            type=RoleType.BACKEND_ENGINEER,
        ),
        area=InterviewArea.TECH_CASE_STUDY,
        level=SeniorityLevel.MID,
        difficulty=difficulty,
        ingestion_metadata=IngestionMetadata(
            source_name="test",
            source_type="test",
            dataset_version="v1",
            ingestion_timestamp="2026-01-01T00:00:00Z",
        ),
    )


def main() -> None:

    analyzer = DifficultyProgressionAnalyzer()

    questions = [
        build_question("q1", 1),
        build_question("q2", 3),
        build_question("q3", 2),
        build_question("q4", 5),
    ]

    score = analyzer.calculate_progression_score(
        questions=questions,
    )

    print()

    print("DIFFICULTY PROGRESSION")

    print()

    print(f"score: {score}")

    print()


if __name__ == "__main__":

    main()
