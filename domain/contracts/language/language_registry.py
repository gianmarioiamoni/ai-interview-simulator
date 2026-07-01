# domain/contracts/language/language_registry.py

from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.language.language_family import LanguageFamily


# V1.2 canonical language instances — the only concrete language objects in
# the domain layer. All domain logic that needs a language reference imports
# from here rather than constructing ProgrammingLanguage ad-hoc (ADR-019 I-20).
PYTHON = ProgrammingLanguage(
    language_id="python",
    display_name="Python",
    language_version="3.12",
    language_family=LanguageFamily.PYTHON,
)

JAVASCRIPT = ProgrammingLanguage(
    language_id="javascript",
    display_name="JavaScript",
    language_version="22",
    language_family=LanguageFamily.JAVASCRIPT,
)

TYPESCRIPT = ProgrammingLanguage(
    language_id="typescript",
    display_name="TypeScript",
    language_version="5.4",
    language_family=LanguageFamily.TYPESCRIPT,
)


class LanguageRegistry:
    """Authoritative, static registry of all supported ProgrammingLanguages.

    The registry is the single source of truth for which languages the platform
    supports. All domain logic resolves languages through this registry; no
    component may reference a concrete language by string or construct
    ProgrammingLanguage instances outside this module (ADR-019 I-20).

    Extension: register a new language by adding a module-level constant and
    a registry entry below. Zero changes required anywhere else in the domain.
    """

    _registry: dict[str, ProgrammingLanguage] = {
        PYTHON.language_id: PYTHON,
        JAVASCRIPT.language_id: JAVASCRIPT,
        TYPESCRIPT.language_id: TYPESCRIPT,
    }

    @classmethod
    def get(cls, language_id: str) -> ProgrammingLanguage:
        """Resolve a language by its stable id.

        Raises KeyError if the language is not registered.
        Domain code must not catch this exception — an unregistered language_id
        is always a programming error, not a runtime condition.
        """
        if language_id not in cls._registry:
            raise KeyError(
                f"Language '{language_id}' is not registered. "
                f"Registered languages: {list(cls._registry.keys())}"
            )
        return cls._registry[language_id]

    @classmethod
    def all(cls) -> list[ProgrammingLanguage]:
        """Return all registered languages in deterministic insertion order."""
        return list(cls._registry.values())

    @classmethod
    def ids(cls) -> list[str]:
        """Return all registered language_ids in deterministic insertion order."""
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, language_id: str) -> bool:
        """Return True if the given language_id is registered."""
        return language_id in cls._registry

    @classmethod
    def by_family(cls, family: "LanguageFamily") -> list[ProgrammingLanguage]:
        """Return all registered languages belonging to the given family."""
        return [lang for lang in cls._registry.values() if lang.language_family == family]
