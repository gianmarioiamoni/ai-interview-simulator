# services/question_corpus/adapters/chroma_result_adapter.py

from langchain_core.documents import Document

from services.question_corpus.contracts.retrieval_result import (
    RetrievalResult,
)


class ChromaResultAdapter:

    # =====================================================
    # PUBLIC
    # =====================================================

    def adapt(
        self,
        raw_results: dict,
    ) -> list[RetrievalResult]:

        documents = raw_results["documents"][0]

        metadatas = raw_results["metadatas"][0]

        distances = raw_results["distances"][0]

        embeddings = raw_results["embeddings"][0]

        results: list[RetrievalResult] = []

        for (
            content,
            metadata,
            distance,
            embedding,
        ) in zip(
            documents,
            metadatas,
            distances,
            embeddings,
        ):

            document = Document(
                page_content=content,
                metadata=metadata,
            )

            semantic_score = max(
                0.0,
                1.0 - distance,
            )

            quality_score = float(
                metadata.get(
                    "quality_score",
                    0.5,
                )
            )

            result = RetrievalResult(
                document=document,
                distance=distance,
                embedding=embedding,
                semantic_score=round(
                    semantic_score,
                    3,
                ),
                quality_score=round(
                    quality_score,
                    3,
                ),
            )

            results.append(
                result,
            )

        return results
