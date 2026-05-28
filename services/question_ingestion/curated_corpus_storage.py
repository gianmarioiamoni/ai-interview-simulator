# services/question_ingestion/curated_corpus_storage.py

import json

from pathlib import Path

from services.question_ingestion.contracts import (
    CorpusOnboardingResult,
    CuratedCorpusRecord,
)


class CuratedCorpusStorage:

    # =====================================================
    # PUBLIC
    # =====================================================

    def persist(
        self,
        onboarding_result: CorpusOnboardingResult,
        output_path: str,
        corpus_version: str,
    ) -> None:

        records: list[CuratedCorpusRecord] = []

        for result in onboarding_result.accepted_results:

            if result.normalized_record is None:
                continue

            records.append(
                CuratedCorpusRecord(
                    question=result.normalized_record,
                    semantic_score=result.technical_result.score,
                    matched_categories=result.technical_result.matched_categories,
                    matched_terms=result.technical_result.matched_terms,
                    source_repository=onboarding_result.repository_name,
                    onboarding_decision=onboarding_result.onboarding_decision,
                    corpus_version=corpus_version,
                )
            )

        self._write_records(
            records=records,
            output_path=output_path,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _write_records(
        self,
        records: list[CuratedCorpusRecord],
        output_path: str,
    ) -> None:

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = [
            record.model_dump(
                mode="json",
            )
            for record in records
        ]

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                serialized,
                f,
                indent=2,
                ensure_ascii=False,
            )
