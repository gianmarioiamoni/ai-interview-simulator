# services/question_corpus/dedup/corpus_id_deduplicator.py

from domain.contracts.corpus.curated_question import CuratedQuestion


class CorpusIdDeduplicator:

    # =====================================================
    # PUBLIC
    # =====================================================

    def deduplicate(
        self,
        questions: list[CuratedQuestion],
    ) -> tuple[list[CuratedQuestion], int]:

        seen_ids: set[str] = set()

        deduplicated: list[CuratedQuestion] = []

        skipped_count = 0

        for question in questions:

            if question.id in seen_ids:

                skipped_count += 1

                continue

            seen_ids.add(
                question.id,
            )

            deduplicated.append(
                question,
            )

        return deduplicated, skipped_count
