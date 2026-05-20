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

            required_matches = [
                tag for tag in (query.required_tags) if (tag in record.retrieval_tags)
            ]

            score += len(required_matches) * 0.5

            results.append(
                RetrievalResult(
                    record=record,
                    final_score=(round(score, 2)),
                    matched_tags=(matched_tags),
                    matched_categories=(matched_categories),
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
