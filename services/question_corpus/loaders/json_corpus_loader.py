# services/question_corpus/loaders/json_corpus_loader.py

import json

from pathlib import Path

from domain.contracts.corpus.curated_question import CuratedQuestion

from services.question_corpus.contracts.curated_corpus import CuratedCorpus


class JsonCorpusLoader:

    # =====================================================
    # PUBLIC
    # =====================================================

    def load(
        self,
        path: str,
    ) -> CuratedCorpus:

        corpus_path = Path(path)

        with open(
            corpus_path,
            "r",
            encoding="utf-8",
        ) as f:

            raw_data = json.load(f)

        questions = [CuratedQuestion(**item) for item in raw_data]

        return CuratedCorpus(
            questions=questions,
        )
