# ARC-02 — Architecture Review Checklist

**Version 1.0 | Operationalizes the Architecture Constitution**

---

## Purpose

Every significant architectural change must pass this checklist before approval. A significant architectural change is any proposal that introduces a new runtime artifact, extends an existing pipeline, adds or transfers ownership, modifies an immutable contract, crosses a constitutional boundary, or touches replay, closure, or presentation integration.

This checklist is the operational instrument for:

- Architecture Reviews (CAR)
- new Architecture Decision Records (ADRs)
- major pull requests with structural impact
- major refactorings that affect runtime ownership or contract shape
- introduction of new runtime artifacts
- introduction of new pipelines or pipeline stages
- introduction of new Builders
- replay evolution

The checklist does not replace judgment. It structures it. A reviewer who answers every question without understanding the proposal has not reviewed it. The checklist ensures that no constitutional dimension is overlooked; it does not substitute for architectural reasoning.

This document operationalizes the Architecture Constitution. When the Constitution and this checklist appear to conflict, the Constitution takes precedence. When this checklist does not cover a situation, the reviewer returns to the Constitution directly.

---

## Review Workflow

Apply the following sequence for every review. Steps are ordered to surface the most fundamental violations early, before investment in detailed review.

### Step 1 — Understand the Proposal

Read the proposal in full before evaluating any checklist item. Identify:

- the problem being solved
- the artifacts being introduced, modified, or removed
- the nodes, pipelines, or services being affected
- the lifecycle boundaries being crossed, if any

Do not begin checklist evaluation until you can describe the proposal in one paragraph without consulting the proposal document.

### Step 2 — Identify Affected Artifacts

List every runtime artifact touched by the proposal: created, read, modified, transferred, or deleted. For each artifact, identify its current producer, writer, and declared readers. This list drives every ownership and immutability question in the checklist.

### Step 3 — Identify Constitutional Boundaries Crossed

Determine whether the proposal crosses any of the five constitutional boundaries:

- Computation/Projection Boundary
- Immutable Contract Boundary
- Ownership Boundary
- Orchestration Boundary
- Replay Boundary
- Presentation Boundary

A boundary crossing is not automatically a rejection — it is a signal that an ADR is required before the change is approved.

### Step 4 — Apply the Checklist

Work through sections A through J in order. Record YES, NO, or N.A. for each item. For every NO, record the specific violation in the Review Report (see §Architecture Review Report Template).

### Step 5 — Evaluate ADR Compliance

Identify every active ADR affected by the proposal. Verify that the proposal does not contradict any frozen ADR. If the proposal requires modifying the constraints of an existing ADR, a superseding ADR must be drafted and approved before this proposal is approved.

### Step 6 — Evaluate PAT Compliance

Identify every official pattern (OP-01 through OP-06) that applies to the proposal. Verify compliance with each applicable pattern. A proposal that introduces a pattern violation must either be corrected or accompanied by a constitutional amendment justifying the exception.

### Step 7 — Evaluate Runtime Impact

Assess whether the proposal changes latency, computational cost, or error recovery behavior at runtime. Evaluate whether any computation was moved from the runtime cycle to a closure or projection step, or vice versa. Record the finding.

### Step 8 — Evaluate Replay Impact

Determine whether the proposal affects the deterministic reconstruction contract. Any change to an artifact that is included in a `SessionHistory` or `CandidateProfileSnapshot` potentially affects replay. Evaluate whether the closed artifact remains fully self-contained for reconstruction.

### Step 9 — Evaluate Testing Impact

Identify which tests must be added, updated, or removed. Confirm that ownership invariants, immutability invariants, and sole-writer contracts are covered by tests. Identify any migration-only tests that become dead after the proposal is implemented.

### Step 10 — Approve, Conditionally Approve, or Reject

Apply the criteria in §Review Outcomes and record the decision in the Review Report.

---

## Checklist

Each item is answered: **YES** (compliant), **NO** (violation — must be addressed), or **N.A.** (not applicable to this proposal).

---

### A. Runtime

| # | Question | Answer |
|---|----------|--------|
| A-01 | Is all knowledge computation (LLM calls, feature derivation, signal extraction, reasoning) confined to the live runtime cycle? | |
| A-02 | Does any projection or closure step invoke an Engine, NarrativeGenerator, CoachingEngine, or LLM-backed service? | |
| A-03 | Does any session-close component re-execute a pipeline that was already run during the live cycle? | |
| A-04 | Does any presentation layer component derive or enrich domain knowledge values rather than reading them from a closed artifact? | |
| A-05 | If computation was moved, was it moved into the runtime cycle (not out of it)? | |
| A-06 | Does the proposal preserve the principle that session close is pure assembly? | |
| A-07 | Does the proposal preserve the principle that report generation is pure projection? | |

