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

        # -------------------------------------------------
        # RETURN CACHED MODEL
        # -------------------------------------------------

        if cls._model is not None:

            return cls._model

        # -------------------------------------------------
        # LOAD MODEL
        # -------------------------------------------------

        try:

            cls._model = SentenceTransformer(
                cls._model_name,
            )

            return cls._model

        # -------------------------------------------------
        # FALLBACK ERROR
        # -------------------------------------------------

        except Exception as exc:

            raise RuntimeError(
                (
                    "Failed to load embedding model "
                    f"'{cls._model_name}'. "
                    "Ensure internet connectivity or preload "
                    "the model locally before running offline."
                )
            ) from exc

    @classmethod
    def get_model_name(
        cls,
    ) -> str:

        return cls._model_name
