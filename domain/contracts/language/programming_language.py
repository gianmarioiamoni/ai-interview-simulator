# domain/contracts/language/programming_language.py

from pydantic import BaseModel, Field


class ProgrammingLanguage(BaseModel):
    """First-class abstract domain concept representing a supported programming language.

    Not a string. Not a fixed enum. Concrete instances (Python, JavaScript,
    TypeScript) are registered in LanguageRegistry. Domain logic operates against
    this abstraction — never against concrete language names (ADR-019 I-20, I-22).

    ProgrammingLanguage has zero knowledge of:
    - sandbox technology (Docker, AST guard, JVM)
    - runtime environment (CPython, Node.js, JVM, LLVM)
    - execution engine details
    - container orchestration
    """

    language_id: str = Field(
        ..., min_length=1, description="Stable string key (e.g. 'python', 'javascript')"
    )
    display_name: str = Field(
        ..., min_length=1, description="Human-readable name (e.g. 'Python', 'JavaScript')"
    )
    language_version: str = Field(
        ..., min_length=1, description="Default runtime version (e.g. '3.12', '22')"
    )
    language_family: str = Field(
        ..., min_length=1, description="Language family identifier (e.g. 'python', 'javascript')"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