---

### B. Ownership

| # | Question | Answer |
|---|----------|--------|
| B-01 | Does every affected artifact still have exactly one declared producer? | |
| B-02 | Does every affected artifact still have exactly one declared writer? | |
| B-03 | Are the readers of every affected artifact declared? | |
| B-04 | If ownership is transferred, is the prior owner disabled in the same increment? | |
| B-05 | Does the proposal introduce any parallel production path for an existing artifact? | |
| B-06 | Does any pipeline, service, or utility write to a state field owned by a different node? | |
| B-07 | Is the sole-writer contract of every affected node documented in that node's module? | |

---

### C. Immutability

| # | Question | Answer |
|---|----------|--------|
| C-01 | Are all new domain contracts declared with `frozen=True` or an equivalent immutability guarantee? | |
| C-02 | Are all `InterviewState` updates performed via `model_copy` rather than in-place mutation? | |
| C-03 | Does any code path mutate a domain object after its construction? | |
| C-04 | Do all reconstruction functions enumerate every field of the target type explicitly? | |
| C-05 | If a new field was added to an accumulation artifact, was every reconstruction path updated in the same change? | |
| C-06 | Are there any reconstruction paths that rely on default values to cover fields not explicitly listed? | |
| C-07 | Does the proposal preserve the invariant that a closed artifact (Snapshot, SessionHistory, Report) is never modified after construction? | |

---

### D. Builders

| # | Question | Answer |
|---|----------|--------|
| D-01 | Does every new immutable artifact introduced by this proposal have exactly one Builder? | |
| D-02 | Is direct constructor invocation of any immutable artifact prohibited in production paths? | |
| D-03 | Does any Builder contain conditional business logic, LLM calls, or derivation logic? | |
| D-04 | Does any Engine produce a finished domain artifact directly rather than returning an intermediate result for a Builder to assemble? | |
| D-05 | Does the Builder's `build()` method validate all mandatory fields before constructing the artifact? | |
| D-06 | If an existing Builder is modified, does it remain the sole construction path for its artifact? | |

---

### E. Orchestration

| # | Question | Answer |
|---|----------|--------|
| E-01 | Is LangGraph still the sole runtime orchestrator after this change? | |
| E-02 | Does any new service, pipeline, or coordinator implement control flow by calling other nodes in sequence? | |
| E-03 | Does any pipeline hold a reference to the LangGraph runner or invoke it directly? | |
| E-04 | Does any new component have a name or responsibility suggesting routing, sequencing, or coordination? | |
| E-05 | Do all new pipelines return a result without deciding what the runtime does next? | |
| E-06 | Are all new conditional routing decisions expressed as LangGraph edges and conditions? | |

---

### F. Replay

| # | Question | Answer |
|---|----------|--------|
| F-01 | If the proposal touches any artifact included in `SessionHistory` or `CandidateProfileSnapshot`, is the replay contract still satisfied? | |
| F-02 | Is the replay path fully isolated from the live runtime path? | |
| F-03 | Does the replay path use only replay-designated engines (e.g., `ReplayFeatureEngine`) and never live engines? | |
| F-04 | Does any replay component write to `InterviewState` fields owned by live runtime nodes? | |
| F-05 | Is the reconstructed artifact deterministic given the same `SessionHistory` input? | |
| F-06 | If the proposal modifies a closed artifact's schema, is the replay reconstruction updated to handle the new schema? | |

---

### G. Presentation

| # | Question | Answer |
|---|----------|--------|
| G-01 | Does the UI layer read exclusively from closed artifacts (`state.report`, `SessionHistory`, or equivalent)? | |
| G-02 | Does any DTO mapper, export handler, or view builder derive or compute domain values rather than projecting them? | |
| G-03 | Is the routing signal for the report UI state driven by the presence of the closed Report artifact, not by an intermediate V1.x artifact? | |
| G-04 | Does the Report remain immutable after `report_node` writes it? | |
| G-05 | Are all export handlers (PDF, JSON) consumers of pre-assembled DTOs, not independent derivers of knowledge? | |

---

### H. Testing

| # | Question | Answer |
|---|----------|--------|
| H-01 | Are the ownership invariants of all affected artifacts covered by architectural tests? | |
| H-02 | Are the sole-writer contracts of all affected nodes covered by tests that verify no other node writes the same fields? | |
| H-03 | Are all new Builders tested for mandatory field validation and structural validity of the produced artifact? | |
| H-04 | Are reconstruction paths tested with a complete set of non-default field values to detect silent field omissions? | |
| H-05 | If replay is affected, are determinism tests present? | |
| H-06 | Were any tests that protected now-deleted behavior removed alongside the production code? | |
| H-07 | Were any migration-only tests that are now dead identified and scheduled for removal? | |
| H-08 | Does the test suite for this proposal include at least one test per ownership invariant introduced? | |

