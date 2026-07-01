# ADR-028 — Language Selection Policy

**Status:** Accepted — V1.2 Architecture (Language Layer Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Application — Language Independence Layer
**Preconditions:** ADR-019 (Language Independence Layer), ADR-027 (LanguageExecutor Abstraction)
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-019, ADR-027, ADR-031

---

## Context

ADR-019 froze the `DETERMINISTIC_ALTERNATING` selection strategy as the sole V1.2 mixed-mode policy and introduced `LanguageConfig` with a `selection_strategy` field. What remained undefined was the complete policy specification: who owns selection, when it is decided, how the selection sequence is frozen, how the question repository interacts with language selection, and what the deterministic runtime ordering looks like end-to-end.

This ADR freezes language selection policy completely.

---

## Decision

**Language selection belongs to `InterviewSetup`. Not Runtime.**

The complete language sequence for a session is computed at session initialisation and frozen as part of `LanguageProfile`. No runtime component may alter the sequence after session start.

---

## SECTION A — Purpose: Selection Belongs to InterviewSetup

### The V1.1 Problem

In V1.1, language was an implicit parameter passed through the pipeline at question generation time. No formal selection decision existed. In a mixed-language scenario, there was no defined policy for which language to use per question — creating non-determinism that made replay impossible.

### The V1.2 Guarantee

Language selection is decided exactly once — at session initialisation — and frozen for the lifetime of the session.

**Frozen invariant (I-28-1):** Language assignment is determined at session start, before any question is asked. The complete sequence is computed from `LanguageConfig`, frozen in `LanguageProfile`, and never modified during session execution.

**Frozen invariant (I-28-2):** No runtime component — `QuestionSelection`, `ExecutionRouting`, `EvaluationEngine`, or any downstream component — may reassign a question's language after session start.

### Why Not Runtime Selection

Runtime selection would:
1. Break deterministic replay — the language sequence would not be recoverable from `SessionHistory`
2. Couple selection logic to execution state — making the session non-reproducible
3. Allow performance signals to influence language assignment — violating the language-independence principle

---

## SECTION B — Supported Modes

The following session modes are supported in V1.2. No other modes are permitted.

| Mode | `enabled_languages` | `mixed_mode` | Description |
|---|---|---|---|
| Python only | `[python]` | `false` | All coding questions in Python |
| JavaScript only | `[javascript]` | `false` | All coding questions in JavaScript |
| TypeScript only | `[typescript]` | `false` | All coding questions in TypeScript |
| Python + JavaScript | `[python, javascript]` | `true` | Mixed; `DETERMINISTIC_ALTERNATING` active |
| Python + TypeScript | `[python, typescript]` | `true` | Mixed; `DETERMINISTIC_ALTERNATING` active |

**Invariant (I-28-3):** No V1.2 session may enable more than two languages simultaneously.

**Invariant (I-28-4):** The only supported two-language combinations are Python+JavaScript and Python+TypeScript. JavaScript+TypeScript mixed sessions are not supported in V1.2.

**Invariant (I-28-5):** Single-language sessions have no active `selection_strategy`. The concept is irrelevant when one language is enabled.

---

## SECTION C — Selection Strategies

### V1.2 Active Strategy

**`DETERMINISTIC_ALTERNATING`**

Strict alternating assignment between the two enabled languages. Deterministic for a given `LanguageConfig` and session seed.

Rules:
1. First question → `primary_language`
2. Second question → secondary language
3. Third question → `primary_language`
4. Pattern continues for the full session
5. For odd-count sessions: `primary_language` receives one more question than the secondary

Example — 6 questions, primary = Python, secondary = JavaScript:

| Q# | Language |
|---|---|
| 1 | Python |
| 2 | JavaScript |
| 3 | Python |
| 4 | JavaScript |
| 5 | Python |
| 6 | JavaScript |

Example — 5 questions, primary = Python, secondary = TypeScript:

| Q# | Language |
|---|---|
| 1 | Python |
| 2 | TypeScript |
| 3 | Python |
| 4 | TypeScript |
| 5 | Python |

### Reserved Future Strategies

The following strategies are architecturally reserved. No implementation.

| Strategy | Description | Status |
|---|---|---|
| `WEIGHTED_RANDOM` | Probabilistic selection with configurable per-language weights | Reserved V1.3+ |
| `CANDIDATE_PREFERENCE` | Candidate selects language per question at runtime | Reserved V1.3+ |
| `BALANCED` | Ensures equal topic coverage per language across session | Reserved V1.3+ |
| `ADAPTIVE` | Selection adapts based on performance signals | Reserved V1.4+ |

**Invariant (I-28-6):** `ADAPTIVE` strategy is permanently reserved. It may not be implemented without a dedicated ADR addressing performance-signal feedback into language selection and its impact on replay determinism.

---

## SECTION D — Question Repository

### Responsibilities

| Responsibility | Owner |
|---|---|
| Language-aware question retrieval | `QuestionRepository` |
| Topic diversity within each language bucket | `QuestionSelection` |
| Language assignment per question | `LanguageProfile` (frozen at session start) |
| Knowledge model structure | Domain — language-independent |

**Frozen invariant (I-28-7):** The question repository is language-aware. Questions are authored per language. `QuestionRepository.for_language(language_id)` returns questions for that language only.

**Frozen invariant (I-28-8):** The knowledge model is language-independent. `ObservationType`, `ProfileFeature` taxonomy, `EvaluationDimension` weights — none of these reference a programming language. Language is authoring metadata on a question; it is not a knowledge classification.

### Coverage Balancing

In mixed-mode sessions, topic diversity within each language must be maintained independently:

- `QuestionSelection` selects diverse topics within the Python bucket and within the JavaScript/TypeScript bucket separately.
- The language selection algorithm (alternating) is orthogonal to topic coverage.
- A mixed-mode session must not produce two questions on the same topic in the same language unless the repository is exhausted for that language.

**Invariant (I-28-9):** Topic coverage balancing is `QuestionSelection`'s responsibility. Language assignment is `LanguageProfile`'s responsibility. These are orthogonal concerns.

---

## SECTION E — Runtime

The canonical runtime ordering for language selection:

```
LanguageConfig (set before session start)
    │  [InterviewSetup reads LanguageConfig]
    │  [validates enabled_languages against LanguageRegistry]
    │  [computes complete language sequence from selection_strategy]
    ▼
LanguageProfile (immutable; language sequence frozen)
    │  [stored in SessionHistory at session close for replay]
    ▼
QuestionSelection (Application layer)
    │  [reads LanguageProfile.language_sequence[question_index]]
    │  [calls QuestionRepository.for_language(language_id)]
    ▼
Question (QuestionLanguage = language_sequence[question_index])
    │
    ▼
ExecutionRouting
    │  [dispatches to LanguageExecutor for language_sequence[question_index]]
    ▼
LanguageExecutor → Sandbox → Runtime → Judge → ExecutionResult
    │
    ▼
EvaluationEngine (applies LanguagePolicy for active language)
    │
    ▼
EvidenceSignal → Observation → FeatureEngine → CandidateProfile
```

### Determinism Invariants

**I-28-10:** The language sequence is fully deterministic. Given the same `LanguageConfig`, `InterviewSetup` always produces the same `LanguageProfile.language_sequence`.

**I-28-11:** The language sequence is not reactive. No execution result, evaluation score, or candidate action may alter the sequence after session start.

**I-28-12:** `SessionHistory` stores `LanguageProfile` in full at session close. Replay always reconstructs the exact same language sequence by reading the stored `LanguageProfile` — never by re-running `InterviewSetup`.

**I-28-13:** `LanguagePolicy` used per question is frozen at session start via `LanguageConfig.evaluation_policy`. Policy changes after session start do not affect the active session.

---

## SECTION F — Future Concepts (Reserved)

### LanguageCapabilityProfile

**Conceptual introduction only. No implementation.**

`LanguageCapabilityProfile` aggregates `LanguageCapabilityFeature` instances across sessions to represent a candidate's language-specific competence history.

- Produced by: `ReplayUpdater` (V1.3+ full activation)
- Consumed by: `ProgressTracker`, `NarrativeGenerator` (language capability trend)
- Language-aware: yes — each profile entry is associated with a `ProgrammingLanguage`
- Knowledge Model: language-independent — the feature type is universal; language is provenance metadata

Reserved. No architecture changes required when activated.

### LanguageFamilyProfile

**Conceptual introduction only. No implementation.**

`LanguageFamilyProfile` represents candidate capability across language families:

| Family | Members |
|---|---|
| Dynamic | Python, JavaScript, Ruby |
| JVM | Java, Kotlin, Scala |
| Systems | Rust, C, C++ |
| CLR | C#, F# |
| JavaScript Family | JavaScript, TypeScript |

`LanguageFamilyProfile` would allow coaching and narrative to reason about candidate transfer capability across languages within a family (e.g. "strong in Python suggests fast ramp in JavaScript"). Reserved for V1.4+.

---

## Rationale

Language selection at session initialisation — not at runtime — is the only design that satisfies three simultaneous requirements: deterministic replay, language-independent knowledge model, and zero runtime coupling between performance signals and language assignment.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Runtime language selection (per question, at question time) | Non-deterministic; breaks replay; allows performance-to-language coupling |
| Candidate-chosen language per question (V1.2) | Introduces UI state management at execution time; deferred to V1.3+ as `CANDIDATE_PREFERENCE` |
| Weighted random selection (V1.2) | Adds non-determinism without proportional value at V1.2 scale; reserved for V1.3+ |
| JavaScript + TypeScript mixed mode | TypeScript is a superset of JavaScript; mixing the two in a single session creates overlapping question pools without added evaluation value; not supported in V1.2 |

## Consequences

### Positive
- Language sequence is deterministic and reproducible; replay is correct by construction
- Topic coverage and language coverage are orthogonal concerns; each is independently maintainable
- `InterviewSetup` is the single point of language configuration; no downstream component needs to make selection decisions

### Negative / Risks
- Mixed-mode session quality depends on question repository depth; if the repository has insufficient questions in one language, topic diversity within that language degrades
- `DETERMINISTIC_ALTERNATING` produces a fixed 50/50 balance regardless of candidate skill or question topology — this is a V1.2 simplification accepted deliberately

## Implementation Evidence

Architecture only. No production files modified.
