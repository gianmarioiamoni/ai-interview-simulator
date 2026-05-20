# services/retrieval/embedding_generator.py

from sentence_transformers import (
    SentenceTransformer,
)

from services.retrieval.contracts import (
    RetrievalCorpusRecord,
    EmbeddingRecord,
)


class EmbeddingGenerator:

    # =====================================================
    # INIT
    # =====================================================

    def __init__(self) -> None:

        self._model = SentenceTransformer("all-MiniLM-L6-v2")

    # =====================================================
    # PUBLIC
    # =====================================================

    def generate(
        self,
        records: list[RetrievalCorpusRecord],
    ) -> list[EmbeddingRecord]:

        texts = [record.content for record in records]

        vectors = self._model.encode(
            texts,
            convert_to_numpy=True,
        )

        results: list[EmbeddingRecord] = []

        for record, vector in zip(
            records,
            vectors,
        ):

            results.append(
                EmbeddingRecord(
                    content=(record.content),
                    embedding=(vector.tolist()),
                    retrieval_record=(record),
                )
            )

        return results
