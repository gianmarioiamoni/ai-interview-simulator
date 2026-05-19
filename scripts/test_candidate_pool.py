# scripts/test_candidate_pool.py

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

from services.candidate_pool.candidate_pool_builder import (
    CandidatePoolBuilder,
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
    # POOL
    # -------------------------------------------------

    builder = CandidatePoolBuilder()

    pool = builder.build(
        items=items,
        role=(RoleType.BACKEND_ENGINEER),
        level=(SeniorityLevel.SENIOR),
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("CANDIDATE POOL")
    print()

    print(f"TOTAL: " f"{pool.total_candidates}")

    print(f"ELIGIBLE: " f"{pool.eligible_count}")

    print(f"REJECTED: " f"{pool.rejected_count}")

    print()

    print("ELIGIBLE QUESTIONS")
    print()

    for idx, question in enumerate(
        pool.eligible_questions,
        start=1,
    ):

        print(f"QUESTION #{idx}")
        print()

        print(question.text)
        print()

        print(f"role: " f"{question.role.type.value}")

        print(f"level: " f"{question.level.value}")

        print()

        print("-" * 80)
        print()

    print()
    print("REJECTED QUESTIONS")
    print()

    for idx, question in enumerate(
        pool.rejected_questions,
        start=1,
    ):

        print(f"QUESTION #{idx}")
        print()

        print(question.text)
        print()

        print(f"role: " f"{question.role.type.value}")

        print(f"level: " f"{question.level.value}")

        print()

        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
