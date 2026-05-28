# services/question_corpus/loaders/folder_corpus_loader.py

from pathlib import Path

from domain.contracts.corpus.curated_question import CuratedQuestion

from services.question_corpus.contracts.curated_corpus import CuratedCorpus
from services.question_corpus.loaders.json_corpus_loader import JsonCorpusLoader


class FolderCorpusLoader:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._json_loader = JsonCorpusLoader()

    # =====================================================
    # PUBLIC
    # =====================================================

    def load(
        self,
        root_path: str,
    ) -> CuratedCorpus:

        root = Path(root_path)

        questions: list[CuratedQuestion] = []

        for file_path in root.rglob("*.json"):

            corpus = self._json_loader.load(
                str(file_path),
            )

            questions.extend(corpus.questions)

        return CuratedCorpus(
            questions=questions,
        )
