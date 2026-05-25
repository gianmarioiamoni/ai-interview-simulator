# services/planning/semantic_cluster_suppressor.py

from sentence_transformers.util import cos_sim

from domain.contracts.question.question_bank_item import QuestionBankItem

from services.embedding.embedding_model_provider import EmbeddingModelProvider


class SemanticClusterSuppressor:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        similarity_threshold: float = 0.70,
        suppression_penalty: float = 0.40,
    ) -> None:

        self._threshold = similarity_threshold

        self._penalty = suppression_penalty

        self._model = EmbeddingModelProvider.get_model()

    # =====================================================
    # PUBLIC
    # =====================================================

    def apply_penalty(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
        current_score: float,
    ) -> float:

        if not selected_questions:
            return current_score

        highest_similarity = self._highest_similarity(
            candidate,
            selected_questions,
        )

        if highest_similarity < (self._threshold):
            return current_score

        adjusted = current_score - self._penalty

        return round(
            adjusted,
            4,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _highest_similarity(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
    ) -> float:

        candidate_embedding = self._model.encode(
            candidate.text,
            convert_to_tensor=True,
        )

        similarities: list[float] = []

        for selected in selected_questions:

            selected_embedding = self._model.encode(
                selected.text,
                convert_to_tensor=True,
            )

            similarity = cos_sim(
                candidate_embedding,
                selected_embedding,
            )

            similarities.append(float(similarity.item()))

        if not similarities:
            return 0.0

        return max(similarities)
