# ADR-031 — LanguagePolicy Governance

**Status:** Accepted — V1.2 Architecture (Language Layer Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Language Independence Layer
**Preconditions:** ADR-019 (Language Independence Layer), ADR-024 (Calibration Framework)
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-019, ADR-024, ADR-027, ADR-028

---

## Context

ADR-019 introduced `LanguagePolicy` as a Domain concept governing language-specific evaluation configuration: idiom recognition, type error classification, import allowlist/blocklist. It established that `LanguagePolicy` is read-only at runtime, changes require a new `policy_version`, and it never modifies `EvaluationDimension` weights.

What remained undefined was the complete governance model: what a `LanguagePolicy` contains, how versions are managed, how sessions are bound to a policy version, how policy changes interact with the calibration baseline, and the full governance process for adding a new language.

This ADR freezes `LanguagePolicy` governance completely.

---

## Decision

**`LanguagePolicy` defines interpretation. Never execution. Never scoring weights.**

---

## SECTION A — Purpose: What LanguagePolicy Is

`LanguagePolicy` is a Domain-layer configuration artifact. Its purpose is to provide language-specific interpretation rules to `EvaluationEngine` so that evaluation can recognise idiomatic correctness in a language-aware way — without altering the structure of evaluation, the weights of dimensions, or any knowledge model component.

### What LanguagePolicy Defines

Language-specific *interpretation* of candidate behaviour:

- What counts as idiomatic usage in this language
- What constitutes a type error in this language
- What imports are allowed or forbidden
- What patterns are language-canonical versus anti-idiomatic

### What LanguagePolicy Never Defines

| Concern | Owner | Why LanguagePolicy is excluded |
|---|---|---|
| `EvaluationDimension` weights | EvaluationEngine configuration | Dimension weights are language-independent by invariant I-06 |
| Sandbox type | `ExecutionPolicy` / `LanguageExecutor` | Execution is Infrastructure; policy is Domain |
| Memory / timeout limits | `ExecutionPolicy` | Execution resource management is Infrastructure |
| `ObservationType` definitions | Domain ObservationType registry | Observation taxonomy is language-independent |
| `ProfileFeature` types | ProfileFeature taxonomy (ADR-018) | Feature taxonomy is language-independent |
| `CandidateProfile` structure | CandidateProfile aggregate | Profile structure is language-independent |
| Narrative or coaching templates | NarrativeGenerator, CoachingEngine | Narrative and coaching are language-independent |

**Invariant (I-31-1):** `LanguagePolicy` only affects interpretation. It never changes scoring weights, evaluation dimensions, feature types, or knowledge model components.

---

## SECTION B — Policy Contents

Each `LanguagePolicy` artifact contains exactly the following structure. This structure is frozen for V1.2.

| Field | Description |
|---|---|
| `policy_id` | Stable identifier (e.g. `"python_policy"`) — never changes |
| `policy_version` | Semantic version (e.g. `"1.0.0"`) — incremented on every change |
| `language_id` | The `ProgrammingLanguage` this policy governs |
| `allowed_imports` | Allowlist of standard library imports permitted in V1.2 coding scope |
| `forbidden_imports` | Blocklist of imports that are rejected at evaluation time (network, filesystem, subprocess, etc.) |
| `idiomatic_patterns` | List of patterns considered idiomatic in this language (e.g. list comprehensions in Python, destructuring in JavaScript) |
| `type_error_taxonomy` | Classification of language-specific type errors (e.g. `AttributeError` in Python, `TypeError` in JavaScript) |
| `warning_taxonomy` | Classification of language-specific warnings that are semantically significant (e.g. implicit type coercion in JavaScript) |
| `metadata` | Reserved field for V1.3+ governance extensions; never parsed by V1.2 logic |

### Reserved Future Rules

The following fields are structurally reserved in `metadata` for future policy extensions. No V1.2 logic reads them:

- Async/await pattern taxonomy (reserved for concurrency scope expansion)
- Framework idiom rules (reserved when framework support is added)
- Compiler warning integration (reserved for compiled languages: Java, Go, Rust)

**Invariant (I-31-2):** `LanguagePolicy` structure is additive-only. Fields may be added; existing fields may not be renamed or removed without a `policy_version` increment and a governance review.

---

## SECTION C — Policy Versioning

### Versioning Rules

| Rule | Statement |
|---|---|
| Every change to a `LanguagePolicy` requires a `policy_version` increment | Even documentation changes that could affect interpretation |
| Sessions are bound to policy versions at session start | `LanguageConfig.evaluation_policy` stores the `policy_version` per language |
| Running sessions are never affected by policy changes | A policy update after session start has no effect on the active session |
| Completed sessions store the policy version used | `SessionHistory` stores `policy_version` as part of `LanguageProfile` |
| Replay always uses the stored policy version | Never the current policy |

### Frozen Invariant

**I-31-3:** Every session stores the `LanguagePolicy` version(s) active at session start as part of `LanguageProfile` in `SessionHistory`. Replay reconstruction always reads the stored `policy_version` and applies that version's policy — never the current deployed policy.

**I-31-4:** `LanguagePolicy` is read-only at runtime. No session, evaluation, or executor may mutate a policy object during session execution.

### Why Replay Must Use Stored Policy

If replay used the current policy instead of the stored policy:
- A policy change that reclassifies an import as forbidden would retroactively fail evaluations that were correct under the original policy
- Replay would produce different `ExecutionResult` interpretations than the original session — violating replay fidelity
- Calibration baselines would be invalidated silently

Storing and replaying with the original `policy_version` is the only design that guarantees replay correctness.

---

## SECTION D — Governance

### Adding a New Language

Adding a new programming language to the platform requires exactly the following and nothing else:

| Artifact | Owner | Layer | Description |
|---|---|---|---|
| `LanguageRegistry` entry | Domain team | Domain | Register the new `ProgrammingLanguage` |
| `LanguagePolicy` artifact | Domain team | Domain | Author policy: imports, idioms, type error taxonomy, warnings |
| `LanguageExecutor` adapter | Infrastructure team | Infrastructure | Implement concrete executor for the new language |
| Question repository | Content team | Content | Author coding questions and hidden tests in the new language |
| Evaluation Adapter | Infrastructure/Application | Application boundary | Normalise language-specific execution output to `ExecutionResult` |

**No other changes are required.** The following components require zero modification:

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
| Any ADR-016/017/018/019 decisions | **No** |

**Invariant (I-31-5):** Adding a language requires exactly 5 artifacts. Adding a sixth requirement is an architectural violation that must be resolved by amending the three-layer separation, not by expanding the governance checklist.

### ADR Approval Requirement

Adding a new language to the `LanguageRegistry` requires:

1. **ADR approval** — a new ADR or amendment to an existing language-governance ADR documenting: the language, the `ExecutionPolicy` parameters, the sandbox technology, and the question scope constraints
2. **`LanguageRegistry` entry** — formally registered before any session may use the language
3. **`LanguagePolicy` authored and versioned** — policy must be at `v1.0.0` minimum before the first session
4. **`LanguageExecutor` implemented and tested** — in isolation; zero domain dependencies
5. **Question repository** — minimum viable question count per topic category (as defined in ADR-019 Section G scope)
6. **Evaluation Adapter** — normalises language-specific output to `ExecutionResult`

No shortcuts. No partial activations. All 6 artifacts must be complete before a language is available in any session.

### Policy Change Governance

Any change to an existing `LanguagePolicy` (even minor) requires:

1. `policy_version` increment
2. Review of `CalibrationProfile` baseline — does the change shift expected evaluation output on calibration fixtures?
3. If calibration shift is detected: calibration baseline update before deployment
4. Deployment of updated policy — old version remains available for replay

**Invariant (I-31-6):** A `LanguagePolicy` change that causes a measurable shift in `CalibrationProfile` output must be treated as a calibration event. The calibration baseline must be updated and validated before the new policy version is deployed to production sessions.

---

## SECTION E — Engineering Invariants

The following invariants are frozen for `LanguagePolicy`. They are permanent.

| Invariant | Statement |
|---|---|
| **I-31-1** | `LanguagePolicy` only affects interpretation; never scoring weights, dimensions, feature types, or knowledge model |
| **I-31-2** | `LanguagePolicy` structure is additive-only; no field removals or renames without `policy_version` increment |
| **I-31-3** | Every session stores `policy_version`; replay uses stored version, never current |
| **I-31-4** | `LanguagePolicy` is read-only at runtime |
| **I-31-5** | Adding a language requires exactly 5 artifacts; no more |
| **I-31-6** | Policy changes causing calibration shift require baseline update before deployment |
| **I-31-7** | `LanguagePolicy` is one policy per language; no cross-language policies exist |
| **I-31-8** | `LanguagePolicy` does not define `ExecutionPolicy`; execution parameters belong to `ExecutionPolicy` in `LanguageConfig` |
| **I-31-9** | `LanguagePolicy` version history is permanent; versions are never deleted (replay depends on historical versions) |
| **I-31-10** | No session may start with a `LanguagePolicy` version that is not registered in the `LanguageRegistry` for that language |

---

## SECTION F — Calibration Interaction

`LanguagePolicy` and `CalibrationProfile` interact at one point: policy changes may shift evaluation output on calibration fixtures.

### Interaction Model

```
LanguagePolicy change (new policy_version)
    │
    ▼
EvaluationEngine (applies updated policy to existing calibration fixtures)
    │
    ▼
CalibrationProfile comparison
    │  [is output shift within tolerance?]
    ├── Yes → deploy new policy_version; update baseline
    └── No  → policy change is a breaking change; requires separate ADR
```

**Invariant (I-31-6):** This interaction is the only point where `LanguagePolicy` governance touches the broader system. It does not flow back into the Knowledge Model, FeatureEngine, or CandidateProfile.

---

## Rationale

`LanguagePolicy` governance requires formal versioning and replay binding because evaluation correctness must be reproducible across time. Without stored policy versions, a change to what counts as "idiomatic Python" would silently alter what past session evaluations meant. The governance model ensures that the meaning of every past evaluation is permanently fixed by the `policy_version` stored in `SessionHistory`.

The 5-artifact addition requirement enforces the structural guarantee from ADR-019: adding a language must be a domain-zero-impact operation. Governance that requires more than these 5 artifacts signals an architectural violation that must be resolved structurally.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Shared LanguagePolicy across languages | Language idioms are mutually exclusive; a shared policy creates impossible merge conflicts and undefined behaviour for mixed-mode sessions |
| LanguagePolicy inside LanguageExecutor | Conflates evaluation rules (domain) with execution (infrastructure); makes policy change control impossible without infrastructure deployment |
| No formal versioning | Makes replay non-deterministic; policy changes retroactively alter historical session correctness |
| Calibration-independent policy changes | Silent evaluation drift; scoring becomes meaningless without baseline stability |

## Consequences

### Positive
- Replay is permanently correct by construction — stored `policy_version` guarantees evaluation fidelity
- Calibration baseline stability is formally protected against silent policy drift
- Language addition is a bounded 5-artifact operation — no governance scope creep

### Negative / Risks
- Policy version history must be permanently retained — version pruning is forbidden; storage cost grows with platform age
- Calibration baseline review on every policy change adds process overhead — accepted cost for scoring integrity

## Implementation Evidence

Architecture only. No production files modified.
