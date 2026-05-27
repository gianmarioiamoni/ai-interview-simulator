# services/question_ingestion/cli/acquire_github_corpora.py

from services.question_ingestion.github_corpus_registry_loader import (
    GitHubCorpusRegistryLoader,
)

from services.question_ingestion.github_repository_downloader import (
    GitHubRepositoryDownloader,
)


def main() -> None:

    print("\nGITHUB CORPUS ACQUISITION\n")

    loader = GitHubCorpusRegistryLoader()

    downloader = GitHubRepositoryDownloader()

    sources = loader.load()

    for source in sources:

        if not source.enabled:
            continue

        print(f"\n[DOWNLOADING] {source.repository_name}")

        path = downloader.download(
            source,
        )

        print(f"stored_at={path}")

    print("\nACQUISITION COMPLETED\n")


if __name__ == "__main__":

    main()
