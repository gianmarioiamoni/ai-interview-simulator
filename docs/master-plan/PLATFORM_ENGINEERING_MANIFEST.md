# Platform Engineering Manifest
## AI Interview Simulator

**Version:** 1.0  
**Date:** 2026-07-01  
**Status:** FOUNDATIONAL — Authoritative for all versions ≥ V1.1  
**Supersedes:** Nothing. Supplements all other documents.

---

## Purpose

This Manifest is the engineering constitution of the AI Interview Simulator project. It defines how the platform is engineered, not what it does or how it is implemented.

It exists to answer one question permanently: **what does "engineering this platform correctly" mean?**

Every team member, every contributor, every future version is bound by this document.

### Relationship with other documents

| Document | Role | Relationship |
|---|---|---|
| **This Manifest** | Engineering principles and invariants | Highest authority. Defines how all other documents are written. |
| `PRD-V1.1-V1.2.md` | Product requirements | Defines what to build. Must comply with Manifest principles. |
| `TDS-V1.1-V1.2.md` | Technical design | Defines how to build it. Implements the principles here. |
| `ADR-*.md` | Architecture decisions | Records individual decisions. Must be consistent with this Manifest. |
| `README.md` | Repository identity | Describes the platform to the outside world. |
| `INDEX.md` | Document registry | Navigation guide for all master-plan artifacts. |

The Manifest defines principles. Other documents define implementations. If any implementation contradicts a principle in this Manifest, the Manifest wins.

---

## Engineering Philosophy

### 1. Enterprise-first engineering

Every technical decision is evaluated as if the platform will be maintained by a team, extended by contributors who did not write the original code, and operated in production for years. Convenience for the original author is never a valid justification for reducing quality.

### 2. Architecture before implementation

No line of implementation code is written before the architecture of the feature is designed, documented, and reviewed. Architecture is not discovered by writing code — it is designed before code begins.

### 3. Contracts before code

Every component boundary is defined by an explicit, immutable contract before any implementation begins. Contracts are the interface between components. Changing a contract requires an ADR.

### 4. Small independent components

No component is allowed to grow beyond its single stated responsibility. When a component becomes too large, it is decomposed. Dependencies between components are explicit. A component that cannot be tested independently is a design failure.

### 5. Immutability by default

All data transferred across component boundaries is immutable. Mutation is permitted only within a component's own internal scope. All public contracts are frozen after their milestone boundary.

### 6. Deterministic behaviour

Every subsystem that does not require non-determinism must be deterministic. The Interview Reasoner is the canonical example: it produces identical output for identical input, regardless of how many times it is called. Non-determinism is only permitted where the domain explicitly requires it (LLM calls for question generation, humanizer output).

### 7. LLMs are assistants, never decision-makers

No LLM call produces a decision that is surfaced to the candidate without a deterministic validation layer. LLMs generate candidates. Deterministic rules decide. The Interview Reasoner contains zero LLM calls. The FollowUpGuard validates all LLM-generated follow-up output before it reaches the interview graph.

### 8. Explicit over implicit

Configuration is always explicit and centralized. State transitions are documented. Component ownership is stated. No magic numbers, no hidden defaults, no implicit fallbacks. If a behaviour exists, it must be traceable to a configuration value, a contract, or an ADR.

### 9. Composition over inheritance

The platform uses Pydantic mixin composition, registry-backed pipelines, and functional service patterns. Class hierarchies are avoided. Extension points are defined by protocols, not base classes. The detector registry pattern is the canonical example of composition-based extensibility.

### 10. Evidence-driven reasoning

All reasoning about candidate performance is based on typed evidence signals accumulated over the session. No subsystem produces a qualitative judgment without a supporting evidence trail. The `EvidenceStore`, `ReasoningHistory`, and `CandidateProfile` are the three persistent reasoning structures that guarantee this.

### 11. Progressive evolution

Each version builds on the frozen foundation of the previous version. V1.2 extends V1.1 contracts using reserved extension points defined in V1.1 ADRs. No version breaks a previously frozen contract.

### 12. Backward compatibility

Once a public API is frozen, it does not change. Additive evolution (new optional fields, new reserved variants) is permitted. Breaking changes require a new major version and an ADR with full migration plan.

