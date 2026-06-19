# infrastructure/config/settings.py

# Settings
#
# Responsibility:
# Centralized configuration management.
# Loads environment variables and provides type-safe access.

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Self


class Settings(BaseSettings):
    # ── Credentials ──────────────────────────────────────────────────────────
    openai_api_key: str = ""
    hf_token: str | None = None

    # ── Corpus ───────────────────────────────────────────────────────────────
    # HF Dataset repo ID containing the pre-built Chroma corpus artifact.
    # Required at startup when no local corpus is present.
    corpus_hf_repo: str | None = None

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

    # ── Humanizer feature flags ───────────────────────────────────────────────
    # Enable the Humanizer subsystem (conversational question framing).
    humanizer_enabled: bool = True

    # Enable FOLLOW_UP decisions in the Humanizer policy engine.
    # Requires humanizer_enabled=True. Disabled by default until V1.1
    # (score propagation and timing fixes are prerequisites).
    humanizer_follow_up_enabled: bool = False

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

    @model_validator(mode="after")
    def validate_required_credentials(self) -> Self:
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required but not set. "
                "Set it in your environment or .env file."
            )
        return self


settings = Settings()
