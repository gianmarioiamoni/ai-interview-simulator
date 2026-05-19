# scripts/test_interview_selection.py

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

from services.interview_selection.interview_question_selector import (
    InterviewQuestionSelector,
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
    # SELECTION
    # -------------------------------------------------

    selector = InterviewQuestionSelector()

    result = selector.select(
        candidates=items,
        max_questions=5,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()
    print("INTERVIEW SELECTION")
    print()

    print(
        result.model_dump_json(
            indent=2,
        )
    )

    print()

    for idx, question in enumerate(
        result.selected_questions,
        start=1,
    ):

        print(f"QUESTION #{idx}")
        print()

        print(question.item.text)
        print()

        print(f"area: " f"{question.item.area.value}")

        print(f"difficulty: " f"{question.item.difficulty}")

        print(f"reason: " f"{question.selection_reason}")

        print()
        print("-" * 80)
        print()


if __name__ == "__main__":
    main()