### 13. Stable public APIs

All milestone boundaries are accompanied by an explicit API freeze. After freeze, no API surface changes until the next milestone boundary. The M2-8 Reasoner API Freeze is the canonical example.

---

## Development Workflow

The following order is permanent and non-negotiable.

```
1. Architecture design
        ↓
2. Contract definition (Pydantic, extra=forbid)
        ↓
3. ADR registration
        ↓
4. Implementation
        ↓
5. Unit tests
        ↓
6. Integration tests
        ↓
7. Audit (layering, ownership, configuration, contract compliance)
        ↓
8. Documentation (TDS update, INDEX update)
        ↓
9. Freeze (API freeze, contract freeze, detector freeze)
        ↓
10. Release Certification
```

### Why this order exists

**Architecture before implementation** ensures that structural mistakes are caught before they are encoded in code. Code is expensive to change. Architecture decisions are cheap to change on paper.

**Contracts before implementation** ensures that all component boundaries are stable before any component begins working. A service that begins implementing before its contract is defined will implicitly define the contract through its implementation — producing a contract that reflects the implementation's convenience rather than the domain's requirements.

**ADRs before implementation** ensures that every non-obvious decision is recorded while the reasoning is fresh. An ADR written after implementation is a post-hoc rationalization, not a decision record.

**Audit before freeze** ensures that no structural violation, ownership ambiguity, or configuration gap is frozen into the codebase. Technical debt that reaches a freeze boundary is intentional, registered, and assigned to a future milestone. Unregistered debt is not acceptable.

**Freeze before certification** ensures that the certification process evaluates a stable state. A moving target cannot be certified.

### Why implementation never comes first

Implementation that precedes architecture creates a system where the architecture is discovered retroactively from the code. This produces a system that cannot be reasoned about, extended safely, or certified. Every shortcut taken at implementation time becomes a constraint on every future version.

---

## Architectural Principles

### Domain-Driven Design (DDD)

The platform organises code around domain concepts, not technical layers. `InterviewState`, `EvidenceStore`, `CandidateProfile`, `ReasonerDecision` are domain objects — not database rows, not API responses. The domain layer contains only concepts from the problem domain. It has no dependencies on infrastructure, application framework, or external services.

### Single Responsibility Principle (SRP)

Every module, class, and service has one reason to change. When a service accumulates multiple responsibilities, it is decomposed. File size is a proxy: files exceeding 200 lines are candidates for decomposition.

### Open/Closed Principle (OCP)

The platform is open for extension, closed for modification. The detector registry pattern (ADR-051) is the primary implementation: new detectors are registered without modifying the pipeline. New evidence types extend the catalog without modifying existing detectors.

### Dependency Inversion Principle (DIP)

High-level modules do not depend on low-level modules. Services depend on domain contracts (interfaces), not on infrastructure implementations. LLM access is mediated through `LLMPort`. Infrastructure implements ports; it does not define them.

### Plugin Architecture

The detector framework is a first-class plugin architecture. A detector is a self-contained unit that implements `PatternDetector` (ABC), registers with `PatternDetectorRegistry`, and requires no modification to the core pipeline. The same plugin principle applies to question adapters, embedding providers, and future coaching components.

### Single Writer Principle

Every mutable domain object has exactly one designated writer. `InterviewMemory` is written only by `reasoner_node`. `ReasoningHistory` is written only by `reasoner_node`. `CandidateProfile` is updated only through `CandidateProfileEngine`. Shared mutable state with multiple uncoordinated writers is a design violation.

### Immutable Contracts

All cross-boundary contracts are immutable by default. Pydantic `extra=forbid` prevents unknown field injection. `schema_version` fields allow future validation. Once frozen, a contract field is never removed or renamed — it is deprecated and superseded by a new field.

### Append-only History

`EvidenceStore` and `ReasoningHistory` are append-only. Evidence is never deleted or modified after being written. The full history is always available for audit. Idempotency guards prevent duplicate writes.

### Configuration Centralization

