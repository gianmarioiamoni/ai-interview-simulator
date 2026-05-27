# services/question_ingestion/github_corpus_registry_loader.py

import json
from pathlib import Path

from services.question_ingestion.contracts.github_corpus_source import (
    GitHubCorpusSource,
)


class GitHubCorpusRegistryLoader:

    REGISTRY_PATH = Path("datasets/github_corpus_registry.json")

    # =====================================================
    # PUBLIC
    # =====================================================

    def load(
        self,
    ) -> list[GitHubCorpusSource]:

        with open(
            self.REGISTRY_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return [GitHubCorpusSource(**item) for item in data]
