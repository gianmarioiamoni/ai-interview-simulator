# scripts/test_interview_orchestration.py

from domain.contracts.user.role import (
    RoleType,
)

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_ingestion.loaders.json_dataset_loader import (
    JSONDatasetLoader,
)

from services.question_ingestion.normalizers.question_normalizer import (
    QuestionNormalizer,
)

from services.question_ingestion.classifiers.question_metadata_classifier import (
    QuestionMetadataClassifier,
)

from services.question_ingestion.mappers.question_bank_item_mapper import (
    QuestionBankItemMapper,
)

from services.interview_orchestration.interview_orchestrator import (
    InterviewOrchestrator,
)


def main():

    # -------------------------------------------------
    # LOAD
    # -------------------------------------------------

    loader = JSONDatasetLoader()

    raw_records = loader.load(
        dataset_path=("data/curated_engineering_questions.json"),
        source="curated_engineering",
    )

    # -------------------------------------------------
    # NORMALIZE
    # -------------------------------------------------

    normalizer = QuestionNormalizer()

    normalized = normalizer.normalize(
        raw_records,
    )

    # -------------------------------------------------
    # CLASSIFY
    # -------------------------------------------------

    classifier = QuestionMetadataClassifier()

    classified = classifier.classify(
        normalized,
    )

    # -------------------------------------------------
    # MAP
    # -------------------------------------------------

    mapper = QuestionBankItemMapper()

    items = mapper.map(
        classified,
    )

    # -------------------------------------------------
    # ORCHESTRATION
    # -------------------------------------------------

    orchestrator = InterviewOrchestrator()

    result = orchestrator.orchestrate(
        items=items,
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

    print("CANDIDATE POOL")
    print()

    print(f"eligible: " f"{result.candidate_pool.eligible_count}")

    print(f"rejected: " f"{result.candidate_pool.rejected_count}")

    print()

    print("PLANNING")
    print()

    print(
        result.planning_result.model_dump_json(
            indent=2,
        )
    )
    
    print()
    print("VALIDATION")
    print()
    print(
        result.validation_result.model_dump_json(
            indent=2,
        )
    )

    print()

    print()
    print("REPLANNING")
    print()
    print(
        result.replanning_result.model_dump_json(
            indent=2,
        )
    )
    print()

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


if __name__ == "__main__":
    main()
