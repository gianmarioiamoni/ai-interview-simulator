# scripts/test_policy_driven_assembly.py

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

from services.interview_policy.policy_factory import (
    PolicyFactory,
)

from services.interview_selection.adaptive_interview_assembler import (
    AdaptiveInterviewAssembler,
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
    # POLICY
    # -------------------------------------------------

    factory = PolicyFactory()

    policy = factory.build(
        role=(RoleType.BACKEND_ENGINEER),
        level=(SeniorityLevel.SENIOR),
    )

    # -------------------------------------------------
    # ASSEMBLY
    # -------------------------------------------------

    assembler = AdaptiveInterviewAssembler()

    result = assembler.assemble(
        items=items,
        policy=policy,
        max_questions=5,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("POLICY-DRIVEN ASSEMBLY")
    print()

    print(
        policy.model_dump_json(
            indent=2,
        )
    )

    print()

    for idx, question in enumerate(
        result.questions,
        start=1,
    ):

        print(f"QUESTION #{idx}")
        print()

        print(question.item.text)
        print()

        print(f"area: " f"{question.item.area.value}")

        print(f"difficulty: " f"{question.item.difficulty}")

        print(f"stage: " f"{question.stage.value}")

        print()

        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
