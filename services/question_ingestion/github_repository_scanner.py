# services/question_ingestion/github_repository_scanner.py

from pathlib import Path

from services.question_ingestion.contracts.github_document import GitHubDocument
from services.question_ingestion.contracts.github_corpus_source import GitHubCorpusSource


class GitHubRepositoryScanner:

    # =====================================================
    # PUBLIC
    # =====================================================

    def scan(
        self,
        repository_path: Path,
        source: GitHubCorpusSource,
    ) -> list[GitHubDocument]:

        markdown_files = self._discover_markdown_files(
            repository_path=repository_path,
            source=source,
        )

        documents: list[GitHubDocument] = []

        for file_path in markdown_files:

            try:

                content = file_path.read_text(
                    encoding="utf-8",
                )

            except Exception:
                continue

            relative_path = file_path.relative_to(
                repository_path,
            )

            documents.append(
                GitHubDocument(
                    path=str(relative_path),
                    content=content,
                    repository=source.repository_name,
                    branch=source.branch,
                )
            )

        return documents

    # =====================================================
    # INTERNALS
    # =====================================================

    def _discover_markdown_files(
        self,
        repository_path: Path,
        source: GitHubCorpusSource,
    ) -> list[Path]:

        discovered: list[Path] = []

        for file_path in repository_path.rglob("*"):

            if not file_path.is_file():
                continue

            if not self._is_allowed_extension(
                file_path=file_path,
                source=source,
            ):
                continue

            relative_path = str(file_path.relative_to(repository_path))

            if self._is_excluded(
                relative_path=relative_path,
                source=source,
            ):
                continue

            if not self._is_included(
                relative_path=relative_path,
                source=source,
            ):
                continue

            discovered.append(file_path)

        return discovered

    def _is_allowed_extension(
        self,
        file_path: Path,
        source: GitHubCorpusSource,
    ) -> bool:

        return file_path.suffix.lower() in source.allowed_extensions

    def _is_excluded(
        self,
        relative_path: str,
        source: GitHubCorpusSource,
    ) -> bool:

        for excluded in source.exclude_paths:

            if excluded in relative_path:
                return True

        return False

    def _is_included(
        self,
        relative_path: str,
        source: GitHubCorpusSource,
    ) -> bool:

        if not source.include_paths:
            return True

        for included in source.include_paths:

            if included in relative_path:
                return True

        return False
