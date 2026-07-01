# ADR-019 — Language Independence Layer & LanguageConfig Architecture

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Language Independence Layer
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, K0/K1/K2 frozen
**Supersedes:** ADR-019 v0 (LanguageConfig Design sketch — replaced by this document)
**Superseded by:** Nothing
**Related:** ADR-020, ADR-021, ADR-024, ADR-027, ADR-028, ADR-031

---

## Context

In V1.1, programming language was an execution flag — a string value passed through the pipeline. No formal layer boundary existed between language-specific concerns and language-agnostic domain logic. The platform was implicitly Python/JavaScript/TypeScript-only at every layer.

K2 Amendment A-5 elevated `ProgrammingLanguage` to a first-class abstract domain concept. ADR-018 froze the ProfileFeature taxonomy as language-independent. ADR-016/017 confirmed that language is metadata — not semantics — throughout the Observation layer.

What remained undefined:

- The three-layer separation (Domain / Application / Infrastructure) and what belongs where
- The complete `LanguageConfig` design — fields, mode support, selection strategy
- The V1.2 mixed-language interview policy
- The V1.2 coding scope boundary (what is in scope, what is explicitly out)
- The `FeatureIdentity` concept — semantic identity of a ProfileFeature across schema versions
- The complete runtime architecture validation
- The full future extensibility guarantee for Go, Java, Rust, C#, Kotlin, C++, Swift

This ADR freezes all of the above. It supersedes the v0 sketch of ADR-019 and is the authoritative Language Independence Layer architecture.

---

## Decision

**The Language Independence Layer is a three-layer separation: Domain / Application / Infrastructure.**

**Language affects only: execution, question repository, and evaluation adapter.**

**No component above the evaluation boundary may branch on language identity.**

---

## SECTION A — Purpose: Why Language Independence Must Be Structural

### The V1.1 Coupling Problem

In V1.1, language leaked across every boundary:

| Boundary | V1.1 coupling |
|---|---|
| Question generation | Branched on language string to select stubs |
| Execution routing | `if language == "python"` style dispatch |
| EvidenceSignal descriptions | Occasionally named the language explicitly |
| CandidateProfile | No formal separation between language-specific and language-agnostic knowledge |
| Coaching text | Implicitly Python-centric idiom references |

Every one of these couplings would require modification when adding a new language.

### The V1.2 Architectural Guarantee

The Language Independence Layer makes one structural guarantee: **adding any new language requires changes only below the evaluation boundary**. Everything above it — Observation, FeatureEngine, CandidateProfile, Narrative, Coaching, Report — requires zero modification.

This is not a convention. It is enforced by layer separation.

### The Three-Layer Separation

```
┌─────────────────────────────────────────────────────────┐
│  DOMAIN LAYER                                           │
│                                                         │
│  ProgrammingLanguage (abstract concept)                 │
│  LanguageRegistry    (static registry)                  │
│  LanguagePolicy      (evaluation config)                │
│  LanguageProfile     (session config)                   │
│  LanguageCapabilityFeature (ProfileFeature)             │
│  CodingCapability    (V1.1 carry-over)                  │
│                                                         │
│  ProgrammingLanguage knows nothing about:               │
│  sandbox, runtime, Docker, interpreter, compiler,       │
│  execution engine, JVM, Node.js, AST sandbox            │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  APPLICATION LAYER                                      │
│                                                         │
│  LanguageConfig      (interview language configuration) │
│  InterviewSetup      (session initialisation)           │
│  QuestionSelection   (language-aware question routing)  │
│  ExecutionRouting    (LanguageExecutor dispatch)         │
│  ReportConfiguration (language context for report)      │
│                                                         │
│  Application layer decides which language(s) are active │
│  and routes requests to the correct infrastructure.     │
│  It does NOT execute code or evaluate domain semantics. │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER                                   │
│                                                         │
│  LanguageExecutor    (abstract execution interface)     │
│  Sandbox             (concrete execution environment)   │
│  Runtime             (Python interpreter, Node.js, JVM) │
│  Interpreter/Compiler (language-specific)               │
│  ExecutionAdapter    (per-language result normaliser)   │
│  Judge               (test pass/fail evaluator)         │
│  Docker              (container isolation)              │
│  ExecutionResult     (normalised output)                │
│                                                         │
│  Infrastructure layer runs code and returns results.    │
│  It knows nothing about ProfileFeatures,                │
│  CandidateProfile, Reasoner, Narrative, Coaching.       │
└─────────────────────────────────────────────────────────┘
```

### Frozen Responsibility Assignments