All governance thresholds live in `infrastructure/config/evaluation.py`. All runtime configuration lives in `infrastructure/config/settings.py`. Application structure constants live in `app/settings/constants.py`. No hardcoded governance value exists outside these three files. A value that influences a hire decision must be in `evaluation.py`.

### Small Components

No service file exceeds 200 lines without justification. Detector files are bounded by ADR-056. Services are decomposed into pipeline steps. Builders are separated from orchestrators.

### Pure Domain

The domain layer contains no imports from `app/`, `services/`, or `infrastructure/`. It contains only Pydantic contracts, value objects, policies, and events. Any violation of this principle is registered as High-severity technical debt and assigned to the next milestone.

### Deterministic Services

The Interview Reasoner contains zero LLM calls. Given identical `ReasonerInput`, it always produces identical `ReasonerDecision`. This is not a constraint — it is a design goal. Deterministic services are testable, auditable, and deployable without LLM availability.

---

## Quality Standards

The following standards are permanent. They apply to every version.

- Every public contract is immutable after its milestone freeze.
- Every public API is versioned and frozen at the milestone boundary.
- Every architectural decision is recorded in an ADR before implementation begins.
- Every milestone is audited before certification.
- Every subsystem is independently testable in isolation.
- Every governance threshold is sourced from `evaluation.py` or `settings.py`.
- Every new detector complies with ADR-051 (extensibility contract).
- Every component boundary is defined by an explicit Pydantic contract with `extra=forbid`.
- Every feature that is not yet production-ready is gated by a feature flag.
- No undocumented configuration value influences production behaviour.
- No LLM output reaches the candidate without passing a deterministic validation layer.
- No hidden runtime state exists. All session state lives in `InterviewState`.
- No implicit fallback exists without a documented fallback policy.
- Test coverage of the core reasoning path is mandatory. Coverage gaps are registered as technical debt.

---

## Release Policy

```
Development (active implementation)
        ↓
Freeze (API freeze, contract freeze, feature flag lock)
        ↓
Release Candidate (certification audit, regression suite, acceptance gates)
        ↓
Bug Fix Only (no features, no contract changes after RC tag)
        ↓
Stable Release (tag, release notes, changelog)
        ↓
Next Version (V1.2 opens on main after V1.1 stable merge)
```

### Why features stop after Freeze

The freeze boundary exists to create a stable, certifiable state. A feature added after freeze has not been audited, has not been tested in the full system context, and has not been architecturally reviewed against the frozen contracts. Allowing post-freeze features is equivalent to certifying a system that has not been fully evaluated.

After a freeze boundary:
- No new features.
- No new detectors.
- No new contracts.
- No new ADRs unless a true architectural inconsistency is discovered.
- Bug fixes only, with scope limited to observable defects in already-frozen behaviour.

---

## Technical Debt Policy

### Accepted Technical Debt

Technical debt is accepted when:
- The violation has no observable production impact.
- The violation is registered in the Technical Debt Register with an ID, severity, location, and target milestone.
- The violation does not affect a governance decision path (hire/no-hire, scoring, signal writing).
- The cost of fixing it now exceeds the cost of carrying it to the next milestone.

Accepted debt is not shameful. It is an explicit engineering decision.

### Deferred Technical Debt

Technical debt is deferred when:
- The fix requires an architectural change that is scoped to the next major version.
- The fix depends on a V1.2 extension point (e.g. `ProfileFeature`, `ObservationModel`) that is reserved but not yet implemented.
- A governing ADR explicitly defers the fix (e.g. ADR-039, ADR-048, ADR-055).

Deferred debt must have a target milestone. "Future" is not a milestone.

### Forbidden Technical Debt

Technical debt is forbidden when:
- It affects the correctness of a hire decision.
- It affects the integrity of a frozen public contract.
- It introduces a circular dependency in the production runtime path.
- It causes non-determinism in a deterministic service.
- It bypasses a validation layer (FollowUpGuard, EvidenceStore idempotency guard, contract `extra=forbid`).

Forbidden debt blocks a release. It cannot be accepted or deferred.

### When debt blocks a release

Technical debt blocks a release when it falls into the Forbidden category, or when an Accepted item's actual production impact is discovered to be higher than assessed. The Release Certification process is the gate for this determination.

