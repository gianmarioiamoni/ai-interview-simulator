# services/retrieval/corpus_retrieval_preparator.py

import json

from pathlib import Path

from services.question_ingestion.contracts import (
    CuratedCorpusRecord,
)

from services.retrieval.contracts import (
    RetrievalCorpusRecord,
)


class CorpusRetrievalPreparator:

    # =====================================================
    # PUBLIC
    # =====================================================

    def prepare(
        self,
        corpus_path: str,
    ) -> list[RetrievalCorpusRecord]:

        curated_records = self._load_records(corpus_path)

        prepared: list[RetrievalCorpusRecord] = []

        for record in curated_records:

            retrieval_tags = self._build_tags(record)

            retrieval_score = self._calculate_retrieval_score(record)

            prepared.append(
                RetrievalCorpusRecord(
                    content=(record.question.text),
                    retrieval_tags=(retrieval_tags),
                    retrieval_score=(retrieval_score),
                    source_repository=(record.source_repository),
                    corpus_version=(record.corpus_version),
                    semantic_categories=(record.matched_categories),
                    original_record=(record),
                )
            )

        return prepared

    # =====================================================
    # INTERNALS
    # =====================================================

    def _load_records(
        self,
        corpus_path: str,
    ) -> list[CuratedCorpusRecord]:

        path = Path(corpus_path)

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            raw_data = json.load(f)

        return [CuratedCorpusRecord(**item) for item in raw_data]

    def _build_tags(
        self,
        record: CuratedCorpusRecord,
    ) -> list[str]:

        tags = set()

        tags.update(record.matched_categories)

        tags.update(record.matched_terms)

        # ---------------------------------------------
        # AREA
        # ---------------------------------------------

        if record.question.area_hint:

            tags.add(
                record.question
                .area_hint
                .value
            )

        # ---------------------------------------------
        # LEVEL
        # ---------------------------------------------

        if record.question.level_hint:

            tags.add(
                record.question
                .level_hint
                .value
            )

        # ---------------------------------------------
        # ROLE
        # ---------------------------------------------

        if record.question.role_hint:

            tags.add(
                record.question
                .role_hint
                .value
            )

        return sorted(tags)

    
    def _calculate_retrieval_score(
        self,
        record: CuratedCorpusRecord,
    ) -> float:

        score = record.semantic_score

        # ---------------------------------------------
        # DIFFICULTY BOOST
        # ---------------------------------------------

        difficulty = record.question.difficulty_hint

        if difficulty is not None:

            score += difficulty * 0.05

        # ---------------------------------------------
        # CATEGORY DENSITY BOOST
        # ---------------------------------------------

        score += len(record.matched_categories) * 0.1

        return round(score, 2)
