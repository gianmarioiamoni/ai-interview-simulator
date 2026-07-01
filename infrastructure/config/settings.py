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
    # Requires humanizer_enabled=True. Activated in V1.1.
    humanizer_follow_up_enabled: bool = True

    # ── Follow-up configuration (single source of truth) ─────────────────────
    # Score threshold to trigger a follow-up (Quality.OPTIMAL.rank() = 4).
    follow_up_score_threshold: int = 4

    # Maximum follow-up turns per interview session.
    max_follow_ups_per_interview: int = 2

    # Fraction of planned questions eligible for follow-up (0.0–1.0).
    follow_up_percentage: float = 0.20

    # Selector policy: "percentage" uses follow_up_percentage; "fixed" uses max_follow_ups.
    follow_up_selector_policy: str = "percentage"

    # Minimum character length for a generated follow-up message to be accepted.
    follow_up_min_length: int = 20

    # Maximum characters of the candidate answer passed into the humanizer prompt.
    follow_up_max_input_chars: int = 800

    # Minimum number of qualifying keywords (≥4 chars, non-stopword) that must
    # overlap between last_answer and the generated follow-up message.
    follow_up_min_keyword_overlap: int = 1

    # Comma-separated InterviewArea values allowed for follow-up.
    # Empty string means all WRITTEN areas are allowed.
    follow_up_allowed_areas: str = ""

    # Comma-separated QuestionType values allowed for follow-up.
    follow_up_allowed_types: str = "written"

    # Emit structured log entries for follow-up trigger/skip events.
    follow_up_logging_enabled: bool = True

    # Sanitize candidate answer input before humanizer prompt construction.
    follow_up_sanitize_input: bool = True

    # ── Coding domain profile feature flags ──────────────────────────────────
    # Enable CodingDomainProfile-driven framing in coding question prompts.
    coding_domain_profile_enabled: bool = True

    # Enable scenario anchor sampling from CodingDomainProfile.scenario_anchor_pool.
    coding_scenario_anchor_enabled: bool = True

    # Enable domain vocabulary injection from CodingDomainProfile.vocabulary_hint.
    coding_domain_vocabulary_enabled: bool = True

    # --- Interview Reasoner (V1.1 M2, ADR-034) ---
    # CoverageDetector stays silent until this many questions have been answered.
    # Prevents false navigation triggers at session start.
    reasoner_coverage_min_questions: int = 2

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
