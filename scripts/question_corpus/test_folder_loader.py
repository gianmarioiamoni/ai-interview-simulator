# scripts/question_corpus/test_folder_loader.py

from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.builders.corpus_statistics_builder import CorpusStatisticsBuilder


def main() -> None:

    loader = FolderCorpusLoader()

    statistics_builder = CorpusStatisticsBuilder()

    corpus = loader.load("datasets/curated/interview_seed")

    stats = statistics_builder.build(
        corpus,
    )

    print("\nCORPUS STATISTICS\n")

    print(f"Questions: {stats.total_questions}")
    print(f"Roles: {stats.total_roles}")
    print(f"Areas: {stats.total_areas}")
    print(f"Domains: {stats.total_domains}")
    print(f"Average Quality: {stats.average_quality_score}")


if __name__ == "__main__":

    main()