| Concept | Layer | Responsibility |
|---|---|---|
| `ProgrammingLanguage` | Domain | Abstract concept; root of language hierarchy |
| `LanguageRegistry` | Domain | Authoritative registry of supported languages |
| `LanguagePolicy` | Domain | Language-specific evaluation rules (idioms, type errors, imports) |
| `LanguageProfile` | Domain | Immutable session language configuration |
| `LanguageCapabilityFeature` | Domain | Language-specific idiomatic competence ProfileFeature |
| `CodingCapability` | Domain | V1.1 language-dimensional ability summary |
| `LanguageConfig` | Application | Interview language configuration; enabled languages; mode |
| `InterviewSetup` | Application | Session initialisation; resolves LanguageConfig → LanguageProfile |
| `QuestionSelection` | Application | Language-aware question routing from repository |
| `ExecutionRouting` | Application | Dispatches code execution to correct LanguageExecutor |
| `ReportConfiguration` | Application | Language context for report assembly |
| `LanguageExecutor` | Infrastructure | Abstract execution interface |
| `Sandbox` | Infrastructure | Concrete execution environment (AST guard, Docker, JVM) |
| `Runtime` | Infrastructure | Language interpreter/compiler |
| `Judge` | Infrastructure | Test pass/fail evaluator |
| `ExecutionResult` | Infrastructure | Normalised execution output |

---

## SECTION B — Domain Language Model

### ProgrammingLanguage

**Definition:** First-class, abstract domain concept. The notion of a supported programming language as understood by the platform's domain model. Not a string. Not an enum of fixed values (K2 Amendment A-5).

**Identity:** `language_id` (stable string key, e.g. `"python"`, `"java"`) + `display_name` + `language_version`.

**What ProgrammingLanguage NEVER knows:**
- Sandbox technology (Docker, AST guard, JVM)
- Runtime environment (Python interpreter, Node.js, JVM, LLVM)
- Interpreter or compiler implementation
- Execution engine details
- Container orchestration

**Invariant (I-20):** All domain logic that acts on language must operate on the abstract `ProgrammingLanguage` concept resolved from `LanguageRegistry`. Direct string comparisons against language names are forbidden in domain code.

### LanguageCapabilityFeature

Defined fully in ADR-018 Section D. Summary here:

- A ProfileFeature representing the candidate's language-specific idiomatic competence.
- **Type is universal.** A Python instance and a Java instance are the same type.
- **Carries `language_context` in provenance only.** The feature value and type do not depend on language.
- The one permitted exception to full language-independence at the ProfileFeature layer.

### LanguagePolicy

Language-specific evaluation configuration artifact. Governs idiom recognition, type error classification, import allowlist/blocklist. **Never modifies EvaluationDimension weights** (Domain Invariant I-13). Static per `policy_version`. Owned by the Domain layer.

### CodingCapability

V1.1 carry-over. Language-dimensional ability summary in `CandidateProfile`. In V1.2, feeds into `LanguageCapabilityFeature` via Observations (`LANGUAGE_IDIOMATIC_USAGE`, `LANGUAGE_TYPE_ERROR_PATTERN`, `LANGUAGE_CONSTRUCT_CONFUSION`). Coexists with `LanguageCapabilityFeature` during V1.2.

### QuestionLanguage

The programming language in which a coding question's starter code, constraints, and examples are authored. Owned by the question repository. Maps 1:1 to the session's active `ProgrammingLanguage`.

### ExecutionLanguage

The language runtime used to execute candidate code during a session. Resolved by `ExecutionRouting` from `LanguageProfile.active_language`. Maps 1:1 to `QuestionLanguage` within a single-language session.

### EvaluationLanguage

The language lens applied during scoring. `LanguagePolicy` informs `EvaluationEngine` of language-specific idioms without altering rubric structure. EvaluationLanguage is not a stored object — it is the runtime application of `LanguagePolicy` within `EvaluationEngine`.

### Domain Layer Invariants

**I-05:** Language never changes the semantics of `EvidenceSignal`. A `REASONING_SHALLOW` signal means the same thing in Python and Java.

**I-06:** `EvaluationDimension` weights are language-independent. Correctness, Communication, Reasoning, and Problem Decomposition are weighted identically regardless of programming language.

**I-13:** `LanguagePolicy` never modifies `EvaluationDimension` weights.

**I-19:** No `ProfileFeature` type name may reference a programming language.

**I-20:** All domain logic operates on abstract `ProgrammingLanguage`. No string comparisons against language names in domain code.

**I-21:** `LanguagePolicy` is read-only at runtime. Changes require a new `policy_version`.

**I-22 (new):** `ProgrammingLanguage` has no knowledge of any execution technology. The Domain layer is fully isolated from sandbox, runtime, container, and compiler concerns.

---

## SECTION C — Application Layer

### Responsibility

The Application layer owns the language configuration lifecycle for a session. It:
- Reads user/CLI configuration to determine which language(s) are enabled.
- Resolves `LanguageConfig` → `LanguageProfile` at session start.
- Routes question selection to the appropriate language bucket.
- Dispatches code execution to the correct `LanguageExecutor` (Infrastructure).
- Provides language context to `ReportBuilder` for report assembly.

The Application layer **does not** execute code. It **does not** evaluate domain semantics. It is the coordination layer between Domain intent and Infrastructure execution.

### LanguageConfig

`LanguageConfig` is the interview-level language configuration. It is the input to `InterviewSetup`. It answers: "what language options are configured for this interview?"

**Conceptual fields:**

