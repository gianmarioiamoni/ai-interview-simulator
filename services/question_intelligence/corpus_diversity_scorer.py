# services/question_intelligence/corpus_diversity_scorer.py

from collections import Counter

from services.question_ingestion.contracts import (
    CuratedCorpusRecord,
)


class CorpusDiversityScorer:

    # =====================================================
    # PUBLIC
    # =====================================================

    def score(
        self,
        records: list[CuratedCorpusRecord],
    ) -> dict:

        if not records:

            return {
                "total_records": 0,
                "unique_categories": 0,
                "category_distribution": {},
                "dominant_category": None,
                "dominance_ratio": 0.0,
                "diversity_score": 0.0,
            }

        # -------------------------------------------------
        # CATEGORY EXTRACTION
        # -------------------------------------------------

        categories = []

        for record in records:

            categories.extend(record.matched_categories)

        counter = Counter(categories)

        total_categories = sum(counter.values())

        # -------------------------------------------------
        # DISTRIBUTION
        # -------------------------------------------------

        distribution = {}

        for category, count in counter.items():

            distribution[category] = round(
                count / total_categories,
                2,
            )

        # -------------------------------------------------
        # DOMINANCE
        # -------------------------------------------------

        dominant_category = None

        dominance_ratio = 0.0

        if counter:

            dominant_category = counter.most_common(1)[0][0]

            dominance_ratio = round(
                counter.most_common(1)[0][1] / total_categories,
                2,
            )

        # -------------------------------------------------
        # DIVERSITY SCORE
        # -------------------------------------------------

        unique_categories = len(counter)

        diversity_score = round(
            unique_categories / max(total_categories, 1),
            2,
        )

        return {
            "total_records": (len(records)),
            "unique_categories": (unique_categories),
            "category_distribution": (distribution),
            "dominant_category": (dominant_category),
            "dominance_ratio": (dominance_ratio),
            "diversity_score": (diversity_score),
        }
