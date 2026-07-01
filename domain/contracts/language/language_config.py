# domain/contracts/language/language_config.py

from pydantic import BaseModel, Field, model_validator

from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy


class LanguageConfig(BaseModel):
    """Application-layer interview language configuration.

    LanguageConfig answers: "what language options are configured for this interview?"
    It is the input to InterviewSetup, which resolves it into an immutable LanguageProfile.

    V1.2 supported enabled_languages combinations (ADR-019 Section E):
    - [python]               → Python-only session
    - [javascript]           → JavaScript-only session
    - [typescript]           → TypeScript-only session
    - [python, javascript]   → Mixed Python + JavaScript session
    - [python, typescript]   → Mixed Python + TypeScript session

    No other combinations are supported in V1.2.

    Domain invariants:
    - primary_language must be in enabled_languages.
    - mixed_mode is always derived from len(enabled_languages) > 1.
    - In V1.2, selection_strategy must be DETERMINISTIC_ALTERNATING for mixed sessions.
    - metadata is reserved for V1.3+; V1.2 logic ignores it entirely.
    """

    enabled_languages: list[ProgrammingLanguage] = Field(
        ..., min_length=1, max_length=2,
        description="Languages active for this interview; 1 (single) or 2 (mixed)"
    )
    primary_language: ProgrammingLanguage = Field(
        ..., description="Default language; receives extra question in odd-count mixed sessions"
    )
    selection_strategy: LanguageSelectionStrategy = Field(
        default=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
        description="Language assignment algorithm for mixed-mode sessions"
    )
    execution_policies: list[ExecutionPolicy] = Field(
        default_factory=list,
        description="Execution parameters per enabled_language; may be empty (uses defaults)"
    )
    evaluation_policies: list[LanguagePolicy] = Field(
        default_factory=list,
        description="LanguagePolicy per enabled_language active for this interview"
    )
    # Reserved for V1.3+ — tenant overrides, experiment flags, custom language config.
    # V1.2 logic MUST NOT read or write this field.
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Reserved for V1.3+ extensions; ignored entirely by V1.2 logic"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def mixed_mode(self) -> bool:
        """Derived property — True when more than one language is enabled."""
        return len(self.enabled_languages) > 1

    @model_validator(mode="after")
    def validate_consistency(self) -> "LanguageConfig":
        enabled_ids = {lang.language_id for lang in self.enabled_languages}

        if self.primary_language.language_id not in enabled_ids:
            raise ValueError(
                f"primary_language '{self.primary_language.language_id}' "
                f"must be in enabled_languages {enabled_ids}"
            )

        # V1.2: mixed sessions must use DETERMINISTIC_ALTERNATING
        if self.mixed_mode and self.selection_strategy != LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING:
            raise ValueError(
                f"V1.2 mixed-mode sessions require DETERMINISTIC_ALTERNATING strategy; "
                f"got '{self.selection_strategy}'"
            )

        # execution_policies, if provided, must each reference an enabled language
        ep_ids = {ep.language_id for ep in self.execution_policies}
        for ep_id in ep_ids:
            if ep_id not in enabled_ids:
                raise ValueError(
                    f"ExecutionPolicy references language '{ep_id}' "
                    f"which is not in enabled_languages {enabled_ids}"
                )

        # evaluation_policies, if provided, must each reference an enabled language
        lp_ids = {lp.language_id for lp in self.evaluation_policies}
        for lp_id in lp_ids:
            if lp_id not in enabled_ids:
                raise ValueError(
                    f"LanguagePolicy references language '{lp_id}' "
                    f"which is not in enabled_languages {enabled_ids}"
                )

        return self
