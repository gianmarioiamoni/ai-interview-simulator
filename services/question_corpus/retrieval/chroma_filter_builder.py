# services/question_corpus/retrieval/chroma_filter_builder.py

from services.question_corpus.contracts.retrieval_filters import RetrievalFilters


class ChromaFilterBuilder:

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        filters: RetrievalFilters,
    ) -> dict:

        conditions: list[dict] = []

        # -------------------------------------------------
        # ROLE
        # -------------------------------------------------

        if filters.role:

            conditions.append(
                {
                    "role": filters.role,
                }
            )

        # -------------------------------------------------
        # SENIORITY
        # -------------------------------------------------

        if filters.seniority:

            seniority_values = [v.strip() for v in filters.seniority.split(",") if v.strip()]

            if len(seniority_values) == 1:
                conditions.append({"seniority": seniority_values[0]})
            else:
                conditions.append({"seniority": {"$in": seniority_values}})

        # -------------------------------------------------
        # AREA
        # -------------------------------------------------

        if filters.area:

            conditions.append(
                {
                    "area": filters.area,
                }
            )

        # -------------------------------------------------
        # MIN DIFFICULTY
        # -------------------------------------------------

        if filters.min_difficulty is not None:

            conditions.append(
                {
                    "difficulty": {
                        "$gte": filters.min_difficulty,
                    }
                }
            )

        # -------------------------------------------------
        # MAX DIFFICULTY
        # -------------------------------------------------

        if filters.max_difficulty is not None:

            conditions.append(
                {
                    "difficulty": {
                        "$lte": filters.max_difficulty,
                    }
                }
            )

        # -------------------------------------------------
        # EMPTY
        # -------------------------------------------------

        if not conditions:
            return {}

        # -------------------------------------------------
        # SINGLE CONDITION
        # -------------------------------------------------

        if len(conditions) == 1:
            return conditions[0]

        # -------------------------------------------------
        # MULTI CONDITION
        # -------------------------------------------------

        return {
            "$and": conditions,
        }