---

### I. Legacy

| # | Question | Answer |
|---|----------|--------|
| I-01 | If the proposal activates a new production path, is the superseded path disabled in the same increment? | |
| I-02 | Does any new compatibility bridge carry a declared deletion ticket and target sprint? | |
| I-03 | Are there any deprecated fields, classes, or functions that this proposal leaves active beyond one subsequent increment? | |
| I-04 | Were all test files protecting deleted production behavior removed? | |
| I-05 | Does the proposal leave the codebase with fewer deprecated components than before? | |

---

### J. Performance

| # | Question | Answer |
|---|----------|--------|
| J-01 | Does the proposal introduce any computation that was already performed earlier in the same session cycle? | |
| J-02 | Does the proposal add any Engine invocation, LLM call, or Pipeline execution to a path that did not previously contain one? | |
| J-03 | Are all new Builders computationally lightweight (assembly only, no derivation)? | |
| J-04 | Does the proposal introduce any synchronous blocking operation on the critical path that could degrade session responsiveness? | |
| J-05 | If the proposal adds a new closure or projection step, is it sufficiently fast to be non-observable to the end user? | |

---

## Review Outcomes

### APPROVED

All checklist items return YES or N.A. No constitutional boundary is crossed without a corresponding ADR. No PAT violation is present. The reviewer is satisfied that the proposal is architecturally sound and the testing impact is fully addressed.

The proposal may proceed to implementation without further architectural review.

### APPROVED WITH ACTIONS

One or more checklist items return NO, but the violations are correctable without redesign. Alternatively, the proposal crosses a constitutional boundary and the required ADR has been drafted and is pending approval.

The proposal may proceed to implementation only after all required actions are completed and verified. The Review Report must enumerate every required action with a named owner and a target sprint.

### REJECTED

One or more checklist items return NO and the violations require fundamental redesign. Alternatively, the proposal crosses a constitutional boundary without a corresponding ADR, or the proposal contradicts a frozen ADR that cannot be superseded without broader architectural consensus.

The proposal must be revised before re-submission. The Review Report must specify precisely which constitutional principles were violated and what architectural change would be required to satisfy them. A rejection is not a final decision on the underlying need — it is a determination that the current implementation approach is constitutionally unacceptable.

---

## Common Failure Patterns

These are the recurring patterns that most frequently cause proposals to receive NO answers on checklist items. Reviewers should inspect for these patterns proactively before working through the full checklist.

**Dual Ownership.** A new production path is activated while the prior production path remains active. Manifests as two services, builders, or nodes that can both produce or write the same artifact. Detected via B-01, B-02, B-04, B-05.

**Hidden Orchestration.** A service or pipeline that calls other components in a sequence implementing control flow. Manifests as a class named "Coordinator," "Runner," or "Manager" that holds references to multiple nodes or pipelines. Detected via E-01 through E-06.

**Close-Time Recomputation.** An Engine, LLM call, or Pipeline execution invoked inside a session-close or report-generation component. Manifests as an import of `FeatureEngine`, `NarrativeGenerator`, `CoachingEngine`, or any LLM client inside `session_close_node`, `report_node`, or any downstream projection. Detected via A-02, A-03, A-06.

**Mutable Domain Contracts.** A domain object modified after construction via direct field assignment. Manifests as any assignment to a field on a domain object outside of a `model_copy` call or Builder. Detected via C-01 through C-03.

**Builders Performing Computation.** A Builder that contains conditional business logic, LLM calls, or feature derivation. Manifests as `if/else` logic in `build()` that changes what the artifact contains based on domain rules. Detected via D-03.

**Reconstruction by Omission.** A reconstruction function that copies a subset of fields and relies on defaults for the rest. Manifests as a constructor call that lists fewer fields than the target type declares. Detected via C-04, C-05, C-06.

**Silent Runtime Fallback.** A conditional branch that changes effective behavior without emitting an observable warning. Manifests as `if component is None: use_legacy_component()` without a log statement. Detected via E-04 and by manual inspection of fallback paths.

**Compatibility Bridge Without Deletion Plan.** A bridge, adapter, or translation layer introduced during migration that carries no declared deletion ticket. Detected via I-02. Any bridge that answers N.A. to I-02 is itself a finding.

