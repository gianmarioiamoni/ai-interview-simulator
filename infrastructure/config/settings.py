# infrastructure/config/settings.py

# Settings
#
# Responsibility:
# Centralized configuration management.
# Loads environment variables and provides type-safe access.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Credentials ──────────────────────────────────────────────────────────
    openai_api_key: str = ""
    hf_token: str | None = None

    # ── Chat model ───────────────────────────────────────────────────────────
    chat_model: str = "gpt-4o-mini"

    # Temperature for the primary LangChain LLM factory (deterministic).
    chat_temperature: float = 0.0

    # Temperature for the direct OpenAI SDK client (slightly creative answers).
    openai_client_temperature: float = 0.3

    # ── Embedding models ─────────────────────────────────────────────────────
    # OpenAI embeddings used for Chroma corpus build and retrieval.
    openai_embedding_model: str = "text-embedding-3-small"

    # Local SentenceTransformer model used for semantic dedup and planning.
    local_embedding_model: str = "all-MiniLM-L6-v2"

    # ── Application-level LLM retry counts ───────────────────────────────────
    # JSON parse/validation retries inside DefaultLLMAdapter.invoke_json.
    llm_json_retry_attempts: int = 2

    # JSON parse retries inside CodingQuestionGenerator.
    coding_json_retry_attempts: int = 3

    # Full-generation retries inside CodingQuestionPipeline.
    coding_pipeline_retry_attempts: int = 2

    # Full-generation retries inside SQLQuestionPipeline.
    sql_pipeline_retry_attempts: int = 2

    # Generation retries inside AITestGenerator.
    test_generation_retry_attempts: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=(),
        extra="ignore",
    )


settings = Settings()
