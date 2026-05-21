# services/planning/semantic_novelty_bonus_engine.py

from sentence_transformers import (
    SentenceTransformer,
)

from sentence_transformers.util import (
    cos_sim,
)

from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)


class SemanticNoveltyBonusEngine:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        novelty_threshold: float = 0.35,
        novelty_bonus: float = 0.30,
        embedding_model: str = ("all-MiniLM-L6-v2"),
    ) -> None:

        self._threshold = novelty_threshold

        self._bonus = novelty_bonus

        self._model = SentenceTransformer(embedding_model)

    # =====================================================
    # PUBLIC
    # =====================================================

    def apply_bonus(
        self,
        candidate: QuestionBankItem,
        selected_questions: list[QuestionBankItem],
        current_score: float,
    ) -> float:

        if not selected_questions:
            return current_score

        average_similarity = self._average_similarity(
            candidate,
            selected_questions,
        )

        if average_similarity > (self._threshold):
            return current_score

        boosted = current_score + self._bonus

        return round(
            boosted,
            4,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _average_similarity(
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

        return sum(similarities) / len(similarities)
