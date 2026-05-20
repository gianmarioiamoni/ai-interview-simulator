# services/retrieval/semantic_retrieval_engine.py

from services.retrieval.contracts import (
    RetrievalCorpusRecord,
    RetrievalQuery,
    RetrievalResult,
)


class SemanticRetrievalEngine:

    # =====================================================
    # PUBLIC
    # =====================================================

    def retrieve(
        self,
        query: RetrievalQuery,
        corpus: list[RetrievalCorpusRecord],
    ) -> list[RetrievalResult]:

        results: list[RetrievalResult] = []

        query_terms = self._tokenize(query.text)

        for record in corpus:

            # ---------------------------------------------
            # FILTERING
            # ---------------------------------------------

            if record.retrieval_score < query.minimum_score:
                continue

            # ---------------------------------------------
            # MATCHING
            # ---------------------------------------------

            matched_tags = [
                tag for tag in (record.retrieval_tags) if (tag.lower() in query_terms)
            ]

            matched_categories = [
                category
                for category in (record.semantic_categories)
                if (category in query.preferred_categories)
            ]

            # ---------------------------------------------
            # SEMANTIC OVERLAP
            # ---------------------------------------------

            overlap_signals = len(matched_tags) + len(matched_categories)

            required_matches = [
                tag for tag in (query.required_tags) if (tag in record.retrieval_tags)
            ]

            overlap_signals += len(required_matches)

            semantic_overlap = overlap_signals / 5

            semantic_overlap = min(semantic_overlap, 1.0)

            # ---------------------------------------------
            # ADMISSIBILITY
            # ---------------------------------------------

            is_admissible = semantic_overlap >= 0.2

            if not is_admissible:
                continue

            # ---------------------------------------------
            # SCORE
            # ---------------------------------------------

            score = record.retrieval_score

            # ---------------------------------------------
            # TAG BOOST
            # ---------------------------------------------

            score += len(matched_tags) * 0.2

            # ---------------------------------------------
            # CATEGORY BOOST
            # ---------------------------------------------

            score += len(matched_categories) * 0.3

            # ---------------------------------------------
            # REQUIRED TAGS BOOST
            # ---------------------------------------------

            score += len(required_matches) * 0.5

            results.append(
                RetrievalResult(
                    record=record,
                    final_score=(round(score, 2)),
                    matched_tags=(matched_tags),
                    matched_categories=(matched_categories),
                    semantic_overlap=(
                        round(
                            semantic_overlap,
                            2,
                        )
                    ),
                    is_admissible=(is_admissible),
                )
            )

        # -------------------------------------------------
        # SORTING
        # -------------------------------------------------

        results.sort(
            key=lambda result: (result.final_score),
            reverse=True,
        )

        return results[: query.top_k]

    # =====================================================
    # INTERNALS
    # =====================================================

    def _tokenize(
        self,
        text: str,
    ) -> set[str]:

        return {token.strip().lower() for token in (text.split()) if token.strip()}
