# services/question_intelligence/deduplicated_corpus_builder.py

from services.question_intelligence.semantic_duplicate_detector import (
    SemanticDuplicateDetector,
)


class DeduplicatedCorpusBuilder:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        similarity_threshold: float = 0.88,
    ) -> None:

        self._detector = SemanticDuplicateDetector(
            similarity_threshold=(similarity_threshold)
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        questions: list[str],
    ) -> list[str]:

        if len(questions) < 2:
            return questions

        duplicates = self._detector.find_duplicates(
            questions=questions,
        )

        duplicate_questions = set()

        for duplicate in duplicates:

            (
                canonical,
                duplicate_question,
                similarity,
            ) = duplicate

            # ---------------------------------------------
            # KEEP FIRST QUESTION
            # REMOVE SECOND DUPLICATE
            # ---------------------------------------------

            duplicate_questions.add(duplicate_question)

        cleaned = []

        for question in questions:

            if question in duplicate_questions:
                continue

            cleaned.append(question)

        return cleaned
