# services/question_ingestion/github_repository_downloader.py

import subprocess
from pathlib import Path

from services.question_ingestion.contracts.github_corpus_source import (
    GitHubCorpusSource,
)


class GitHubRepositoryDownloader:

    RAW_ROOT = Path("datasets/raw/github")

    # =====================================================
    # PUBLIC
    # =====================================================

    def download(
        self,
        source: GitHubCorpusSource,
    ) -> Path:

        self.RAW_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        target_path = self.RAW_ROOT / source.repository_name

        # -------------------------------------------------
        # UPDATE EXISTING
        # -------------------------------------------------

        if target_path.exists():

            subprocess.run(
                ["git", "-C", str(target_path), "pull"],
                check=True,
            )

            return target_path

        # -------------------------------------------------
        # CLONE
        # -------------------------------------------------

        subprocess.run(
            [
                "git",
                "clone",
                "--branch",
                source.branch,
                source.repository_url,
                str(target_path),
            ],
            check=True,
        )

        return target_path
