# services/embedding/embedding_model_provider.py

from sentence_transformers import SentenceTransformer

from services.embedding.embedding_config import DEFAULT_EMBEDDING_MODEL


class EmbeddingModelProvider:

    # =====================================================
    # SINGLETON STATE
    # =====================================================

    _model: SentenceTransformer | None = None

    _model_name = DEFAULT_EMBEDDING_MODEL

    # =====================================================
    # PUBLIC
    # =====================================================

    @classmethod
    def get_model(
        cls,
    ) -> SentenceTransformer:

        if cls._model is None:

            cls._model = SentenceTransformer(
                cls._model_name
            )

        return cls._model

    @classmethod
    def get_model_name(
        cls,
    ) -> str:

        return cls._model_name