| Field | Description |
|---|---|
| `enabled_languages` | List of `ProgrammingLanguage` references that are active for this interview. V1.2: one or two entries (Python and/or JavaScript/TypeScript). |
| `primary_language` | The default language when selection is unambiguous. For single-language sessions, always the only enabled language. For mixed-mode, the language used when a question has no language preference. |
| `mixed_mode` | Boolean. `true` when `len(enabled_languages) > 1`. Activates the mixed-mode selection strategy. |
| `selection_strategy` | The algorithm for selecting which language to use for each coding question. V1.2: `DETERMINISTIC_ALTERNATING` (50/50 balance). Reserved: `WEIGHTED_RANDOM`, `CANDIDATE_PREFERENCE`, `ADAPTIVE` (V1.3+). |
| `execution_policy` | Reference to the execution parameters (timeout, memory limit, retry policy) for this interview. Language-specific execution limits may be embedded here (Python sandbox may have different timeout from Node.js). |
| `evaluation_policy` | Reference to the `LanguagePolicy` version(s) active for this interview. Per enabled language. |
| `future extensibility` | `metadata: dict` — reserved for V1.3+ fields (tenant overrides, custom language configurations, experiment flags). Never parsed by V1.2 logic. |

### InterviewSetup

Consumes `LanguageConfig`. Produces `LanguageProfile` (immutable session config). Registers the session with the active `LanguageExecutor`(s). No domain knowledge — pure coordination.

### QuestionSelection

Reads `LanguageProfile.active_language` (or the mixed-mode selection sequence) to select questions from the repository. Language-aware but never language-branching in domain logic — it calls `QuestionRepository.for_language(language_id)`.

### ExecutionRouting

Reads `LanguageProfile.executor_ref`. Dispatches the candidate's code to `LanguageExecutor.execute(code, language_id, test_suite)`. Returns `ExecutionResult`. No domain knowledge.

### ReportConfiguration

Reads `LanguageProfile` to assemble language context fields in the report. Provides `language_context` to `ReportBuilder` — does not alter report structure or coaching prose.

---

## SECTION D — Infrastructure Layer

### Responsibility

The Infrastructure layer runs code and reports results. It has one responsibility: accept candidate code + test suite, execute it in an isolated environment, return a normalised `ExecutionResult`.

**What the Infrastructure layer NEVER knows:**

| Concept | Why infrastructure is blind to it |
|---|---|
| `ProfileFeature` | Feature derivation is a FeatureEngine concern — Domain |
| `CandidateProfile` | Profile state is a Domain concept |
| `Reasoner` | Reasoning logic is a Domain/Application concern |
| `Narrative` | Narrative generation is a NarrativeGenerator concern |
| `Coaching` | CoachingPlan is a CoachingEngine concern |
| `Observation` | Observation extraction is a Domain concern |
| `EvidenceSignal` | Signal production is an EvaluationEngine concern |

**Frozen invariant:** Infrastructure receives code and returns results. It does not reason, profile, narrate, or coach.

### LanguageExecutor

Abstract execution interface — parameterised by `language_id`. One concrete `LanguageExecutor` per registered `ProgrammingLanguage`. Defined in ADR-027.

**Contract (conceptual):**
```
Input:  candidate_code (str), language_id, test_suite, execution_policy
Output: ExecutionResult (stdout, stderr, test_results[], runtime_errors[], duration_ms)
```

### Sandbox

The concrete execution environment for a language. Examples:
- Python: AST-guarded subprocess sandbox (no filesystem, no network, no subprocess spawning)
- JavaScript/TypeScript: Node.js isolated runtime (no filesystem, no network)
- Java (V1.3+): JVM sandbox (SecurityManager policy)
- Go (V1.3+): OS-level isolation (seccomp / Docker container)

The sandbox is a language-specific Infrastructure artifact. It has no domain knowledge.

### Runtime

The language interpreter or compiler used within the sandbox. Examples: CPython 3.12, Node.js 22, JVM 21. Runtime details are Infrastructure configuration, not domain configuration.

### Judge

The test pass/fail evaluator. Runs the hidden test suite against the candidate's execution output. Returns structured test results. Language-agnostic at the interface level (test results are universal pass/fail/error). Language-specific in implementation (Python test runner, Jest, JUnit).

### Docker

Container isolation layer used by language sandboxes that require OS-level isolation. Domain and Application layers have no knowledge of Docker. It is purely an Infrastructure implementation detail.

### ExecutionResult

Normalised output from `LanguageExecutor`. Structure is language-independent:

| Field | Description |
|---|---|
| `execution_id` | Unique identifier for this execution |
| `language_id` | The language that was executed |
| `stdout` | Captured standard output |
| `stderr` | Captured standard error |
| `test_results` | List of `(test_id, passed: bool, error_message: str?)` |
| `runtime_errors` | Structured error list (type, message, line) |
| `duration_ms` | Wall-clock execution duration |
| `exit_code` | Process exit code |
| `timed_out` | Boolean; true if execution exceeded `execution_policy.timeout_ms` |

`ExecutionResult` is the Infrastructure-to-Application boundary object. It is consumed by `EvaluationEngine` (Application/Domain boundary) which transforms it into `EvidenceSignal` objects.

---

## SECTION E — LanguageConfig

### Conceptual Definition

`LanguageConfig` is the Application-layer configuration object that defines the language options for an interview session. It is set before session start and used by `InterviewSetup` to produce the immutable `LanguageProfile`.

### Field Definitions

#### `enabled_languages`

List of `ProgrammingLanguage` references active for this interview.

