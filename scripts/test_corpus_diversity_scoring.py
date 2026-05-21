# scripts/test_corpus_diversity_scoring.py

import json

from pathlib import Path

from services.question_ingestion.contracts import (
    CuratedCorpusRecord,
)

from services.question_intelligence.corpus_diversity_scorer import (
    CorpusDiversityScorer,
)


def main() -> None:

    # -------------------------------------------------
    # LOAD CURATED CORPUS
    # -------------------------------------------------

    corpus_path = "datasets/curated/github/" "backend_scalability.json"

    data = json.loads(
        Path(corpus_path).read_text(
            encoding="utf-8",
        )
    )

    records = [CuratedCorpusRecord(**item) for item in data]

    # -------------------------------------------------
    # SCORE
    # -------------------------------------------------

    scorer = CorpusDiversityScorer()

    result = scorer.score(
        records=records,
    )

    # -------------------------------------------------
    # OUTPUT
    # -------------------------------------------------

    print()

    print("CORPUS DIVERSITY SCORING")

    print()

    print(f"total_records: " f"{result['total_records']}")

    print()

    print(f"unique_categories: " f"{result['unique_categories']}")

    print()

    print(f"dominant_category: " f"{result['dominant_category']}")

    print()

    print(f"dominance_ratio: " f"{result['dominance_ratio']}")

    print()

    print(f"diversity_score: " f"{result['diversity_score']}")

    print()

    print("CATEGORY DISTRIBUTION")

    print()

    for (
        category,
        ratio,
    ) in result["category_distribution"].items():

        print(f"{category}: " f"{ratio}")

    print()


if __name__ == "__main__":

    main()
