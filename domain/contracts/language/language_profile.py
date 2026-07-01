# domain/contracts/language/language_profile.py

from enum import Enum
from pydantic import BaseModel, Field, model_validator

from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy


class SessionMode(str, Enum):
    """Mode of a coding session with respect to language coverage."""
    SINGLE = "single"   # One language; all coding questions in that language
    MIXED = "mixed"     # Two languages; questions alternate per selection strategy


class LanguageProfile(BaseModel):
    """Immutable, session-scoped language configuration produced by InterviewSetup.

    LanguageProfile is the frozen, resolved language state for a single session.
    It is produced from LanguageConfig at session start and never mutated thereafter.
    Stored in SessionHistory at session close.

    The full language_sequence is pre-computed at session start to guarantee
    replay determinism: the same LanguageProfile always produces the same
    language assignment per question index (ADR-019 Section F, invariant 4).

    Domain invariants:
    - primary_language must be in active_languages.
    - In SINGLE mode, active_languages has exactly one entry.
    - In MIXED mode, active_languages has exactly two entries.
    - language_sequence is deterministic for a given LanguageProfile (replay fidelity).
    """

    session_id: str = Field(
        ..., min_length=1, description="Session this profile belongs to"
    )
    session_mode: SessionMode
    primary_language: ProgrammingLanguage
    active_languages: list[ProgrammingLanguage] = Field(
        ..., min_length=1, max_length=2,
        description="Ordered list of active languages; 1 for single, 2 for mixed"
    )
    selection_strategy: LanguageSelectionStrategy
    # Pre-computed language sequence for deterministic question assignment.
    # Index i → language for coding question i (0-based).
    # Length == expected number of coding questions in the session.
    language_sequence: list[str] = Field(
        default_factory=list,
        description="Pre-computed language_id per coding question index"
    )
    execution_policies: list[ExecutionPolicy] = Field(
        default_factory=list,
        description="One ExecutionPolicy per active_language, in the same order"
    )
    language_policies: list[LanguagePolicy] = Field(
        default_factory=list,
        description="One LanguagePolicy per active_language, in the same order"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def validate_consistency(self) -> "LanguageProfile":
        active_ids = {lang.language_id for lang in self.active_languages}

        if self.primary_language.language_id not in active_ids:
            raise ValueError(
                f"primary_language '{self.primary_language.language_id}' "
                f"must be in active_languages {active_ids}"
            )

        if self.session_mode == SessionMode.SINGLE and len(self.active_languages) != 1:
            raise ValueError(
                "SINGLE session_mode requires exactly one active_language; "
                f"got {len(self.active_languages)}"
            )

        if self.session_mode == SessionMode.MIXED and len(self.active_languages) != 2:
            raise ValueError(
                "MIXED session_mode requires exactly two active_languages; "
                f"got {len(self.active_languages)}"
            )

        # language_sequence entries must reference registered active language_ids
        for entry in self.language_sequence:
            if entry not in active_ids:
                raise ValueError(
                    f"language_sequence entry '{entry}' is not in active_languages {active_ids}"
                )

        return self