**V1.2 supported values:**
- `[python]` — Python-only session
- `[javascript]` — JavaScript-only session
- `[typescript]` — TypeScript-only session
- `[python, javascript]` — Mixed Python + JavaScript session
- `[python, typescript]` — Mixed Python + TypeScript session

No other combinations are supported in V1.2.

#### `primary_language`

The default language for unambiguous question assignment. In single-language sessions, always the only enabled language. In mixed-mode sessions, the language used for the first question and as tiebreaker in coverage balancing.

#### `mixed_mode`

Boolean derived from `len(enabled_languages) > 1`. When `true`, activates the `selection_strategy` algorithm. Not set independently — it is a computed property of `enabled_languages`.

#### `selection_strategy`

The algorithm for deciding which language a coding question will use.

| Strategy | Description | Status |
|---|---|---|
| `DETERMINISTIC_ALTERNATING` | Strict 50/50 alternation; deterministic for a given session config | V1.2 active |
| `WEIGHTED_RANDOM` | Probabilistic selection with configurable weights | Reserved V1.3+ |
| `CANDIDATE_PREFERENCE` | Candidate selects language per question | Reserved V1.3+ |
| `ADAPTIVE` | Selection adapts based on performance signals | Reserved V1.3+ |

#### `execution_policy`

Execution parameters per language: timeout (ms), memory limit (MB), retry count on transient failure, sandbox type. Language-specific execution limits are embedded here (Python sandbox and Node.js may have different timeouts).

#### `evaluation_policy`

Reference to the `LanguagePolicy` version(s) active for this interview. One entry per enabled language. Frozen at session start — changes to `LanguagePolicy` do not affect running or completed sessions.

#### Future Extensibility

`LanguageConfig` carries a `metadata: dict` field reserved for V1.3+ extensions: tenant-level language overrides, experiment flags, custom evaluation policy references. V1.2 logic ignores this field entirely.

---

## SECTION F — Mixed Language Interviews

### V1.2 Behaviour Freeze

#### Single-Language Session

One language is enabled. All coding questions are authored and executed in that language. `selection_strategy` is irrelevant. `LanguageProfile.session_mode = single`.

Supported configurations:
- Python only
- JavaScript only
- TypeScript only

#### Mixed-Mode Session

Two languages are enabled (Python + JavaScript/TypeScript). Questions alternate between the two languages. `LanguageProfile.session_mode = mixed`.

### Selection Policy: DETERMINISTIC_ALTERNATING

**Freeze:**

- Questions are assigned to languages in strict alternating order.
- First question: `primary_language`.
- Second question: the other enabled language.
- Third question: `primary_language`. And so on.
- For sessions with an odd number of coding questions, `primary_language` receives one more question than the secondary language.

**Example (6 coding questions, primary = Python, secondary = JavaScript):**

| Q# | Language |
|---|---|
| 1 | Python |
| 2 | JavaScript |
| 3 | Python |
| 4 | JavaScript |
| 5 | Python |
| 6 | JavaScript |

### Question Ordering Invariants

1. **Language assignment is determined at session start** — before any question is asked. The full sequence is computed from `LanguageConfig` and frozen as part of `LanguageProfile`.
2. **Language assignment is not reactive** — the sequence does not change based on candidate performance or question outcomes.
3. **Coverage balancing is session-level, not question-level** — the selection algorithm ensures equal language representation across the session, not per-topic coverage.
4. **Determinism** — given the same `LanguageConfig` and session seed, the same language sequence is always produced. This is required for replay fidelity.

### Language Balancing

In mixed-mode sessions, the selection algorithm ensures:
- Neither language exceeds the other by more than one question.
- The `primary_language` receives the extra question in odd-count sessions.
- Topic coverage is balanced independently by `QuestionSelection` (selecting diverse topics within each language bucket).

### Coverage Balancing

`QuestionSelection` is responsible for topic diversity within each language. The language selection algorithm is orthogonal to topic coverage. A mixed-mode session must not produce two questions on the same topic in the same language unless the question repository is exhausted.

---

## SECTION G — Coding Scope

### V1.2 Supported Scope

The following coding problem categories are in scope for V1.2 coding questions. All supported question types are solvable in a single file, with pure functions and standard library only.

| Category | Examples |
|---|---|
| Pure functions | Transformation, filtering, mapping, reduction |
| Algorithms | Sorting, searching, traversal, dynamic programming |
| Collections | Lists, arrays, dictionaries/maps, sets |
| Strings | Parsing, manipulation, pattern matching, encoding |
| Arrays | Two-pointer, sliding window, prefix sums |
| Objects / Maps | Key-value logic, frequency counting, grouping |
| Sets | Intersection, union, membership, deduplication |
| Recursion | Tree traversal, divide-and-conquer, memoisation |
| Complexity analysis | Big-O reasoning, space/time trade-offs |
| Problem solving | Decomposition, edge case reasoning, optimisation |

### V1.2 Explicitly NOT Supported

The following categories are out of scope for V1.2 and must not appear in coding questions.

