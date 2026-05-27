# services/question_ingestion/cli/ingest_github_corpora.py

from pathlib import Path

from services.question_ingestion.github_corpus_registry_loader import GitHubCorpusRegistryLoader
from services.question_ingestion.github_repository_downloader import GitHubRepositoryDownloader
from services.question_ingestion.github_corpus_onboarding_pipeline import GitHubCorpusOnboardingPipeline


def main() -> None:

    print("\nGITHUB CORPUS INGESTION\n")

    loader = GitHubCorpusRegistryLoader()

    downloader = GitHubRepositoryDownloader()

    onboarding_pipeline = GitHubCorpusOnboardingPipeline()

    sources = loader.load()

    for source in sources:

        if not source.enabled:
            continue

        print(f"\n[PROCESSING] {source.repository_name}")

        repository_path = downloader.download(
            source,
        )

        onboarding_pipeline.onboard_repository(
            repository_path=Path(repository_path),
            source=source,
            corpus_version="v1",
        )

        print(f"[COMPLETED] {source.repository_name}")

    print("\nINGESTION COMPLETED\n")


if __name__ == "__main__":

    main()
