# services/question_ingestion/heading_semantic_classifier.py


class HeadingSemanticClassifier:

    INVALID_HEADINGS = {
        "overview",
        "summary",
        "notes",
        "references",
        "links",
        "resources",
        "introduction",
    }

    # =====================================================
    # PUBLIC
    # =====================================================

    def is_semantic(
        self,
        heading: str,
    ) -> bool:

        normalized = heading.strip().lower()

        if not normalized:
            return False

        if normalized in self.INVALID_HEADINGS:
            return False

        if len(normalized.split()) > 8:
            return False

        return True
