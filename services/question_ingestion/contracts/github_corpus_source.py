# services/question_ingestion/contracts/github_corpus_source.py

from pydantic import BaseModel, Field


class GitHubCorpusSource(BaseModel):

    # =====================================================
    # REPOSITORY
    # =====================================================

    repository_name: str

    repository_url: str

    branch: str = "main"

    # =====================================================
    # FILTERING
    # =====================================================

    include_paths: list[str] = Field(default_factory=list)

    exclude_paths: list[str] = Field(default_factory=list)

    allowed_extensions: list[str] = Field(
        default_factory=lambda: [
            ".md",
            ".markdown",
        ]
    )

    # =====================================================
    # DOMAIN METADATA
    # =====================================================

    domains: list[str] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)

    trust_score: float = 0.5

    enabled: bool = True

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
