# domain/contracts/language/__init__.py
# Language Independence Layer — Domain contracts (ADR-019, E00-M1)

from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.language.language_family import LanguageFamily
from domain.contracts.language.language_registry import LanguageRegistry, PYTHON, JAVASCRIPT, TYPESCRIPT
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy
from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.language.language_config import LanguageConfig

__all__ = [
    "ProgrammingLanguage",
    "LanguageFamily",
    "LanguageRegistry",
    "PYTHON",
    "JAVASCRIPT",
    "TYPESCRIPT",
    "LanguageSelectionStrategy",
    "ExecutionPolicy",
    "LanguagePolicy",
    "LanguageProfile",
    "SessionMode",
    "LanguageCapability",
    "LanguageConfig",
]
