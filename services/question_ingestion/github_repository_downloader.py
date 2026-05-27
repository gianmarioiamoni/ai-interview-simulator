# services/question_ingestion/github_repository_downloader.py

import shutil
import subprocess

from pathlib import Path

from services.question_ingestion.contracts.github_corpus_source import GitHubCorpusSource


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
                [
                    "git",
                    "-C",
                    str(target_path),
                    "pull",
                ],
                check=True,
            )

            return target_path

        # -------------------------------------------------
        # CLONE WITH FALLBACK
        # -------------------------------------------------

        branches_to_try = []

        if source.branch:
            branches_to_try.append(source.branch)

        for fallback in ["main", "master"]:

            if fallback not in branches_to_try:
                branches_to_try.append(fallback)

        last_error = None

        for branch in branches_to_try:

            try:

                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--branch",
                        branch,
                        source.repository_url,
                        str(target_path),
                    ],
                    check=True,
                )

                return target_path

            except subprocess.CalledProcessError as e:

                last_error = e

                # -----------------------------------------
                # CLEAN FAILED PARTIAL CLONE
                # -----------------------------------------

                if target_path.exists():

                    shutil.rmtree(
                        target_path,
                        ignore_errors=True,
                    )

        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        if last_error is not None:
            raise last_error

        raise RuntimeError(("Unable to clone repository: " f"{source.repository_url}"))
