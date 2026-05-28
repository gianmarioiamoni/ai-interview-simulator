# services/question_ingestion/github_corpus_onboarding_pipeline.py

from pathlib import Path

from services.question_ingestion.contracts.github_corpus_source import GitHubCorpusSource
from services.question_ingestion.github_repository_scanner import GitHubRepositoryScanner
from services.question_ingestion.corpus_onboarding_service import CorpusOnboardingService
from services.question_ingestion.curated_corpus_storage import CuratedCorpusStorage


class GitHubCorpusOnboardingPipeline:

    CURATED_ROOT = Path("datasets/curated/github")

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
    ) -> None:

        self._scanner = GitHubRepositoryScanner()

        self._onboarding_service = CorpusOnboardingService()

        self._storage = CuratedCorpusStorage()

    # =====================================================
    # PUBLIC
    # =====================================================

    def onboard_repository(
        self,
        repository_path: Path,
        source: GitHubCorpusSource,
        corpus_version: str = "v1",
    ) -> None:

        documents = self._scanner.scan(
            repository_path=repository_path,
            source=source,
        )

        for document in documents:

            onboarding_result = self._onboarding_service.onboard(
                document=document,
            )

            # -------------------------------------------------
            # SKIP EMPTY RESULTS ONLY
            # -------------------------------------------------

            if not onboarding_result.accepted_results:
                continue

            output_path = self._build_output_path(
                source=source,
                document_path=document.path,
            )

            self._storage.persist(
                onboarding_result=onboarding_result,
                output_path=str(output_path),
                corpus_version=corpus_version,
            )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _build_output_path(
        self,
        source: GitHubCorpusSource,
        document_path: str,
    ) -> Path:

        sanitized = (
            document_path.replace("/", "_")
            .replace(".md", ".json")
            .replace(".markdown", ".json")
        )

        return self.CURATED_ROOT / source.repository_name / sanitized
