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

    # ── Context profile prompt limits ────────────────────────────────────────
    # Maximum characters of job_description injected into generation prompts.
    job_description_max_chars: int = 500

    # Maximum characters of company_description injected into generation prompts.
    company_description_max_chars: int = 200

    # Minimum keyword score required for BusinessContext classification.
    # A score below this threshold falls back to GENERIC.
    business_context_min_keyword_score: int = 2

    # ── Coding domain profile feature flags ──────────────────────────────────
    # Enable CodingDomainProfile-driven framing in coding question prompts.
    coding_domain_profile_enabled: bool = True

    # Enable scenario anchor sampling from CodingDomainProfile.scenario_anchor_pool.
    coding_scenario_anchor_enabled: bool = True

    # Enable domain vocabulary injection from CodingDomainProfile.vocabulary_hint.
    coding_domain_vocabulary_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=(),
        extra="ignore",
    )


settings = Settings()
