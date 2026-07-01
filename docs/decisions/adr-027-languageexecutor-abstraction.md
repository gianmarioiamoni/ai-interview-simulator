# ADR-027 — LanguageExecutor Abstraction

**Status:** Accepted — V1.2 Architecture (Language Layer Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Infrastructure — Language Independence Layer
**Preconditions:** ADR-019 (Language Independence Layer)
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-019, ADR-028, ADR-031

---

## Context

ADR-019 froze the three-layer separation (Domain / Application / Infrastructure) and assigned `LanguageExecutor` to the Infrastructure layer with the responsibility of running candidate code and returning `ExecutionResult`. What remained undefined was the precise abstraction boundary: what exactly `LanguageExecutor` receives, what it returns, what it is forbidden to know, and how execution flows from InterviewSetup through sandbox to `ExecutionResult`.

This ADR freezes the `LanguageExecutor` abstraction completely.

---

## Decision

**`LanguageExecutor` is an Infrastructure service. It executes code. It never evaluates knowledge.**

---

## SECTION A — Why LanguageExecutor Is Infrastructure

`LanguageExecutor` is classified as Infrastructure for structural reasons, not by convention:

| Criterion | Classification |
|---|---|
| It accepts raw code strings | Infrastructure I/O boundary |
| It manages sandbox lifecycle | Infrastructure resource management |
| It controls execution timeout and memory | Infrastructure policy enforcement |
| It returns raw execution output | Infrastructure result normalisation |
| It has no access to candidate knowledge state | Domain is inaccessible from here |
| It has no awareness of evaluation dimensions | Domain scoring is inaccessible from here |

**It executes code. It never evaluates knowledge.**

The separation is non-negotiable. Merging execution with evaluation would couple sandbox policy to scoring policy — making it impossible to change one without the other.

### Frozen Responsibility

`LanguageExecutor` owns exactly one responsibility:

> Accept `(LanguageConfig, Question, CandidateCode, HiddenTests, ExecutionPolicy)` → return `ExecutionResult`.

Nothing else. Everything else is a domain or application concern.

### What LanguageExecutor Never Knows

| Concept | Reason |
|---|---|
| `CandidateProfile` | Profile state is owned by FeatureEngine and CandidateProfile aggregate — Domain |
| `FeatureEngine` | Feature derivation is a Domain concern |
| `EvidenceSignal` | Signal production is an EvaluationEngine concern — Application/Domain boundary |
| `Observation` | Observation extraction is a Domain concern |
| `SessionHistory` | Session persistence is a Domain/Application concern |
| `Narrative` | Narrative generation is a NarrativeGenerator concern |
| `Coaching` | CoachingPlan is a CoachingEngine concern |
| `ObservationType` | Observation taxonomy is a Domain concern |
| `ProfileFeature` | Feature taxonomy is a Domain concern |

**Invariant (I-27-1):** `LanguageExecutor` is blind to all Domain concepts. It receives code; it returns results.

---

## SECTION B — Responsibilities

### Input Contract (Conceptual)

`LanguageExecutor` receives exactly:

| Parameter | Description |
|---|---|
| `LanguageConfig` | Active language configuration for the session (resolved from `LanguageProfile`) |
| `Question` | The coding question being evaluated (stub, constraints, examples) |
| `CandidateCode` | The candidate's submitted solution as a raw string |
| `HiddenTests` | The hidden test suite to execute against the solution |
| `ExecutionPolicy` | Timeout (ms), memory limit (MB), retry policy, sandbox type |

### Output Contract (Conceptual)

`LanguageExecutor` returns exactly:

| Field | Description |
|---|---|
| `execution_id` | Unique identifier for this execution event |
| `language_id` | The language that was executed |
| `stdout` | Captured standard output |
| `stderr` | Captured standard error |
| `test_results` | List of `(test_id, passed: bool, error_message: str?)` |
| `runtime_errors` | Structured error list `(type, message, line)` |
| `duration_ms` | Wall-clock execution duration |
| `exit_code` | Process exit code |
| `timed_out` | Boolean; true if execution exceeded `ExecutionPolicy.timeout_ms` |

**Nothing else.**

`ExecutionResult` is the Infrastructure-to-Application boundary object. Its sole consumer within the Knowledge Pipeline is `EvaluationEngine`, which transforms it into `EvidenceSignal`. `LanguageExecutor` has no knowledge of this transformation.

### Boundary Invariants

**I-27-2:** `LanguageExecutor` never produces `EvidenceSignal`.

**I-27-3:** `LanguageExecutor` never produces `Observation`.

**I-27-4:** `LanguageExecutor` never writes to `CandidateProfile`.

**I-27-5:** `LanguageExecutor` never writes to `SessionHistory`.

**I-27-6:** `LanguageExecutor` never reads `LanguagePolicy` for scoring. It may read execution-relevant policy fields (import allowlist enforcement, sandbox type) from `ExecutionPolicy` only.

**I-27-7:** `LanguageExecutor` never reasons about candidate capability.

---

## SECTION C — Execution Pipeline

The canonical execution pipeline from Interview Question to `ExecutionResult`:

```
InterviewSetup
    │  [resolves LanguageConfig → LanguageProfile]
    ▼
LanguageProfile (immutable; session config frozen)
    │
    ▼  [QuestionSelection reads LanguageProfile.active_language]
Question (QuestionLanguage = active ProgrammingLanguage)
    │  [candidate submits code]
    ▼
ExecutionRouting (Application layer)
    │  [resolves LanguageProfile.executor_ref]
    │  [dispatches to correct LanguageExecutor per language_id]
    ▼
LanguageExecutor (Infrastructure)
    │  [routes to language-specific Sandbox + Runtime]
    ▼
Sandbox (AST guard / Docker / JVM / Node.js isolated runtime)
    │  [executes candidate code against hidden tests]
    ▼
Runtime (CPython 3.12 / Node.js 22 / JVM 21 / ...)
    │
    ▼
Judge (test pass/fail evaluator; language-specific runner)
    │
    ▼
ExecutionResult (normalised; language-independent structure)
    │
    ▼  [single writer: EvaluationEngine]
EvaluationAdapter → EvidenceSignal
```

### Ownership Validation

| Stage | Owner | Layer |
|---|---|---|
| `InterviewSetup` → `LanguageProfile` | Application | Application |
| `QuestionSelection` | Application | Application |
| `ExecutionRouting` | Application | Application |
| `LanguageExecutor` | Infrastructure | Infrastructure |
| `Sandbox` | Infrastructure | Infrastructure |
| `Runtime` | Infrastructure | Infrastructure |
| `Judge` | Infrastructure | Infrastructure |
| `ExecutionResult` | Infrastructure (produced); Application (consumed) | Boundary |
| `EvaluationEngine` | Application/Domain boundary | Evaluation Boundary |

---

## SECTION D — Supported Languages

### V1.2 Freeze

The following languages are supported in V1.2:

| Language | Status | Sandbox |
|---|---|---|
| Python | Active | AST-guarded subprocess |
| JavaScript | Active | Node.js isolated runtime |
| TypeScript | Active | Node.js with tsc transpilation |

### Future Languages (Reserved — No Implementation)

The following languages are planned. No architectural changes are required when they are activated. Each requires only: `LanguageRegistry` entry + `LanguagePolicy` + `LanguageExecutor` adapter + question repository.

| Language | Planned Sandbox |
|---|---|
| Java | JVM sandbox (SecurityManager policy) |
| Go | OS-level isolation (seccomp / Docker) |
| Rust | Compiler sandbox (Cargo + seccomp) |
| C# | .NET runtime sandbox |
| Kotlin | JVM sandbox (same executor variant as Java) |
| Swift | Swift compiler sandbox |

**Invariant (I-27-8):** Adding any future language requires zero changes to Domain layer, FeatureEngine, CandidateProfile, NarrativeGenerator, CoachingEngine, or SessionHistory.

---

## SECTION E — Engineering Invariants

The following invariants are frozen for `LanguageExecutor`. They are permanent. No amendment process exists for these invariants — they may only be superseded by a replacement ADR.

| Invariant | Statement |
|---|---|
| **I-27-1** | `LanguageExecutor` is blind to all Domain concepts |
| **I-27-2** | `LanguageExecutor` never produces `EvidenceSignal` |
| **I-27-3** | `LanguageExecutor` never produces `Observation` |
| **I-27-4** | `LanguageExecutor` never writes to `CandidateProfile` |
| **I-27-5** | `LanguageExecutor` never writes to `SessionHistory` |
| **I-27-6** | `LanguageExecutor` never reads `LanguagePolicy` for scoring |
| **I-27-7** | `LanguageExecutor` never reasons about candidate capability |
| **I-27-8** | Adding any future language requires zero Domain changes |
| **I-27-9** | `ExecutionResult` is language-independent in structure |
| **I-27-10** | One concrete `LanguageExecutor` per registered `ProgrammingLanguage`; dispatched by `language_id` only |

---

## SECTION F — Future Concepts (Reserved)

### ExecutionCapability

**Conceptual introduction only. No implementation.**

`ExecutionCapability` describes the runtime characteristics of each language:

- Memory limit
- Execution timeout
- Sandbox type
- Import restriction mechanism
- Filesystem isolation level
- Network isolation level

`ExecutionCapability` is an Infrastructure-only concept. It never surfaces in Domain or Application layers. It is reserved for a future ADR when sandbox configuration management requires formalisation.

---

## Rationale

Assigning `LanguageExecutor` to Infrastructure is the only design that preserves the language independence guarantee from ADR-019. If `LanguageExecutor` had access to Domain concepts, every new language would require verifying that the executor did not corrupt domain state. The structural blind wall between executor and domain eliminates this verification requirement entirely.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| LanguageExecutor in Application layer | Conflates execution mechanics with session coordination; Application layer should not manage sandbox lifecycle |
| One LanguageExecutor with internal language branching | Every new language requires modifying the executor; violates OCP; impossible to test per-language in isolation |
| LanguageExecutor producing EvidenceSignal directly | Couples sandbox policy to scoring policy; makes calibration impossible without redeploying executor |

## Consequences

### Positive
- `LanguageExecutor` can be replaced, tested, or scaled per language without any Domain or Application change
- New languages require only an adapter + sandbox; zero domain redesign
- `ExecutionResult` is a clean, language-independent boundary object

### Negative / Risks
- Each language requires a distinct concrete executor — manageable at V1.2 scale (3 languages); may require executor registry management at V1.3+ scale (8+ languages)

## Implementation Evidence

Architecture only. No production files modified.
