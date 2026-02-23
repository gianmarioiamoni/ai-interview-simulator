# infrastructure/config/settings.py

# Settings
#
# Responsibility:
# Centralized configuration management.
# Loads environment variables and provides type-safe access.

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
