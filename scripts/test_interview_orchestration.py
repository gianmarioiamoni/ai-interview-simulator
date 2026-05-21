# scripts/test_interview_orchestration.py

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.interview_orchestration.interview_orchestrator import (
    InterviewOrchestrator,
)


def main() -> None:

    # -------------------------------------------------
    # ORCHESTRATION
    # -------------------------------------------------

    orchestrator = InterviewOrchestrator()

    result = orchestrator.orchestrate(
        items=[],
        role=(RoleType.BACKEND_ENGINEER),
        level=(SeniorityLevel.SENIOR),
        max_questions=5,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()

    print("INTERVIEW ORCHESTRATION")

    print()

    print("RETRIEVAL-DRIVEN " "ORCHESTRATION ACTIVE")

    print()

    # -------------------------------------------------
    # CANDIDATE POOL
    # -------------------------------------------------

    print("CANDIDATE POOL")

    print()

    print(f"eligible: " f"{result.candidate_pool.eligible_count}")

    print(f"rejected: " f"{result.candidate_pool.rejected_count}")

    print()

    # -------------------------------------------------
    # PLANNING
    # -------------------------------------------------

    print("PLANNING")

    print()

    print(
        result.planning_result.model_dump_json(
            indent=2,
        )
    )

    print()

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------

    print("VALIDATION")

    print()

    print(
        result.validation_result.model_dump_json(
            indent=2,
        )
    )

    print()

    # -------------------------------------------------
    # REPLANNING
    # -------------------------------------------------

    print("REPLANNING")

    print()

    print(
        result.replanning_result.model_dump_json(
            indent=2,
        )
    )

    print()

    # -------------------------------------------------
    # FINAL INTERVIEW
    # -------------------------------------------------

    print("FINAL INTERVIEW")

    print()

    for idx, question in enumerate(
        result.assembly_result.questions,
        start=1,
    ):

        print(f"QUESTION #{idx}")

        print()

        print(question.item.text)

        print()

        print(f"role: " f"{question.item.role.type.value}")

        print(f"area: " f"{question.item.area.value}")

        print(f"level: " f"{question.item.level.value}")

        print(f"difficulty: " f"{question.item.difficulty}")

        print(f"stage: " f"{question.stage.value}")

        print()

        print("-" * 80)

        print()

    print()

    print("RETRIEVAL MEMORY")
    print()

    for question in orchestrator._retrieval_memory.get_recent_questions():

        print(question)

if __name__ == "__main__":

    main()