| Category | Reason |
|---|---|
| Projects / multi-file programs | Requires build system and file I/O — outside sandbox scope |
| Frameworks (React, Django, Spring, etc.) | Framework-specific; not evaluable in a pure sandbox |
| Web APIs / HTTP servers | Requires network access — forbidden in sandbox |
| GUI applications | No rendering environment available |
| Database interaction | No database runtime in sandbox |
| Concurrency / threading / async | Non-deterministic; not reliably evaluable in sandbox |
| Build systems (Make, Gradle, Cargo) | Requires full build environment |
| Package managers (pip, npm, cargo) | Requires network; solution-revealing risk |
| File system operations | Forbidden in sandbox |
| External service calls | Forbidden in sandbox |

### Scope Invariant

**I-23 (new):** All V1.2 coding questions must be solvable with: one function or class, standard library imports from the `import_allowlist`, no external I/O. Any question that cannot be evaluated within this scope is rejected at question authoring time.

### Why Scope Is Frozen Here

Scope determines what `LanguagePolicy`, `LanguageExecutor`, and `Judge` must support. Expanding scope beyond V1.2 boundaries requires:
1. A new sandbox capability (Infrastructure change).
2. A `LanguagePolicy` update to recognise new constructs (Domain change with ADR-031 review).
3. Potentially new `ObservationType` entries (ADR amendment).

No scope expansion is permitted without an ADR.

---

## SECTION H — Language Independence Validation

### Principle

> **Language affects only: execution, question repository, and evaluation adapter. No component above the evaluation boundary may branch on language identity.**

### Component-by-Component Validation

| Component | Language-independent? | Validation |
|---|---|---|
| `Reasoner` (ReasonerService) | **Yes** | Reads `ReasonerDecision`; no language awareness needed. Language-agnostic invariant confirmed. |
| `ObservationExtractor` | **Yes** | Transforms `EvidenceSignal` → `Observation`. Assigns `language_context` as nullable metadata. Semantic transformation is language-agnostic. |
| `ObservationStore` | **Yes** | Stores Observations. Lifecycle identical for all language_context values. No branching on language. |
| `FeatureEngine` | **Yes** | Reads ObservationStore. Produces ProfileFeatures. `language_context` appears only in `LanguageCapabilityFeature` provenance — handled uniformly by type dispatch, not language branching. |
| `CandidateProfile` | **Yes** | Holds `ProfileFeature[]`. No language-specific fields at profile level. |
| `NarrativeGenerator` | **Yes** | Reads `CandidateProfile.features`. `language_context` available via provenance only. Does not branch on language for structural logic. May use provenance to select language-specific idiom examples in prose — this is content variation, not structural branching. |
| `CoachingEngine` | **Yes** | Reads `KnowledgeGap[]` + `CandidateProfile.features`. No language-specific logic. |
| `ReportBuilder` | **Yes** | Assembles from Narrative + CoachingPlan + CandidateProfileSnapshot. Reads `LanguageProfile` for metadata display only — does not alter report structure. |
| `KnowledgeGapEngine` | **Yes** | Reads `EvaluationResults`. Gap identification is dimension-based, not language-based. |
| `SessionHistory` | **Yes** | Write-once archive. Stores `LanguageProfile` + `policy_version` as metadata. No language-specific schema branching. |

### The Evaluation Boundary

```
                        ┌─────────────────────┐
                        │  EVALUATION BOUNDARY │
                        └─────────────────────┘
                                   │
  Below: language-aware            │   Above: language-blind
                                   │
  LanguagePolicy ────────────► EvaluationEngine ──► EvidenceSignal ──► Observation
  LanguageExecutor ──────────►                                              │
  ExecutionResult ───────────►                                              ▼
                                                                        FeatureEngine
                                                                            │
                                                                            ▼
                                                                      CandidateProfile
                                                                            │
                                                                            ▼
                                                                    Narrative / Coaching
```

After `EvaluationEngine` produces `EvidenceSignal`, language identity is present only as nullable metadata (`language_context`). No structural logic above this line branches on language.

---

## SECTION I — FeatureIdentity

### Concept

`FeatureIdentity` represents the **semantic identity** of a `ProfileFeature` across schema versions.

A `ReasoningFeature` computed under schema v1 and a `ReasoningFeature` computed under schema v3 represent the same conceptual characteristic of the candidate — reasoning quality. They may differ in field structure, value encoding, or confidence calculation. They share the same **identity**.

### Why FeatureIdentity Is Needed

Without a formal identity concept:
- Cross-session comparison (LearningProgress) cannot match features from different schema versions.
- ReplayUpdater cannot decide whether a v1 feature and a v3 feature represent the same knowledge.
- Consumer code must inspect `schema_version` to understand what a feature means — instead of relying on the identity being stable.

### Conceptual Definition

```
FeatureIdentity
    │
    ├── feature_type_id     — stable string key (e.g. "reasoning_feature")
    │                          Never changes, even as schema evolves.
    │
    ├── semantic_category   — the conceptual dimension this feature represents
    │                          (e.g. "analytical_reasoning", "communication_clarity")
    │
    └── schema_version      — the version of the schema used at computation time
                               (e.g. "1.0", "2.0")
```

`FeatureIdentity` = `(feature_type_id, semantic_category)`. The `schema_version` qualifies the representation but does not alter the identity.

### Freeze

**Two ProfileFeatures with the same `feature_type_id` and `semantic_category` represent the same candidate characteristic, regardless of `schema_version`.**