---

## AI Collaboration Principles

The AI Interview Simulator was engineered using a structured human-AI collaboration methodology. The following principles are permanent for all future development.

### AI assists. Human architects.

AI tooling accelerates design iteration, identifies consistency violations, generates implementation candidates, and validates architectural decisions. It does not make architectural decisions. The human engineer is always the final authority on architecture, contracts, and ADR content.

### Architecture frozen before implementation

No AI-generated implementation is accepted before the architecture is reviewed and frozen by the human engineer. AI-generated code that assumes an unreviewed architecture is discarded, not iterated upon.

### Iterative engineering over single-pass generation

Complex subsystems (the Reasoner, the Humanizer, the detector framework) were built iteratively: design, review, refine, freeze, implement, audit. No subsystem was generated in a single pass. Every iteration was validated against the frozen contracts of the previous iteration.

### Continuous verification

Every implementation phase was followed by an audit phase. The audit verified:
- Layering compliance (no domain imports from services or app).
- Ownership correctness (single writer per mutable object).
- Configuration consistency (all thresholds sourced from SSOT).
- Contract compliance (extra=forbid, schema_version, immutability).

### Evidence over intuition

Architectural decisions were not made on intuition. Every decision was supported by an analysis of the existing system state, the requirements of the next milestone, and the constraints of the frozen contracts. ADRs record the evidence, alternatives considered, and rationale chosen.

### Repeatability

The development process is documented and repeatable. A new contributor can follow the workflow in Section D and produce work that is consistent with the existing platform quality.

### Why this process improved quality

The combination of human architectural authority, AI acceleration, and systematic audit cycles produced a platform where:
- 67 architectural decisions are recorded and traceable.
- 2,802 tests pass with zero failures at V1.1 RC.
- All M1 and M2 public APIs are frozen with documented contracts.
- Every milestone was audited before certification.
- Technical debt is explicit, registered, and assigned — not hidden.

---

## Extensibility

The following protocol is permanent for adding any new capability to the platform.

### Adding a new detector

```
1. Design: define detector responsibility, evidence types consumed, pattern matched
        ↓
2. Contract: define new EvidenceType entries if required (domain catalog)
        ↓
3. ADR: record the detector design, responsibility matrix position, compatibility
        ↓
4. Implementation: implement PatternDetector ABC, register in default_registry.py
        ↓
5. Tests: unit tests (≥ 5 scenarios per ADR-060), isolated from pipeline
        ↓
6. Documentation: TDS section update, detector catalog update in INDEX
        ↓
7. Integration: verify pipeline execution order, performance budget (ADR-054)
        ↓
8. Freeze: detector catalog frozen, API unchanged
```

No shortcuts. A detector that skips any step is not eligible for registry registration.

### Adding a new subsystem

```
1. Architecture design (new section in TDS)
        ↓
2. ADR registration (minimum 1 ADR per subsystem boundary)
        ↓
3. Contract definition (domain/contracts/ for cross-boundary DTOs)
        ↓
4. Port definition (app/ports/ or domain/ports/) if LLM or external dependency
        ↓
5. Implementation
        ↓
6. Tests (unit + integration)
        ↓
7. Audit
        ↓
8. Freeze at milestone boundary
```

### Adding a new contract field

1. The field must be optional or have a default value (backward compatibility).
2. If the field is required, it requires an ADR and a migration plan.
3. `extra=forbid` remains enforced — new fields must be explicitly added to the Pydantic model.
4. `schema_version` is incremented if the change is non-additive.

---

## Engineering Invariants

These invariants are permanent. They cannot be overridden by any ADR, PRD, or implementation decision. They can only be changed by a new version of this Manifest with explicit human approval.

