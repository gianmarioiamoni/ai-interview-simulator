# domain/contracts/language/language_family.py

from enum import Enum


class LanguageFamily(str, Enum):
    """Taxonomy of programming language families supported by the platform.

    Languages within the same family share syntax ancestry and often have
    compatible execution environments. Used for mixed-mode session configuration
    and coverage balancing (ADR-019 Section F).

    Domain invariant: LanguageFamily groupings are structural metadata only.
    They do not alter EvaluationDimension weights, EvidenceSignal semantics,
    ObservationType vocabulary, or ProfileFeature taxonomy.
    """

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    # TypeScript shares execution family with JavaScript (Node.js runtime)
    TYPESCRIPT = "typescript"
    # Reserved for future registration — zero domain redesign required (ADR-019 K)
    JVM = "jvm"          # Java, Kotlin, Scala
    SYSTEMS = "systems"  # Go, Rust, C, C++
    DOTNET = "dotnet"    # C#, F#
    OTHER = "other"      # Swift, Ruby, PHP, etc.