This principle enables:
- LearningProgress to compare a v1 `ReasoningFeature` with a v3 `ReasoningFeature` — same identity, different representation.
- Replay to identify which historical features correspond to which current features.
- Feature migration: when a schema evolves, the identity carries across; the migration path is from one schema version to another under the same identity.

### No Implementation

`FeatureIdentity` is a conceptual model. No classes, contracts, or runtime objects are defined here. The implementation of `FeatureIdentity` as a field on `ProfileFeature` is the subject of ADR-020 (FeatureEngine Architecture). ADR-018 Section G (versioning) relies on this concept but predates its explicit freeze.

---

## SECTION J — Runtime Architecture Validation

### Canonical Runtime Flow

```
InterviewSetup
    │  [reads LanguageConfig; resolves LanguageRegistry]
    ▼
LanguageConfig  ──→  LanguageProfile (immutable; session config frozen)
    │
    ▼
QuestionSelection
    │  [reads LanguageProfile.active_language / mixed-mode sequence]
    │  [selects question from QuestionRepository.for_language(language_id)]
    ▼
Question (with QuestionLanguage = active ProgrammingLanguage)
    │  [candidate submits answer / code]
    ▼
ExecutionRouting
    │  [resolves LanguageProfile.executor_ref]
    ▼
LanguageExecutor  ──→  Sandbox / Runtime / Judge
    │  [execution in isolated environment]
    ▼
ExecutionResult (stdout, stderr, test_results[], runtime_errors[])
    │
    ▼  [single writer: EvaluationEngine]
EvaluationEngine
    │  [applies LanguagePolicy for idiom recognition; does NOT alter dimension weights]
    │  [transforms ExecutionResult + answer text → EvidenceSignal]
    ▼
EvidenceSignal  ──→  EvidenceStore (append-only; V1.1 frozen contract)
    │  ← EVALUATION BOUNDARY: language-awareness ends here →
    ▼  [single writer: ObservationExtractor]
Observation (language_context = nullable ProgrammingLanguage)
    │  [language is metadata; semantics are language-agnostic from here forward]
    ▼
ObservationStore (append-only; Independent Aggregate Root; ADR-016/017)
    │
    ▼  [single writer: FeatureEngine]
ProfileFeature[]  ──→  CandidateProfile.features
    │  [no language branching; LanguageCapabilityFeature handled by type dispatch]
    ├──────────────────────────────────────────────────────────────────┐
    ▼  [single writer: NarrativeGenerator]                            │
Narrative                                                  KnowledgeGapEngine
(reads CandidateProfile.features)                          (reads EvaluationResults)
    │                                                                  │
    │                                               [single writer: CoachingEngine]
    │                                               CoachingPlan
    │                                                                  │
    └──────────────────────────┬───────────────────────────────────────┘
                               ▼  [single writer: ReportBuilder]
                          Report
                               ▼
                          CandidateProfileSnapshot
                               ▼  [single writer: session completion pipeline]
                          SessionHistory
                          (stores LanguageProfile + policy_version + CandidateProfileSnapshot)
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         Replay UI      ProgressTracker   CalibrationProfile
        (read-only)     (LearningProgress  (read-only aggregate)
                         derived; never
                         persisted)
```

### Validation: Single Writer Per Aggregate

| Aggregate | Single Writer |
|---|---|
| `EvidenceStore` | `EvaluationEngine` only ✓ |
| `ObservationStore` | `ObservationExtractor` only ✓ |
| `CandidateProfile.features` | `FeatureEngine` only ✓ |
| `Narrative` | `NarrativeGenerator` only ✓ |
| `CoachingPlan` | `CoachingEngine` only ✓ |
| `SessionHistory` | Session completion pipeline only ✓ |

### Validation: No Language-Specific Branches After Evaluation

| Component | Language branch present? |
|---|---|
| `ObservationExtractor` | No — assigns `language_context` as nullable metadata; no branching |
| `ObservationStore` | No — lifecycle identical regardless of `language_context` |
| `FeatureEngine` | No — `LanguageCapabilityFeature` handled by type dispatch, not language `if` |
| `CandidateProfile` | No |
| `NarrativeGenerator` | No structural branching; may vary prose content via provenance |
| `CoachingEngine` | No |
| `ReportBuilder` | No structural branching; reads `LanguageProfile` for metadata only |

All validation checks pass. ✓

---

## SECTION K — Future Extensibility

### Supported Future Languages

The platform is designed to support Go, Java, Rust, C#, Kotlin, C++, Swift (and any other language) without domain redesign.

### Required Changes Per New Language

Adding any new language requires exactly the following and nothing else:

| Change | Owner | Layer | Domain impact |
|---|---|---|---|
| `LanguageRegistry` entry | Language Independence Layer | Domain | Declaration only |
| `LanguagePolicy` artifact | Domain team | Domain | Static config; no logic change |
| `LanguageExecutor` adapter | Infrastructure team | Infrastructure | Zero domain change |
| Question stubs + hidden tests | Content team | Content | Zero domain change |
| `LanguageProfile` configuration update | App config | Application | Session config only |

### Explicitly Not Required

