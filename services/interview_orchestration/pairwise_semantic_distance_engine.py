# services/interview_orchestration/pairwise_semantic_distance_engine.py

from itertools import combinations

from sentence_transformers import (
    SentenceTransformer,
)

from sentence_transformers.util import (
    cos_sim,
)

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class PairwiseSemanticDistanceEngine:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        embedding_model: str = ("all-MiniLM-L6-v2"),
    ) -> None:

        self._model = SentenceTransformer(embedding_model)

    # =====================================================
    # PUBLIC
    # =====================================================

    def calculate_average_similarity(
        self,
        questions: list[QuestionBankItem],
    ) -> float:

        if len(questions) < 2:
            return 0.0

        similarities: list[float] = []

        for first, second in combinations(
            questions,
            2,
        ):

            similarity = self._similarity(
                first.text,
                second.text,
            )

            similarities.append(similarity)

        if not similarities:
            return 0.0

        return round(
            sum(similarities) / len(similarities),
            4,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _similarity(
        self,
        first: str,
        second: str,
    ) -> float:

        embeddings = self._model.encode(
            [first, second],
            convert_to_tensor=True,
        )

        similarity = cos_sim(
            embeddings[0],
            embeddings[1],
        )

        return float(similarity.item())
