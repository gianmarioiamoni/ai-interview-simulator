# scripts/question_corpus/test_statistics_analyzer.py

from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader
from services.question_corpus.analyzers.corpus_statistics_analyzer import CorpusStatisticsAnalyzer


def main() -> None:

    loader = FolderCorpusLoader()

    analyzer = CorpusStatisticsAnalyzer()

    corpus = loader.load(
        "datasets/curated/interview_seed",
    )

    report = analyzer.analyze(
        corpus,
    )

    print("\nCORPUS STATISTICS REPORT\n")

    print(f"Questions: {report.total_questions}")

    print("\nROLES")

    for role, count in report.roles_distribution.items():

        print(f"- {role}: {count}")

    print("\nAREAS")

    for area, count in report.areas_distribution.items():

        print(f"- {area}: {count}")

    print("\nDOMAINS")

    for domain, count in report.domains_distribution.items():

        print(f"- {domain}: {count}")

    print("\nDIFFICULTIES")

    for difficulty, count in report.difficulty_distribution.items():

        print(f"- {difficulty}: {count}")

    print(f"\nAverage Quality: " f"{report.average_quality_score}")


if __name__ == "__main__":

    main()
