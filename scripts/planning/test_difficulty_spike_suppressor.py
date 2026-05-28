# scripts/test_difficulty_spike_suppressor.py

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

from services.planning.difficulty_spike_suppressor import (
    DifficultySpikeSuppressor,
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

    suppressor = DifficultySpikeSuppressor()

    previous_questions = [
        build_question(
            question_id="q1",
            difficulty=1,
        )
    ]

    candidate = build_question(
        question_id="q2",
        difficulty=5,
    )

    original_score = 5.3

    adjusted_score = suppressor.apply_penalty(
        candidate=candidate,
        selected_questions=previous_questions,
        current_score=original_score,
    )

    print()

    print("DIFFICULTY SPIKE SUPPRESSION")

    print()

    print(f"original_score: {original_score}")

    print(f"adjusted_score: {adjusted_score}")

    print()


if __name__ == "__main__":

    main()