**Parallel Production Paths.** A migration that introduces a new production path without disabling the prior path. Differs from Dual Ownership in that the parallel paths may serve different callers. Both paths producing the same class of artifact is the violation. Detected via B-05, I-01.

**Presentation-Layer Computation.** A DTO mapper, view builder, or export handler that derives or enriches knowledge values from raw state fields rather than reading from a closed artifact. Detected via G-01, G-02, G-05.

---

## Architecture Review Report Template

Use this template to record the outcome of every Architecture Review, ADR evaluation, and significant architectural pull request review.

---

```
# Architecture Review Report

**Proposal title:**
**Review date:**
**Reviewer(s):**
**Proposal type:** [ ] CAR  [ ] ADR  [ ] Pull Request  [ ] Refactoring  [ ] Other

---

## Overview

[One paragraph describing the proposal: the problem being solved, the approach taken,
and the primary artifacts affected.]

---

## Affected Components

| Component | Type | Change Type |
|-----------|------|-------------|
|           |      |             |

Change types: Created / Modified / Deleted / Ownership transferred / Schema changed

---

## Constitutional Boundaries Crossed

| Boundary | Crossed? | ADR Present? |
|----------|----------|--------------|
| Computation/Projection |  |  |
| Immutable Contract     |  |  |
| Ownership              |  |  |
| Orchestration          |  |  |
| Replay                 |  |  |
| Presentation           |  |  |

---

## Checklist Summary

| Section | Items | YES | NO | N.A. |
|---------|-------|-----|----|------|
| A. Runtime       |  |  |  |  |
| B. Ownership     |  |  |  |  |
| C. Immutability  |  |  |  |  |
| D. Builders      |  |  |  |  |
| E. Orchestration |  |  |  |  |
| F. Replay        |  |  |  |  |
| G. Presentation  |  |  |  |  |
| H. Testing       |  |  |  |  |
| I. Legacy        |  |  |  |  |
| J. Performance   |  |  |  |  |

---

## Violations Found

[For each NO answer, describe the specific violation, the checklist item that surfaced it,
and the corrective action required.]

| Item | Violation | Required Action | Owner | Target Sprint |
|------|-----------|-----------------|-------|---------------|
|      |           |                 |       |               |

---

## ADR Compliance

[List every active ADR affected by this proposal and whether the proposal is compliant,
requires a superseding ADR, or is not applicable.]

| ADR | Compliance | Notes |
|-----|------------|-------|
|     |            |       |

---

## PAT Compliance

[List every official pattern applicable to this proposal and whether it is followed,
violated, or not applicable.]

| Pattern | Compliance | Notes |
|---------|------------|-------|
|         |            |       |

---

## Risks

[Identify risks specific to this proposal: correctness risks, regression risks,
replay integrity risks, ownership ambiguity, or migration sequencing risks.
Rate each as LOW / MEDIUM / HIGH.]

| Risk | Severity | Mitigation |
|------|----------|------------|
|      |          |            |

---

## Testing Impact

[Describe what tests must be added, updated, or removed. Identify any architectural
invariant tests required. Identify any migration-only tests that become dead.]

---

## Decision

[ ] APPROVED
[ ] APPROVED WITH ACTIONS
[ ] REJECTED

**Rationale:**

[State the primary reason for the decision. For APPROVED WITH ACTIONS and REJECTED,
reference the specific checklist items and constitutional principles that drove the decision.]

---

## Required Actions (if applicable)

[Enumerate every action required before the proposal may be implemented or re-submitted.]

| # | Action | Owner | Target Sprint | Blocking? |
|---|--------|-------|---------------|-----------|
|   |        |       |               |           |
```

---

## Relationship with the Constitution

This checklist exists at the second level of the architectural hierarchy:

```
Architecture Constitution
        ↓
Architecture Review Checklist   (this document)
        ↓
Architecture Reviews (CAR)
        ↓
Architecture Decision Records (ADRs)
        ↓
Pattern Application Tracking (PATs)
        ↓
Migration Tickets
        ↓
Implementation
```

The Constitution defines what is true. This document defines how to verify it. When the Constitution is amended, this checklist must be reviewed for consistency. When this checklist is updated, it must not introduce criteria that contradict the Constitution.

This document should remain stable across releases. It evolves only when the review methodology itself changes — not when a new feature is added, a new ADR is issued, or a migration is completed. An update to a checklist item requires the same justification as a constitutional amendment: evidence from experience that the current formulation fails to detect a class of violation, or that it generates false positives that impede legitimate architectural evolution.

Every reviewer who applies this checklist is accountable for understanding the rationale behind each item. The checklist is not a bureaucratic gate. It is the operationalization of lessons learned at significant cost. Applying it without understanding it produces neither safety nor quality.
