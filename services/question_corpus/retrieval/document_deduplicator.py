# services/question_corpus/retrieval/document_deduplicator.py

from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate

class DocumentDeduplicator:

    def deduplicate(
        self,
        candidates: list[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:

        seen = set()

        result = []

        for candidate in candidates:

            document_id = candidate.document.metadata.get(
                "document_id",
                "",
            )

            if document_id in seen:
                continue

            seen.add(document_id)

            result.append(candidate)

        return result