1. **Public APIs remain stable.** A frozen API does not change. Breaking changes require a new major version.
2. **Contracts remain immutable after freeze.** `extra=forbid` is never relaxed on a frozen contract.
3. **Runtime ownership is explicit.** Every mutable domain object has exactly one designated writer. This is documented.
4. **No circular dependencies in the production runtime path.** Import-time cycles in production modules are registered as technical debt and resolved in the next milestone.
5. **Reasoning is deterministic.** The Interview Reasoner produces identical output for identical input. LLM calls are prohibited in deterministic services.
6. **State transitions are explicit.** Every `InterviewState` field mutation is traceable to a specific graph node, documented as part of that node's contract.
7. **Single source of truth for configuration.** Every governance threshold exists in exactly one location. Duplication of governance values across files is Forbidden Technical Debt.
8. **LLMs never modify architecture.** AI tooling assists implementation. Architectural decisions are made by human engineers and recorded in ADRs.
9. **Every evidence signal is typed.** No free-text signal exists in `EvidenceStore`. Every signal has an `EvidenceType`, a `polarity`, a `source`, and a `strength`.
10. **No hire decision is produced without evidence.** A hire decision requires at least `reasoner_coverage_min_questions` evaluated questions and corresponding evidence signals.
11. **Feature-flagged paths are never on by default in production** without explicit validation and documentation.
12. **Deprecated components follow ADR-059.** Deprecated code is retained for exactly one milestone window, then removed.

---

## Success Criteria — Enterprise Grade

"Enterprise grade" for this platform means:

**Predictable** — Given the same candidate responses, the platform produces the same evaluation, the same signals, and the same reasoning. No session produces unexpected behaviour that cannot be traced to a configuration value or a contract.

**Auditable** — Every hire decision is traceable to a `ReasonerDecision`, which is traceable to `EvidenceStore` signals, which are traceable to individual question evaluations. The full evidence trail is available for inspection.

**Maintainable** — A new engineer can understand the purpose, boundaries, and contracts of any component by reading the TDS section, the relevant ADRs, and the component's Pydantic contracts. No tribal knowledge is required.

**Extensible** — A new detector, a new question domain, or a new reasoning dimension can be added without modifying any frozen component. The plugin architecture and reserved extension points (ADR-048, ADR-055, ADR-066) guarantee this.

**Observable** — Every meaningful event in the interview lifecycle is represented as a typed domain event (`FollowUpTriggeredEvent`, `FollowUpSkippedEvent`). LLM calls are observable through the observability adapter. Reasoning traces are available for audit.

**Testable** — Every component can be tested in isolation. The detector pipeline is independently testable. The humanizer guard is independently testable. No test requires a running LLM.

**Deterministic** — The reasoning path (ReasonerService, all 13 detectors, EvidenceStore, CandidateProfileEngine) produces deterministic output. Tests do not use mocks for deterministic services.

**Failure-safe** — The reasoner node never stops an interview due to a reasoning failure. The humanizer guard always falls back to SKIP rather than propagating an invalid follow-up. Every non-deterministic path has a documented fallback.

---

## Future Vision

This Manifest is not version-specific. It defines the engineering identity of the platform across all future versions.

### V1.2

V1.2 activates the extension points reserved in V1.1: `ProfileFeature` (ADR-048), `NarrativeGenerator` (ADR-050), `CoachingEngine` (ADR-067), `ObservationModel` (ADR-055, ADR-066), evidence freshness weighting (ADR-039). All V1.2 work will follow the exact development workflow defined in Section D. All new ADRs will be numbered from ADR-068 upward.

### V2 and beyond

Future major versions may introduce new reasoning paradigms (multi-session memory, cross-interview profile, streaming evaluation). Regardless of how the implementation evolves, these principles remain fixed:
- Architecture before implementation.
- Contracts before code.
- Deterministic reasoning services.
- Immutable frozen contracts.
- Single source of truth for configuration.
- LLMs as assistants, not decision-makers.

### Future plugins

The detector plugin architecture (ADR-051) is designed to support external detector contributions. A third-party detector that implements `PatternDetector` ABC, registers with `PatternDetectorRegistry`, and complies with ADR-053 (compatibility policy) can be integrated without modifying the core platform.

### Future coaching

The `CoachingEngine` (ADR-067) will consume `ProfileFeatures` derived from detector observations. The pipeline is designed so that coaching components never have direct access to raw `EvidenceStore` signals — they consume the structured `ProfileFeature` abstraction. This preserves the separation between evidence accumulation and coaching recommendation generation.

---

## Document History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-01 | Initial Manifest — V1.1 RC foundation |