| Component | Change required? |
|---|---|
| `Reasoner` / `ReasonerService` | **No** |
| `ObservationExtractor` | **No** |
| `ObservationType` registry | **No** |
| `ObservationStore` | **No** |
| `FeatureEngine` | **No** |
| `ProfileFeature` taxonomy | **No** |
| `CandidateProfile` | **No** |
| `NarrativeGenerator` | **No** |
| `CoachingEngine` | **No** |
| `KnowledgeGapEngine` | **No** |
| `ReportBuilder` | **No** |
| `SessionHistory` schema | **No** |
| `EvidenceSignal` schema | **No** |
| `EvaluationDimension` weights | **No** |
| Any ADR-016/017/018 decisions | **No** |
| Knowledge Model | **No** |

**This is the structural guarantee of the Language Independence Layer.**

### Future Language Matrix

| Language | Status | Required on activation |
|---|---|---|
| Go | planned | LanguageRegistry + LanguagePolicy + LanguageExecutor + Questions |
| Java | planned | LanguageRegistry + LanguagePolicy + LanguageExecutor (JVM sandbox) + Questions |
| Rust | planned | LanguageRegistry + LanguagePolicy + LanguageExecutor (Cargo + seccomp) + Questions |
| C# | planned | LanguageRegistry + LanguagePolicy + LanguageExecutor (.NET runtime) + Questions |
| Kotlin | planned | LanguageRegistry + LanguagePolicy + LanguageExecutor (JVM) + Questions |
| C++ | planned | LanguageRegistry + LanguagePolicy + LanguageExecutor (compiler + sandbox) + Questions |
| Swift | planned | LanguageRegistry + LanguagePolicy + LanguageExecutor + Questions |

---

## SECTION L — Roadmap Alignment: ADR-020 Unblock

### Why ADR-019 Fully Unblocks ADR-020

ADR-020 (FeatureEngine Architecture — Orchestrator + Updater Composition) requires:

1. **A stable `ProgrammingLanguage` abstraction** — so that `FeatureEngine` can reference `language_context` from Observations without knowing about concrete languages. ✓ Frozen in ADR-019 Section B.

2. **A `LanguageCapabilityFeature` identity and provenance contract** — so that `ObservationUpdater` knows how to produce `LanguageCapabilityFeature` instances from `LANGUAGE_*` observation types without language branching. ✓ Frozen in ADR-018 Section D + ADR-019 Section B.

3. **A `FeatureIdentity` concept** — so that `FeatureEngine` can resolve semantic identity across schema versions when the Updater composition is designed. ✓ Frozen in ADR-019 Section I.

4. **Confirmation that FeatureEngine requires no language-specific internal logic** — so that the Updater composition can be designed as fully language-agnostic orchestration. ✓ Validated in ADR-019 Section H.

### Why FeatureEngine Remains Completely Language-Independent

`FeatureEngine` orchestrates `Updaters`. Each `Updater` reads from `ObservationStore` and produces `ProfileFeature[]`. The `ObservationUpdater` produces `LanguageCapabilityFeature` when it encounters `LANGUAGE_*` observation types.

This is **type dispatch** — not language dispatch. `ObservationUpdater` matches `ObservationType.LANGUAGE_*` to `LanguageCapabilityFeature`. It does not check `if language == "python"`. It checks `if observation_type in LANGUAGE_OBSERVATION_TYPES`. The `language_context` value from the source Observation is forwarded to the feature's provenance record.

At no point does `FeatureEngine` branch on a concrete language name. It is as language-independent as `NarrativeGenerator` or `CoachingEngine`.

### ADR-020 Dependency Confirmation

| ADR-020 Precondition | Source | Status |
|---|---|---|
| Observation schema frozen | ADR-016 | ✓ |
| ObservationStore lifecycle frozen | ADR-017 | ✓ |
| ProfileFeature taxonomy frozen | ADR-018 | ✓ |
| Feature versioning strategy frozen | ADR-018 Section G | ✓ |
| FeatureIdentity concept frozen | ADR-019 Section I | ✓ |
| Language independence of FeatureEngine confirmed | ADR-019 Section H | ✓ |
| ProgrammingLanguage abstraction frozen | ADR-019 Section B | ✓ |

**ADR-020 is fully unblocked. All preconditions are met.**

---

## SECTION M — ADR Backlog Update

### ADR-019 Status

**Accepted.** This document. Language Independence Layer, LanguageConfig Architecture, and all related invariants frozen. Supersedes the v0 sketch.

### Updated Backlog

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-019 | Language Independence Layer & LanguageConfig Architecture | v0 Accepted | **ACCEPTED (v1 — this document)** |
| ADR-020 | FeatureEngine Architecture | UNBLOCKED (ADR-018) | **FULLY UNBLOCKED** — all preconditions confirmed |
| ADR-027 | LanguageExecutor Abstraction | Pending | **UNBLOCKED** |
| ADR-028 | Language Selection Policy | Pending | **UNBLOCKED** |
| ADR-031 | LanguagePolicy Governance | P3 | Unchanged — P3, non-blocking |

### Critical Path After ADR-019

