# scripts/test_adaptive_difficulty_balancing.py

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

from services.planning.planner_selection_scoring_engine import (
    PlannerSelectionScoringEngine,
)


def build_question(
    question_id: str,
    text: str,
    difficulty: int,
    area: InterviewArea,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=question_id,
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(
            type=RoleType.BACKEND_ENGINEER,
        ),
        area=area,
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

    engine = PlannerSelectionScoringEngine()

    selected_questions = [
        build_question(
            question_id="q1",
            text="Basic SQL joins",
            difficulty=1,
            area=InterviewArea.TECH_DATABASE,
        )
    ]

    candidate = build_question(
        question_id="q2",
        text="Design a globally distributed cache",
        difficulty=5,
        area=InterviewArea.TECH_CASE_STUDY,
    )

    breakdown = engine.score(
        candidate=candidate,
        selected_questions=selected_questions,
    )

    print()

    print("ADAPTIVE DIFFICULTY BALANCING")

    print()

    print(
        breakdown.model_dump_json(
            indent=2,
        )
    )

    print()


if __name__ == "__main__":

    main()