```
ADR-019 ACCEPTED (this document)
    │
    ├──→ ADR-020 (FeatureEngine Architecture) — PRIMARY NEXT MILESTONE
    │         All preconditions met.
    │
    ├──→ ADR-027 (LanguageExecutor Abstraction) — parallel, infrastructure track
    │
    └──→ ADR-028 (Language Selection Policy) — parallel, session config track
```

---

## SECTION N — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ Domain/Application/Infrastructure separation frozen | **FROZEN** — Section A: three-layer diagram, responsibility table, layer invariants |
| ✓ `ProgrammingLanguage` frozen as Domain concept | **FROZEN** — Section B: abstract, typed, registered; knows nothing about sandbox/runtime/Docker |
| ✓ `LanguageExecutor` frozen as Infrastructure concept | **FROZEN** — Section D: runs code, returns results, no domain knowledge |
| ✓ `LanguageConfig` frozen | **FROZEN** — Section E: all 6 fields defined; V1.2 options frozen |
| ✓ Mixed-language interviews frozen | **FROZEN** — Section F: DETERMINISTIC_ALTERNATING policy; ordering invariants; coverage balancing |
| ✓ Coding scope frozen | **FROZEN** — Section G: 10 supported categories; 10 explicitly not-supported categories; scope invariant I-23 |
| ✓ Language independence validated per component | **VALIDATED** — Section H: Reasoner, Observation, FeatureEngine, CandidateProfile, Narrative, Coaching, Report, KnowledgeGap all confirmed language-independent |
| ✓ Evaluation boundary defined | **FROZEN** — Section H: language-awareness ends at EvidenceSignal production |
| ✓ `FeatureIdentity` concept introduced | **FROZEN** — Section I: `(feature_type_id, semantic_category)` stable across schema versions |
| ✓ Runtime validated | **VALIDATED** — Section J: single-writer verification, no post-evaluation language branches |
| ✓ Future extensibility confirmed | **CONFIRMED** — Section K: 7 future languages; 5 required changes; full not-required list |
| ✓ ADR-020 fully unblocked | **CONFIRMED** — Section L: all 7 preconditions met; FeatureEngine language-independence proven |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section M: no frozen V1.1 asset requires change |

---

## Final Recommendation

**ADR-019 is ACCEPTED.**

The Language Independence Layer is frozen. Domain, Application, and Infrastructure responsibilities are separated. `ProgrammingLanguage` is an abstract domain concept. `LanguageConfig` is fully defined. Mixed-language interview policy is frozen. Coding scope is frozen. `FeatureIdentity` is introduced. All components above the evaluation boundary are confirmed language-independent.

**Immediate next action: ADR-020 (FeatureEngine Architecture — Orchestrator + Updater Composition).** All preconditions are met. ADR-020 is the sole remaining P0 blocker for EPIC-01 implementation.

---

## Rationale

The three-layer separation (Domain / Application / Infrastructure) is the minimal architecture that enforces the language independence guarantee structurally — not by convention. The evaluation boundary is the precise point where language-specific knowledge is consumed and converted into language-agnostic signals. Everything above it is language-blind by construction.

`FeatureIdentity` is introduced here because ADR-020 needs a stable semantic identity concept to design the Updater composition — particularly for how `LanguageCapabilityFeature` instances are handled across schema versions in cross-session scenarios.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Language branching inside FeatureEngine | Produces language-specific ProfileFeature derivation paths; violates I-19; blocks future language addition without engine changes |
| Merging Application and Infrastructure layers | Conflates session configuration (what language?) with execution mechanics (how to run code?); breaks independently evolvable boundaries |
| LanguagePolicy inside LanguageExecutor | Conflates evaluation rules (domain) with execution (infrastructure); makes policy change control impossible without infrastructure deployment |
| No formal mixed-mode policy | Mixed sessions require deterministic replay; without a frozen selection algorithm, replay cannot reconstruct the original question language sequence |

## Consequences

### Positive

- Language independence is a structural guarantee, enforced by layer separation
- Adding Go, Java, Rust, C#, Kotlin, C++, Swift requires only 4 artifacts per language
- FeatureEngine, NarrativeGenerator, CoachingEngine, and all knowledge model components require zero changes for any new language
- `FeatureIdentity` enables correct cross-session comparison for LearningProgress
- ADR-020 is now fully unblocked

### Negative / Risks

- Mixed-mode session language balancing (Section F) must be validated against question repository size — if the repository has insufficient questions in one language, the 50/50 balance may degrade session quality
- `FeatureIdentity` is introduced conceptually here but not yet implemented — ADR-020 must translate it into the FeatureEngine design before implementation begins
- `LanguageCapabilityFeature` provenance exception requires explicit consumer handling; this must be explicitly tested in NarrativeGenerator and ReportBuilder implementations

## Implementation Evidence

Architecture only. No production files modified.
Relevant existing assets (unchanged):
- `domain/contracts/reasoning/evidence_signal.py` (frozen; language-agnostic confirmed)
- `domain/profile/candidate_profile.py` (unchanged)
- All V1.1 evaluation pipeline files (unchanged)

## Review Trigger

- When a new language is proposed for registration
- When mixed-mode session support is extended beyond 50/50 (ADR-028 amendment required)
- When coding scope is proposed for expansion (new ADR required)
- When `FeatureIdentity` implementation in ADR-020 requires amendment to the conceptual model
