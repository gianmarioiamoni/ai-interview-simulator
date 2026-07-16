# V1.3 Development Playbook

**Status:** ACTIVE — Version 1.0  
**Date:** 2026-07-16  
**Precondition:** V1.3 Product Master Plan frozen  
**Authority:** This document is the operational handbook for all V1.3 engineering work. It complements and does not replace the Architecture Constitution (`ARC-01`), the Enterprise Engineering Playbook, or the Platform Engineering Manifest.

---

## 1. Purpose

The V1.3 Product Master Plan defines what will be built. This playbook defines how it will be built.

It is not a specification. It is not a design document. It is the set of operational habits, review triggers, workflow constraints, and collaboration norms that govern every engineering decision from the first V1.3 increment to the production release tag.

It should be consulted at the start of every epic, before every architectural decision, and whenever a process question arises during implementation.

This document is expected to outlast V1.3. It should be maintained and evolved as lessons are learned.

---

## 2. Engineering Principles

These principles govern every implementation decision in V1.3. They are derived from V1.2 lessons and are operative, not decorative.

### Runtime First

All knowledge computation occurs within the live runtime cycle. Session close is projection. Report generation is projection. Replay is controlled recomputation under an explicit flag. No LLM call, no feature derivation, and no pipeline execution occurs outside `reasoner_node` and its direct dependencies. This is a constitutional constraint — any exception requires a new ADR.

### Single Writer

Every runtime artifact has exactly one producer and exactly one writer. Before implementing any new artifact, declare its sole writer explicitly. If a migration temporarily creates two paths to the same artifact, the legacy path must be disabled in the same increment the new path is activated. There are no exceptions to this rule.

### Fail Fast

Silent fallbacks are architectural violations. Any code path that changes behavior without emitting an observable error is prohibited. The default for any unmet precondition is `RuntimeError`, not a silent degradation. This applies to node configuration, reconstruction completeness, and dependency resolution.

### Evidence Before Refactor

Refactoring decisions are not made on intuition. Before any refactoring is proposed, the evidence must exist: an audit finding, a PAT violation, a failing architectural invariant, or a measurable performance issue. Refactoring without evidence is scope creep.

### Architecture Before Implementation

No implementation increment begins without a completed architecture review. Contracts are defined before code is written. ADRs are accepted before implementation depends on them. The cost of architecture on paper is negligible. The cost of architecture discovered during implementation is high.

### Deletion Is Completion

A migration is not done until the legacy artifact is deleted from the codebase. Deprecated-but-not-deleted code is not a milestone. It is a debt item. Every migration increment must have an explicit deletion target, and that target must be closed before the epic is marked done.

### Small Incremental Changes

Every change addresses one logical concern. Mixed commits — where a refactor, a feature, and a test fix are bundled together — obscure history, complicate review, and make bisection impossible. One logical change per commit. One concern per pull request.

### One Responsibility per Component

A component that does two things should be two components. This applies to nodes, services, pipelines, builders, and engines. File size approaching 200 lines during design is a signal to decompose before implementation, not after.

### Product Before Features

V1.3 is the production release. Completion and correctness of committed epics take priority over adding new scope. If a new idea surfaces during implementation, it is assessed against the Deferred Features list in the Master Plan. If it is not already there, it belongs there — not in V1.3.

### Implementation Dependency Validation

Before implementation begins, every commit boundary in the Implementation Plan must be validated for self-containment. This review is mandatory and independent from Architecture Freeze. It verifies:

- Every commit is independently implementable — it depends only on artefacts introduced by prior commits, not by later ones.
- Every commit has an executable test gate — at least one test can be written and run at that commit boundary without requiring artefacts from future commits.
- No circular implementation dependencies exist between commits within or across phases.
- Every commit can leave the full regression suite green when applied in sequence.

If a commit boundary fails this validation, the commit must be redesigned — either merged into an adjacent commit, resequenced, or split — before the Implementation Plan is accepted. This review is performed by the author of the Implementation Plan immediately after drafting the commit boundary table, before the plan is submitted for Architecture Freeze review.

### Plan Correction Rule

When an implementation sequencing issue is discovered during implementation — one that affects only the ordering of commits and not the target architecture, ADRs, ownership, contracts, data model, or target behaviour — it is permitted to update the Implementation Plan without a full Architecture Freeze.

Such a correction requires only a Mini Architecture Freeze (§10), which verifies:

- The target architecture is unchanged.
- No ADR is modified.
- No ownership rule changes.
- No contract changes.
- No data model changes.
- No target behaviour changes.

If all of these conditions are satisfied, the correction is recorded in the Implementation Plan revision note and committed as a documentation-only change. Implementation may resume immediately after the Mini Architecture Freeze passes.

If any of these conditions is not satisfied, the correction is a design change — not a sequencing correction — and requires a full Freeze Integrity Check and potentially a new ADR before any modification is committed.

### Architecture-First Discipline

The frozen architecture is the implementation contract. Implementation follows architecture — architecture does not emerge from implementation.

- **Frozen architecture is non-negotiable.** Implementation that contradicts a frozen ADR, Domain Contract, or Data Model is a violation, not a design improvement.
- **No architectural drift.** Every file created or modified during implementation must be traceable to a frozen planning document. If it is not traceable, it is out-of-scope.
- **No opportunistic refactoring.** Refactors that are not mandated by a frozen planning document are prohibited during implementation phases. They are Technical Debt Register items for the next applicable epic.
- **Strict phase isolation.** Each implementation phase has a declared scope (§4 of the Implementation Plan). Work outside that scope is a phase violation, regardless of whether the out-of-scope change is beneficial.

### Zero Known Failing Tests

Every implementation phase, every commit, and every save-token milestone must leave the runtime operational and the complete regression suite green. Planned failing tests are never accepted. If a migration would temporarily break the runtime or the test suite, the implementation plan must introduce bridge phases that restore full green before the breaking removal is committed. A broken test suite is not a milestone — it is a process violation.

### Conversation Boundary Optimization

Long-running implementation work must balance token cost against implementation continuity. Prefer continuing the current conversation while working inside the same implementation milestone or tightly coupled commit sequence. Prefer starting a new conversation only after completing a natural architectural boundary — for example, end of a milestone, end of a phase, end of an EPIC, Architecture Freeze, or Final Review.

The decision must always weigh token savings from a shorter context against the token cost required to reconstruct implementation context. Never restart a conversation in the middle of a tightly coupled implementation sequence unless context size clearly outweighs reconstruction cost.

This principle complements Zero Known Failing Tests (green suite at every milestone), Implementation Dependency Validation (self-contained commit boundaries), the Plan Correction Rule (sequencing corrections resume without full freeze), and the Freeze Integrity Check (frozen-document changes before resume). It does not alter those gates; it governs when conversation context itself should be reset.

---

## 3. Epic Workflow

Every V1.3 epic follows this lifecycle. The sequence is mandatory. Steps may not be skipped or reordered.

```
1. Epic Planning
        ↓
2. Architecture Governance (ADR / PAT / Constitution review — if required)
        ↓
3. Contract Definition
        ↓
4. Architecture Freeze
        ↓
5. Implementation Plan
        ↓
6. Macro Phase
        ↓
7. Architecture Checkpoint
        ↓
8. Next Macro Phase (repeat 6–7 until all phases complete)
        ↓
9. Architectural Review (CAR)
        ↓
10. Regression
        ↓
11. Documentation Update
        ↓
12. Final Review (FR)
        ↓
13. Epic Close
```

### Macro Phase Lifecycle

Within Category B epics, implementation is structured into macro phases. Each macro phase follows this mandatory lifecycle:

```
Architecture Freeze
        ↓
Implementation Plan
        ↓
Macro Phase
        ↓
Architecture Checkpoint
        ↓
Next Macro Phase
```

No macro phase may begin until the Architecture Checkpoint for the preceding phase has been completed and has explicitly authorized the next macro phase. Architecture Checkpoints are mandatory — they may not be skipped.

Architecture Checkpoints are mandatory review gates executed ONLY after completion of the corresponding Macro Phase. Intermediate reviews may be performed when useful, but they are informal reviews and shall not replace the official Architecture Checkpoint defined by the Implementation Plan.

### Step 1 — Epic Planning

Read the epic definition in the Master Plan. Confirm preconditions (prior epics, dependencies). Identify all artifacts the epic will produce, modify, or delete. Identify all `InterviewState` fields the epic touches and verify their declared ownership. Identify whether any new ADR or PAT is required before implementation can begin.

When the Implementation Plan commit boundary table is drafted, apply the Implementation Dependency Validation rule (§2) before the plan is accepted. Each commit boundary must be independently implementable and testable. This review is recorded in the epic planning commit message.

### Step 2 — Architecture Governance

If the epic introduces a new design decision, a new pattern, or a modification to a frozen contract, the governance step is mandatory before any code is written. This may include: drafting and accepting a new ADR; evaluating a proposed pattern through the standard PAT governance process; or proposing an amendment to the Architecture Constitution. No governance artifact is adopted without completing the normal review process. This step may be lightweight for straightforward epics and thorough for foundational ones (e.g., EPIC-V13-01, EPIC-V13-02).

### Step 3 — Contract Definition

Define all new domain contracts before writing implementation code. All contracts are `frozen=True` (or equivalent). All contracts use `extra=forbid`. No implementation begins on any component whose contract is not frozen.

### Step 4 — Architecture Freeze

Confirm that all decisions required for implementation are frozen, unambiguous, and consistent. For Category B epics, Architecture Freeze is the formal gate defined in §8. For Category A epics, accepted ADRs are the equivalent decision freeze. Implementation planning and coding must not begin until this gate passes.

### Step 5 — Implementation Plan

Produce the commit boundary table and phase breakdown. Apply Implementation Dependency Validation (§2) before the plan is accepted. For Category B, the Implementation Plan must satisfy Definition of Done §8.6.

### Step 6 — Macro Phase

Implement against frozen contracts and accepted ADRs within the declared phase scope. Each commit addresses one logical concern. No mixed refactors. No silent fallbacks. Every new `InterviewState` field must have a declared sole writer at the moment of addition. Every reconstruction path must explicitly enumerate every field it copies (Reconstruction Completeness). Dead code is deleted, not deprecated. Every phase and commit must satisfy Zero Known Failing Tests (§2). See Macro Phase Lifecycle above.

### Step 7 — Architecture Checkpoint

After each completed macro phase, perform the official Architecture Checkpoint (§10). Intermediate informal reviews may help but do not authorize the next macro phase. The checkpoint must explicitly authorize (or block) the next macro phase.

### Step 8 — Next Macro Phase

Repeat Steps 6–7 until all macro phases are complete. No macro phase may begin until the preceding Architecture Checkpoint has authorized it.

### Step 9 — Architectural Review (CAR)

After all macro phases are complete, perform a Construction Architecture Review (architecture-conformance certification — see §10). Verify: layering compliance (no domain-to-infrastructure imports); single ownership (no new dual-path violations); constitutional compliance (no computation in projection paths); PAT compliance (all operative patterns followed); and that all `InterviewState` fields have declared ownership. For Category B epics, Architecture Traceability Review is mandatory (§10). P0/P1 findings block the epic from advancing. P2/P3 findings are registered in the Technical Debt Register.

### Step 10 — Regression

Run the full test suite. All V1.2 acceptance criteria must continue to pass. All new epic acceptance criteria must pass. Zero failures permitted to close the epic.

### Step 11 — Documentation Update

Update all affected documents: the Master Plan (if epic scope changed), the Architecture Guide, relevant ADRs (status update), the INDEX (new frozen components, new ADRs), and the Technical Debt Register (new findings or closed items). Documentation is not optional and is not deferred. For Category B living-status rules, see §9 Documentation Certification.

### Step 12 — Final Review (FR)

Perform the Final Review after Documentation Update is complete. The FR is the mandatory Epic-closure gate defined in §10. It produces a binary outcome: Closed or Blocked. A Blocked FR must enumerate blocking findings before any work on the next Epic begins.

### Step 13 — Epic Close

The Epic is formally closed when the FR passes. At this point: all acceptance criteria are satisfied; zero P0/P1 architectural findings remain open; all documentation is updated; all legacy artifacts targeted for deletion are deleted; the regression suite passes in full; and the FR has produced a Closed outcome.

---

## 4. Definition of Ready

An epic is ready to start when all of the following are true:

- All epics it depends on are closed (see Master Plan §8 for sequencing).
- The epic definition in the Master Plan is unambiguous — scope, expected outcome, and non-goals are clear.
- All frozen contracts the epic depends on have been verified to be in their final form.
- Any design decisions that must be resolved before implementation are identified (ADR candidates are named, not necessarily written yet).
- No open P0/P1 findings from prior epics affect the artifacts this epic will touch.
- The sole writer of every `InterviewState` field the epic will create or modify is identified.

---

## 5. Definition of Done

An epic is done when all of the following are true:

- All acceptance criteria defined in the Master Plan for this epic are satisfied.
- All artifacts the epic was expected to produce exist, are correct, and are covered by tests.
- All artifacts the epic was expected to delete have been deleted from the codebase.
- The CAR has been performed and all P0/P1 findings are resolved.
- For Category B epics, Architecture Traceability Review has passed (§10).
- The full regression suite passes with zero failures.
- All new ADRs are in Accepted status.
- All affected documentation has been updated (Architecture Guide, INDEX, ADRs, Technical Debt Register).
- The Technical Debt Register reflects all P2/P3 findings from this epic with target milestones.
- No deprecated-but-not-deleted artifacts from this epic remain in the codebase.
- The Final Review (FR) has been performed and has produced a Closed outcome.

---

## 6. Commit Guidelines

### One Logical Change per Commit

A commit represents one indivisible unit of intent. A refactor and a feature are not the same intent. A test fix and a contract addition are not the same intent. When in doubt, split.

### Commit Message Format

```
<type>(<scope>): <subject>

<optional body — motivation or constraint, not description of what changed>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `delete`

The scope is the epic or component affected (e.g., `scoring-pipeline`, `replay-engine`, `longitudinal-profile`).

The subject is imperative, present tense, ≤ 72 characters: "retire InterviewEvaluation from routing layer", not "retired InterviewEvaluation".

The optional body explains why the change was made, not what it does. Code explains what. The commit message explains why.

### What a Commit Must Never Mix

- A feature addition and a refactor of unrelated code.
- A migration step and a test coverage expansion.
- A contract change and a documentation-only update.
- A deletion and a new feature addition.

### Delete Commits

Deletion commits are first-class commits. A commit that deletes a legacy artifact is as important as a commit that adds a new one. It should be a standalone commit with a clear subject: "delete InterviewEvaluation and all construction paths".

### Atomic Phase Commits

Every implementation sub-phase ends with exactly one atomic commit. The commit must leave the regression suite green. If the automated commit flow is unavailable, the following commands must be provided as the completion artifact:

```
git add .
git commit -m "<type>(<scope>): <subject>"
```

No sub-phase is complete without its commit. A sub-phase with uncommitted changes is not a milestone — it is incomplete work.

---

## 7. Testing Strategy

### Philosophy

Tests verify behavior and structural correctness, not implementation details. A test that breaks when an internal variable is renamed is testing the wrong thing. A test that breaks when a node returns an artifact with a different ownership is testing the right thing.

### Behavioral Tests

Every epic produces behavioral tests: tests that verify the output of a pipeline stage given a defined input, without asserting on internal state. For scoring pipeline tests: given a session with known signals, the `Report` contains the expected scores — not "the `ReportBuilder.build()` method was called with these arguments."

### Architectural Invariant Tests

Domain invariants from `V1.2-DOMAIN-FREEZE.md` must be enforced by tests where possible. Priority invariants for V1.3:

- **I-11:** Replay never invokes LLM calls — enforced by architectural test that mocks and asserts no LLM service is invoked during `replay_node` execution.
- **P-02 (Single Ownership):** Tests that verify `InterviewEvaluation` is not referenced in any production path after EPIC-V13-01.
- **Reconstruction Completeness:** Tests that verify every field of a reconstructed immutable object is explicitly populated (no silent defaults).

### Contract Tests

Every new domain contract (`frozen=True`) has a test that verifies: the contract cannot be mutated post-construction; `extra=forbid` rejects unknown fields; the sole builder produces a valid instance; and the contract is self-consistent (invariants internal to the contract hold).

### What Not to Test

Do not write tests that assert on: internal variable names; call order within a single service; private method return values; or LLM prompt content (prompt content is not a behavioral contract). These tests create brittleness without providing correctness guarantees.

### Zero Known Failing Tests — Enforcement

The Zero Known Failing Tests principle (§2) applies to every individual phase and commit, not only at epic boundaries. Specifically:

- No commit may be tagged a save-token or a phase completion while any test in the suite is failing.
- If implementing a migration phase in one commit would produce failing tests, that phase must be split: an additive bridge phase (which passes) must precede any removal phase (which also passes after all readers are updated).
- A test that is expected to fail after a future phase is not a "known failing test" — it is scope for the next phase and must not exist in the committed codebase.

### Regression Baseline

The V1.2 regression suite is the baseline. It must pass in full at every epic boundary. Any regression introduced by a V1.3 increment must be fixed before the increment is merged — regressions are never deferred to the end of an epic.

### Test Count Target

Total passing tests ≥ 2,500 at V1.3 release gate (Master Plan §5).

---

## 8. Epic Planning Workflow

The EPIC-01 planning process established the standard workflow for V1.3 epics. This section formalises that workflow and makes it mandatory for all subsequent epics. Category selection here determines the pre-implementation path; Epic Close still follows §3 Steps 9–13 (CAR → Regression → Documentation Update → FR → Epic Close).

Two categories of epic exist. The category determines the mandatory pre-implementation workflow. Misclassifying an epic as Category A when it belongs in Category B is a process violation.

---

### Category A — Standard Epics

Applies to epics that do not introduce new domain contracts, new persistent artifacts, new builders, new immutable models, or new serialization contracts.

**Mandatory workflow:**

1. **Master Plan** — Epic scope, purpose, dependencies, and success criteria defined in the Master Plan or in a dedicated epic planning document under `docs/master-plan/epics/`.
2. **Architecture Review** — An explicit review pass that identifies affected subsystems, confirms no missing decisions, and declares the epic ready for ADR.
3. **ADR** — One or more ADRs frozen in `docs/decisions/` that cover every architectural decision the epic requires.
4. **Implementation** — Incremental implementation against frozen decisions. No architectural choices during coding. Zero Known Failing Tests (§2) applies.
5. **CAR (Construction Architecture Review)** — Architecture-conformance certification against ADR decisions and epic success criteria (§10).
6. **Regression** — Confirms the full test suite passes and no regressions were introduced (§3 Step 10). Do not abbreviate this step as "RR" — RR means Release Readiness Review (§10).
7. **Documentation Update** — Living status and affected docs updated (§3 Step 11; §9).
8. **FR (Final Review)** — Epic-closure gate (§10). Binary outcome: Closed or Blocked.
9. **Epic Close** — Epic is declared complete when the FR passes. No further changes to the epic scope.

---

### Category B — Major Architectural Epics

Applies whenever the epic introduces or substantially changes any of the following:

- Domain contracts (`frozen=True` Pydantic models, enums, value types)
- Persistent artifacts (anything written to `SessionHistory`, `Report`, or a future database)
- Builders (`*Builder` classes)
- Immutable models (any `frozen=True` or `__slots__`-based domain object)
- Report structures (any change to `Report`, `FinalReportDTO`, or report section renderers)
- Replay structures (any change to `SessionHistory`, `ReplaySession`, or `ReplayMetadata`)
- Longitudinal models (`LongitudinalProfile`, `CandidateProfileSnapshot`, `LearningProgress`)
- State contracts (`InterviewState` fields, their declared owners, or their write order)
- Serialization models (any change to `schema_version` or stored data shape)

**Mandatory workflow:**

1. **Master Plan / EPIC Initialization** — Epic scope, purpose, dependencies, non-goals, and success criteria. Create/maintain living `EPIC-NN-OVERVIEW.md` for workflow status markers (distinct from frozen Architecture Discovery). Initialization must remain architecture-neutral: it identifies the problem space and does not propose presentation mechanisms, ownership solutions, or other design alternatives. Initialization must include a **Known Inputs** section (see below) before the Architecture Assumptions Register.
2. **Architecture Discovery** — Full analysis of current state, target state, all affected subsystems, open decisions, and structural gaps. Produces a structured report of confirmed decisions, missing decisions, and risks. Does not produce code. Must contain a Component Inventory section (for UI-bearing epics) and populates the Architecture Assumptions Register. See Definition of Done §8.1.
3. **Domain Contracts** — A dedicated domain contract specification document under `docs/master-plan/epics/`. Specifies the complete field set, types, validation invariants, ownership, lifecycle, and relationships of every new artifact. Contains the Traceability Matrix linking Master Plan requirements to domain contract fields. Precise enough that implementation is mechanical. See Definition of Done §8.2.
4. **Data Model Specification** — A dedicated data model document. Resolves all open modelling decisions left by the Domain Contracts document. Freezes the complete field tables for all affected artifacts. Verifies replay completeness. Evaluates future extensibility. All Architecture Assumptions must be VERIFIED before this document is declared complete. See Definition of Done §8.3.
5. **Architecture Review / ADR (conditional)** — Evaluate whether any genuine unresolved architectural decision remains after Domain Contracts and Data Model. Existing ADRs shall be reused whenever possible. A new ADR shall be created only if a genuine unresolved architectural decision remains at this stage. Do not create ADRs proactively. See Definition of Done §8.4.
6. **Architecture Freeze** — A formal gate (described below). Implementation Plan and Implementation cannot begin before Architecture Freeze passes. All Architecture Exit Criteria (§8.7) must be satisfied. See Definition of Done §8.5.
7. **Implementation Plan** — Commit boundary table with Implementation Dependency Validation. Phase breakdown. Regression baseline declared. See Definition of Done §8.6.
8. **Implementation** — Incremental implementation against frozen contracts (Macro Phase Lifecycle, §3). No architectural choices during coding. Every phase must satisfy the Zero Known Failing Tests rule (§2). Bridge phases must be introduced wherever a migration would otherwise produce a temporarily broken runtime or test suite. If an unresolved question emerges, apply the Stopping Rule (below).
9. **CAR (Construction Architecture Review)** — Architecture-conformance certification; includes mandatory Architecture Traceability Review (§10).
10. **Regression** — Confirms the full test suite passes with no regressions (§3 Step 10). Do not abbreviate this step as "RR" — RR means Release Readiness Review (§10).
11. **Documentation Update** — Living status and affected docs updated (§3 Step 11; §9 Documentation Certification).
12. **FR (Final Review)** — Epic-closure gate (§10). Binary outcome: Closed or Blocked.
13. **Epic Close** — Epic is declared complete when the FR passes. No further scope additions.

---

### Architecture Freeze

Architecture Freeze is a mandatory gate between the planning phase (steps 1–5 of Category B) and Implementation Plan / Implementation (steps 7–8). It is not a document — it is a verification checkpoint.

**Purpose:** Confirm that all decisions required for implementation are frozen, unambiguous, and consistent before a single line of production code is written.

**Architecture Freeze passes when all of the following are true:**

- All architectural decisions are frozen in one or more accepted ADRs.
- All domain contract field sets, types, validation invariants, and ownership rules are specified in the Domain Contracts document.
- All data model decisions (field structures, serialization rules, replay completeness, extensibility) are frozen in the Data Model Specification.
- No open architectural questions remain in any planning document. Questions marked "open issue" must be resolved before the freeze, not deferred to implementation.
- Every new artifact has a declared sole writer, declared readers, and a declared lifecycle.
- The `FinalReportDTO` field mapping from `Report` is complete and every field is traceable to a specific source.
- Replay completeness has been verified: every report section can be reconstructed from `SessionHistory` without LLM calls.

**Implementation cannot begin until Architecture Freeze passes.**

If a planning document contains unresolved open issues at the time of the freeze, those issues must be resolved and the affected planning documents updated before the freeze is declared.

---

### Known Inputs (mandatory at EPIC Initialization — Category B)

Every Category B epic Initialization Report (recorded in or referenced from the living `EPIC-NN-OVERVIEW.md`) shall include a **Known Inputs** section immediately before the Architecture Assumptions Register.

**Purpose:** List every existing artifact that Architecture Discovery is expected to inspect, so Discovery begins from an explicit inventory of current inputs rather than from invented scope.

**Content rules:**

- The section shall contain **only already existing artifacts**.
- No new architectural decisions may appear in this section.
- No analysis, findings, alternatives, or assumptions may appear in this section.
- Typical groupings (include those that apply): Existing ADRs; Existing domain artifacts; Existing presentation artifacts; Existing report artifacts; Existing UI host components.

Known Inputs are an Initialization deliverable. They are not a substitute for Architecture Discovery Component Inventory, Domain Contracts, or Data Model.

---

### Document Responsibilities

Each planning document has a unique responsibility. Documents must not duplicate each other's content. If the same information appears in two documents, one of them is wrong.

| Document | Unique Responsibility |
|----------|-----------------------|
| **Master Plan** | Epic scope, purpose, product goals, dependencies, non-goals, success criteria. Does not specify field-level data. |
| **EPIC Overview / Initialization** | Living workflow status; Initialization Report (architecture-neutral problem space, Known Inputs, initial Assumptions Register). Does not invent architecture or choose presentation mechanisms. |
| **Architecture Discovery** | Analysis of current state vs target state. Identifies affected subsystems, confirmed decisions, missing decisions, and risks. Contains Component Inventory (for UI-bearing epics). Populates Architecture Assumptions Register. Produces findings only — no decisions. |
| **ADR** | Freezes decisions. Evaluates alternatives. Records rationale. Specifies migration impact. Each decision is owned by exactly one ADR. Created only when a genuine unresolved architectural decision cannot be resolved by existing ADRs. |
| **Domain Contracts** | Field-level specification of every new or changed artifact: types, defaults, constraints, validators, ownership, lifecycle. Contains Traceability Matrix linking Master Plan requirements to domain fields. Does not evaluate alternatives (that is the ADR's job). |
| **Data Model Specification** | Resolves all open modelling questions left by the Domain Contracts document. Freezes complete field tables. Verifies replay completeness. Evaluates extensibility. All Architecture Assumptions must be VERIFIED before this document is declared complete. Does not re-specify invariants (that is the Domain Contracts' job). |
| **Architecture Freeze** | Formal gate document. Confirms all Architecture Exit Criteria are satisfied. Authorises implementation to begin. |
| **Implementation Plan** | Commit boundary table with dependency validation. Phase breakdown. Regression baseline. |
| **CAR (Construction Architecture Review)** | Post-implementation architecture-conformance certification. For Category B, includes mandatory Architecture Traceability Review (§10). |
| **Regression Report** | Test suite results. Regression counts. No architectural content. Not abbreviated "RR" (RR = Release Readiness Review, §10). |
| **FR (Final Review)** | Epic-closure gate (§10). Certifies objectives, frozen-architecture conformance, and Close/Blocked outcome. |
| **Epic Close** | Declaration that the epic is complete (FR Closed), all criteria are met, and the codebase is stable. |

---

### Traceability Matrix

The Traceability Matrix is a mandatory section within the Domain Contracts document. It must be complete before Architecture Freeze.

**Purpose:** Provide end-to-end traceability from every Master Plan requirement to the artifact that satisfies it, the component that consumes it, and the verification artifact that proves it was implemented.

**Format:** Each row links:

| Master Plan Requirement | Domain Contract / Field | Consuming Component | Verification Artifact |
|---|---|---|---|

**Rules:**
- Every Master Plan requirement for the epic must have at least one row.
- Every domain contract field exposed to the UI must appear in at least one row.
- A field with no consuming component is a dead field — it must be removed or justified.
- A requirement with no domain contract field is an unmet requirement — it blocks Architecture Freeze.
- The Traceability Matrix is not a substitute for the Component Inventory; both are required.

---

### Architecture Assumptions Register

The Architecture Assumptions Register is a mandatory artifact for every Category B epic. It is initialized during Architecture Discovery and must be fully resolved before Architecture Freeze.

**Purpose:** Make every assumption that underpins the architecture explicit and verifiable. An assumption that is never written down is a risk that is never mitigated.

**Format:** Each entry includes:

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|

**Status values:** `UNVERIFIED` (initial) → `VERIFIED` (confirmed by a planning document) → `INVALIDATED` (assumption is false; requires architectural response).

**Rules:**
- Every assumption identified during Architecture Discovery must be registered.
- No assumption may remain `UNVERIFIED` at Architecture Freeze. Every unverified assumption is a blocking issue.
- An `INVALIDATED` assumption requires returning to the Architecture Discovery / ADR phase before proceeding.
- The register is maintained in the Architecture Discovery document (`EPIC-NN-*.md`) as a dedicated section.

---

### Component Inventory

For every UI-bearing epic, the Architecture Discovery document must contain a dedicated **Component Inventory** section.

**Purpose:** Enumerate every UI component and specify its data contract before domain contracts are authored. This prevents domain contracts from being written without a clear consumer.

**For every UI component specify:**

| Field | Required |
|---|---|
| Component name | Yes |
| Responsibility | Yes |
| Owner | Yes |
| Input data | Yes |
| Output | Yes |
| Dependencies | Yes |
| Read-only / write capability | Yes |
| Domain artifact fields consumed | Yes |

A component that consumes a field not present in the domain artifact is a gap — it blocks Architecture Freeze.

---

### Definition of Done — Architecture Documents

Each planning document has mandatory completion criteria. A document that does not satisfy its DoD is not complete and may not be referenced as a basis for the next step.

#### §8.1 Architecture Discovery

- Current state vs. target state analysis is complete.
- All affected subsystems are identified.
- All confirmed decisions are listed with their governing ADR.
- All missing decisions are listed as open items.
- All risks are identified and classified.
- Component Inventory section is complete (for UI-bearing epics).
- Architecture Assumptions Register is populated (all assumptions are `UNVERIFIED` or `VERIFIED`; none are missing).
- No code is produced or modified.

#### §8.2 Domain Contracts

- Every new or changed artifact has a complete field specification (types, defaults, constraints, validators).
- Every artifact has a declared sole writer, declared readers, and a declared lifecycle.
- Traceability Matrix is complete: every Master Plan requirement is linked to at least one domain field, one consuming component, and one verification artifact.
- No field is untraced (dead field).
- No requirement is unmet (missing field).
- Does not contain alternatives evaluation (that belongs in ADRs).

#### §8.3 Data Model Specification

- All open modelling questions from Domain Contracts are resolved.
- Complete field tables are frozen for all affected artifacts.
- Replay completeness is verified (every UI panel has a source field).
- Extensibility for next epics is evaluated.
- All Architecture Assumptions are `VERIFIED` or `INVALIDATED`; none remain `UNVERIFIED`.
- An `INVALIDATED` assumption has a recorded architectural response.

#### §8.4 Architecture Review / ADR (conditional)

- Applies only when a genuine unresolved architectural decision remains after Domain Contracts and Data Model.
- Existing ADRs have been evaluated for applicability before a new ADR is proposed.
- Each new ADR evaluates at least two alternatives.
- Each new ADR records rationale and migration impact.
- No ADR is created proactively or speculatively.
- If no unresolved decision exists, this step is skipped and that decision is recorded in the Architecture Freeze document.

#### §8.5 Architecture Freeze

- All Architecture Exit Criteria (§8.7) are satisfied.
- The freeze document explicitly records whether any new ADR was required and, if not, why it was skipped.
- All Architecture Assumptions are `VERIFIED`.
- The Traceability Matrix is complete and referenced.
- The Component Inventory is complete and referenced.
- No open issues remain in any planning document.

#### §8.6 Implementation Plan

- Commit boundary table is complete.
- Implementation Dependency Validation (§2) has been applied to every commit boundary.
- Every commit is independently implementable and has an executable test gate.
- No circular implementation dependencies exist.
- Regression baseline is declared.
- Phase breakdown matches the Architecture Freeze scope.

---

### §8.7 Architecture Exit Criteria

Implementation Plan acceptance and Implementation may begin only if **ALL** of the following are true. This list is the mandatory gate between planning and implementation. It is evaluated as part of the Architecture Freeze.

- [ ] Architecture Discovery is complete (§8.1 DoD satisfied).
- [ ] Component Inventory is complete (for UI-bearing epics).
- [ ] Traceability Matrix is complete (every Master Plan requirement traced to a field, a component, and a verification artifact).
- [ ] Domain Contracts are frozen (§8.2 DoD satisfied).
- [ ] Data Model is frozen (§8.3 DoD satisfied).
- [ ] All Architecture Assumptions have status `VERIFIED`.
- [ ] No `BLOCKER` findings remain open in any planning document.
- [ ] All ADR decisions are complete and accepted (where an ADR was required).
- [ ] Architecture Freeze is declared (§8.5 DoD satisfied).
- [ ] Implementation Plan is accepted (§8.6 DoD satisfied; Implementation Dependency Validation passed).

A single unchecked item blocks the start of implementation. There are no exceptions.

---

### Stopping Rule

If, during implementation, an unresolved architectural question emerges — a decision that was not covered by the ADR, Domain Contracts, or Data Model documents — the following process is mandatory:

1. **Stop implementation immediately.** Do not make the architectural decision in code. Do not proceed with an assumption.
2. **Classify the issue.** Determine whether it is a sequencing issue (commit ordering only) or an architectural issue (affects contracts, ownership, data model, or behaviour).
   - If it is a **sequencing issue only**, apply the Plan Correction Rule (§2): update the Implementation Plan, perform a Mini Architecture Freeze, and resume implementation.
   - If it is an **architectural issue**, continue with steps 3–6 below.
3. **Return to the Architecture Review / ADR phase.** Document the question, evaluate alternatives, and freeze a decision in a new or amended ADR.
4. **Update the affected planning documents** (Domain Contracts or Data Model Specification) if the decision changes any specified field, type, invariant, or ownership rule.
5. **Perform a Freeze Integrity Check** (§10) on every modified frozen document before resuming implementation.
6. **Declare a new Architecture Freeze** for the affected scope before resuming.
7. **Resume implementation** only after the decision is frozen, the planning documents are updated, and the Freeze Integrity Check passes.

**Conversation continuity under the Stopping Rule.** Apply Conversation Boundary Optimization (§2): sequencing-only corrections (Plan Correction Rule / Mini Architecture Freeze) resume in the same conversation whenever the interrupted work remains a tightly coupled commit sequence. Architectural-issue paths that complete a natural boundary (Architecture Freeze, phase end, or equivalent) may start a new conversation; do not restart mid-sequence solely because implementation paused.

**Architectural decisions must never be made while coding.** A decision made in code is a decision that bypasses all review, rationale recording, and traceability. It is a process violation regardless of whether the decision is technically correct.

## 9. Documentation Strategy

### When to Update the Master Plan

Update `V13-PRODUCT-MASTER-PLAN.md` when: an epic's scope changes (narrowing or expanding); a dependency is discovered that was not captured at planning time; a deferred feature is moved into or out of scope; or a risk materialises and the mitigation strategy changes. Every amendment requires a recorded rationale at the bottom of the affected section.

### When to Write an ADR

Follow the criteria in the Enterprise Engineering Playbook §E. In V1.3 specifically, the following always require an ADR:

- Any decision about the `LongitudinalProfile` ownership model, storage schema, or update trigger.
- Any modification to a frozen V1.2 contract.
- Any exception to a constitutional principle (P-01 through P-05).
- The scoring pipeline migration strategy (how `InterviewEvaluation` is disabled and `Report` is activated).
- The `replay_node` reconstruction completeness contract.

### When to Update the Architecture Constitution

The Constitution (`ARC-01`) is amended only when V1.3 introduces a genuinely new invariant or proves an existing principle requires refinement. Amendments are proposed via ADR, reviewed explicitly, and recorded in the Constitution with a version note. The Constitution is not updated to describe V1.3 features — it describes principles that will remain valid beyond V1.3.

### When to Update the Architecture Guide

Update `ARCHITECTURE-GUIDE.md` at every epic close where the shipped architecture differs from what was previously documented. The guide reflects the current state of the system. Documentation-code divergence is a P2 finding in the CAR.

### When to Update the INDEX

Update `INDEX.md` whenever: a new frozen component is shipped; a new ADR is accepted; a component is deleted; or a Technical Debt Register item is opened or closed.

### Documentation Is Not Optional

Documentation updates are part of the Epic Close checklist (§3, Steps 11–13). An epic whose implementation is complete but whose documentation has not been updated is not done.

### Documentation Certification — Living Status vs Frozen Planning Bodies

Documentation Certification updates **living status artifacts** only:

- Epic Overview (`EPIC-NN-OVERVIEW.md`) — workflow markers, certification outcomes, final Assumptions summary
- Implementation Plan **status header** and close-out workflow markers — phase/checkpoint/CAR/regression/documentation outcomes
- Playbook — only when a reusable process improvement is identified

Documentation Certification **must not rewrite** frozen planning bodies as if they were living status documents:

- Architecture Discovery
- Domain Contracts
- Data Model Specification
- Architecture Freeze

Those documents remain historical records of decisions at the time they were frozen. Discovery-era Assumption statuses may remain as historical evidence; the **authoritative final VERIFIED** set is the Data Model / Architecture Freeze register, summarized in the Epic Overview at Documentation Certification.

### Category B — Living Epic Overview

Every Category B epic shall maintain `docs/master-plan/epics/EPIC-NN-OVERVIEW.md` as the **living** status document for workflow markers through Architecture Checkpoints, CAR, Regression Certification, Documentation Certification, Final Review, and Epic Close. Architecture Discovery remains a separate frozen analysis artifact and is not the living status surface.

---

## 10. Review Gates

### When to Trigger an ADR

Trigger an ADR before beginning any implementation that involves a design decision not already governed by an accepted ADR. An ADR is required; it is not a best-practice recommendation. Implementation is blocked until the ADR is accepted. See §9 for V1.3-specific ADR triggers.

### When to Trigger a CAR (Construction Architecture Review)

Trigger a CAR at the close of every epic (mandatory). Additionally trigger a CAR when: a mid-epic audit finds a structural violation; a previously unknown dependency between two epics is discovered; or an implementation increment introduces a change to a frozen contract. The CAR is not a heavyweight ceremony — it is a focused structural review against the Architecture Constitution, the operative PATs, and the epic's stated scope. P0/P1 findings block the epic from closing.

#### Architecture Traceability Review (mandatory for Category B)

The Construction Architecture Review (CAR) is an **architecture-conformance certification**, not a code-quality review.

Every CAR shall include an end-to-end Architecture Traceability Review that verifies:

- every component defined by the frozen architecture exists in the implementation;
- no additional production components have been introduced outside the approved architecture;
- responsibilities remain consistent with the frozen architecture;
- ownership remains consistent;
- dependencies remain consistent;
- data sources remain consistent with the frozen Domain Contracts and Data Model;
- the implementation conforms to Architecture Discovery, Domain Contracts, Data Model, Architecture Freeze, and Implementation Plan.

Architecture Traceability is a mandatory completion criterion for every Category B epic. A CAR without a completed Architecture Traceability Review cannot authorize advance to Final Review.

### When to Trigger an FR (Final Review)

Trigger the Final Review after the last implementation phase of an Epic is complete and all CAR P0/P1 findings are resolved, before starting the next Epic.

The FR is not an Architecture Review, a CAR, or a Release Readiness Review. It is a dedicated Epic-closure gate. It certifies:

- All Epic objectives have been achieved as defined in the Master Plan and the Epic Overview document.
- All frozen planning documents (ADRs, Domain Contracts, Data Model Specification, Architecture Freeze) have been fully implemented — no partial implementations, no deferred decisions.
- No temporary bridges remain in the codebase unless explicitly planned in the Epic planning documents with a named deletion target and a target Epic.
- No temporary compatibility layers remain unless explicitly planned with the same conditions.
- The runtime architecture matches the frozen architecture documented at Epic planning time.
- All ownership rules for `InterviewState` fields introduced or modified by this Epic are satisfied.
- Implementation debt introduced or discovered during the Epic is classified and registered in the Technical Debt Register with target milestones.
- Lessons learned are captured (either in the Playbook revision note or in a dedicated session note).

The FR produces a binary outcome: **Closed** or **Blocked**. A Blocked FR must enumerate the blocking findings. The Epic does not advance to Closed status until the FR passes.

**FR vs other review types:**

| Review | Closes | Purpose |
|---|---|---|
| CAR | An implementation | Architecture-conformance certification (incl. Architecture Traceability for Category B) |
| FR | An Epic | Epic objectives achieved; runtime matches frozen architecture |
| RR (Release Readiness Review) | A Release Candidate | All Epics done; go-live criteria satisfied |
| Go-Live Review | The product release | Production deployment validated |

### When to Trigger an RR (Release Readiness Review)

Trigger the Release Readiness Review when all Epics are closed (FR passed for each) and all go-live checklist items in the Master Plan (§5) are believed to be satisfied. The RR is the final gate before the V1.3 release tag. It verifies all Success Metrics (Master Plan §9), runs the full regression suite, confirms zero open P0/P1 findings, and validates all production deployment criteria. The RR is not a review of code — it is a review of evidence: test results, deployment validation records, performance baseline reports, and architecture audit reports.

### Architecture Checkpoint

Architecture Checkpoints are mandatory after every completed macro phase. An Architecture Checkpoint is a review-only activity: it performs no implementation and produces no code changes.

**Trigger:** Every completed macro phase — automatically, without exception. The official Architecture Checkpoint is executed ONLY after the corresponding Macro Phase is complete, at the gate defined by the Implementation Plan.

**Informal reviews:** Intermediate architectural reviews may be performed within a Macro Phase when useful (for example, after an early sub-phase). Such reviews are informal. They do not authorize the next Macro Phase and shall not replace the official Architecture Checkpoint.

**Purpose:** Verify that the implementation of the completed macro phase is architecturally compliant before the next macro phase is authorized to begin.

**Each Architecture Checkpoint must:**

- Review the completed macro phase against the frozen architecture documents (ADR, Domain Contracts, Data Model, Architecture Freeze).
- Produce findings classified as PASS, WARNING, or BLOCKER for each review dimension.
- Explicitly authorize (or block) the next macro phase.

**Architecture Checkpoint passes when all of the following are true:**

- All implementation in the completed phase matches the frozen architecture.
- No P0/P1 architectural violations are open.
- The regression suite is green at the phase boundary.
- No temporary bridge, compatibility layer, or partial migration remains unless it has an explicit named deletion target in the Implementation Plan.

**Outcome:** The Architecture Checkpoint produces a binary authorization: **AUTHORIZED** (next macro phase may begin) or **BLOCKED** (blocking findings must be resolved first). A BLOCKED checkpoint prevents the next macro phase from starting; it does not block P2/P3 finding resolution within the same phase.

**Scope:** Architecture Checkpoints cover architecture only. They do not review code style, test coverage, or documentation completeness — those are covered by the CAR and FR.

### Mini Architecture Freeze

Triggered in either of the following cases:

1. **Additive ADR during implementation** — an ADR is discovered and accepted that was not part of the original epic planning set but is required to resolve a lifecycle, ownership, or boundary gap identified during Domain Discovery or implementation.
2. **Sequencing correction** — the Plan Correction Rule (§2) applies: commit ordering in the Implementation Plan must change, and the target architecture, ADRs, ownership, contracts, data model, and target behaviour remain unchanged.

**Purpose (ADR trigger):** Verify that the new ADR introduces no contradiction, no ownership conflict, no replay conflict, no builder conflict, and no freeze violation before implementation resumes. This review is mandatory. It does not repeat the full Epic Architecture Freeze workflow.

**Purpose (sequencing trigger):** Verify the Plan Correction Rule conditions (§2) before the Implementation Plan update is accepted. Implementation may resume immediately after the Mini Architecture Freeze passes.

**Mini Architecture Freeze passes when all of the following are true (ADR trigger):**

- The new ADR does not contradict any decision in any previously accepted ADR or frozen planning document.
- No artifact introduced by the ADR has a second declared producer, writer, or builder elsewhere in the frozen set.
- No replay path introduced or affected by the ADR violates the Replay Boundary (ARC-01 §3).
- No builder introduced by the ADR contains computation logic (P-05).
- The new ADR is internally consistent with the Architecture Constitution (P-01 through P-08).
- The document hierarchy remains internally consistent after the ADR is accepted.

**Mini Architecture Freeze passes when all Plan Correction Rule conditions (§2) are satisfied (sequencing trigger).**

**Gate:** Implementation of any component governed by a new ADR cannot begin until the Mini Architecture Freeze passes. Sequencing corrections may resume only after the Mini Architecture Freeze passes. The outcome is recorded in the session commit message.

**Scope:** For an ADR trigger, Mini Architecture Freeze covers the new ADR only. For a sequencing trigger, it covers the Implementation Plan correction only. It does not re-verify the full epic planning set. It does not replace the Epic Architecture Freeze or the Freeze Integrity Check.

---

### Freeze Integrity Check

Whenever a frozen planning document is modified — including an ADR, Architecture Freeze report, Architecture Constitution, Implementation Plan, Domain Contracts, Data Model Specification, or Architecture Guide — a Freeze Integrity Check is mandatory before implementation resumes.

**A Freeze Integrity Check confirms all of the following:**

- The target architecture is unchanged; only sequencing, process rules, or editorial corrections are modified.
- The document hierarchy remains internally consistent; no contradiction is introduced between the modified document and any document it references or that references it.
- No new architectural decision is embedded in the modification (decisions require a new or amended ADR).
- The scope of the modification is limited to the stated intent; no unrelated changes are introduced.

The Freeze Integrity Check is performed by the author of the modification immediately after editing, before any implementation work continues. If the check reveals a contradiction or an undeclared decision, the modification is revised until the check passes. Verification is recorded in the session commit message (e.g., "Freeze Integrity Check passed — only sequencing revised, architecture unchanged").

### Review Gate Summary

| Gate | Trigger | Closes | Blocks |
|---|---|---|---|
| Implementation Dependency Validation | Implementation Plan commit boundary table drafted | — | Plan acceptance |
| ADR | New design decision before implementation | — | Implementation start |
| Mini Architecture Freeze | Additive ADR accepted during implementation; OR sequencing correction (Plan Correction Rule §2) | — | Resumption of implementation for new ADR scope; OR plan update |
| Freeze Integrity Check | Any frozen document modified | — | Resumption of implementation |
| Architecture Checkpoint | Official gate after every completed macro phase (per Implementation Plan); informal mid-phase reviews do not replace it | Macro phase | Next macro phase start |
| CAR | Epic implementation complete; Architecture Traceability required for Category B | Implementation | Epic advance / FR |
| CAR (mid-epic) | Structural violation discovered during implementation | — | Continuation of affected increment |
| FR (Final Review) | All Epic phases complete; all CAR P0/P1 resolved; Documentation Update complete | Epic | Next Epic start |
| RR (Release Readiness Review) | All Epics closed (FR passed); go-live checklist complete | Release Candidate | V1.3 release tag |
| Go-Live Review | RR passed; production deployment validated | Product Release | Production tag |

---

## 11. Cursor Usage Guidelines

### Purpose of Cursor in V1.3

Cursor accelerates implementation and documentation work. It does not replace architectural judgment, ADR authoring decisions, or epic planning. Every Cursor output is reviewed before it is accepted into the codebase or documentation.

### Cursor Chat Policy

Every Cursor chat session is scoped to a single macro phase. This policy implements Conversation Boundary Optimization (§2) for Cursor sessions: continue within the macro phase; reset at the macro-phase boundary.

- **Start a new Cursor chat** at the beginning of every macro phase.
- **Continue the same chat** throughout all sub-phases within that macro phase.
- **Start another new chat** only when the next macro phase begins.

The rationale: a single chat accumulating context across multiple macro phases degrades prompt quality and increases token cost without benefit. Each macro phase has a well-defined, independent scope — that scope maps exactly to one chat session. Do not restart mid-phase solely to shorten context when reconstruction cost would outweigh the savings (see Conversation Boundary Optimization §2).

### Implementation Prompt Structure

Every implementation prompt sent to Cursor shall contain all of the following elements, in order:

1. **Cursor Chat decision** — new or continue, with rationale (new macro phase → new chat; same macro phase → continue).
2. **SAVE-TOKEN** — mandatory at the start of every prompt.
3. **Regression baseline** — current passing test count from the previous phase completion.
4. **Authoritative documents** — file paths to the frozen architecture documents governing this phase.
5. **Mission** — what this phase must accomplish, stated precisely.
6. **Allowed scope** — files and modules that may be created or modified.
7. **Forbidden scope** — files and modules that must not be touched.
8. **Validation requirements** — the specific gates that must pass before this phase is complete.
9. **Completion criteria** — the observable conditions that define phase completion.
10. **Architecture review requirements** — any architectural invariants that must be verified.
11. **Commit instructions** — atomic commit required; commit message format specified.
12. **Required output format** — what the response must contain (typically: modified files, test results, commit status).

Any prompt missing one or more of these elements is incomplete and must not be submitted until corrected.

### Regression Baseline Protocol

Every completed implementation phase updates the regression baseline:

- The baseline is the passing test count at the end of the completed phase.
- The next implementation prompt must reference that updated baseline, not the baseline from the start of the epic.
- No phase may begin with a stale or incorrect baseline in the prompt.

### For Implementation Work

Provide Cursor with: the relevant frozen contracts (file paths, not pasted content); the accepted ADR(s) that govern the component; the specific scope of the increment (what to implement — and explicitly what not to touch); and any architectural constraints that are not obvious from the contracts alone. Cursor implements against a defined architecture. It does not discover the architecture by implementing.

### For Document Editing

When asking Cursor to edit planning or architectural documents, provide the specific change required with its rationale. Do not ask for open-ended document improvements. The change must be scoped: what section, what wording, and why. The document structure and style must be preserved.

### Output Conventions

- **Compact output only.** Modified files, acceptance checklist, open issues. No reasoning walk-through, no intermediate analysis, no generated code in summaries.
- **No verbose explanations.** If a change requires explanation, the explanation belongs in the ADR or commit message, not in the Cursor response.
- **No document previews.** Do not include the generated Markdown content in the response. Confirm the file was written; do not echo its contents.
- **No implementation notes in summaries.** Summaries reference what was done, not how.

### Save-Token Protocol

Begin every session with a save-token before making any changes. This ensures the project state can be recovered if a session is interrupted. The save-token is mandatory at the start of every task, not optional.

### What Cursor Must Never Do

- Modify production code or tests during a planning or documentation task.
- Generate TODO lists or implementation notes in planning documents.
- Introduce new architectural scope not defined in the Master Plan.
- Write ADRs without a human-defined problem statement and decision rationale.
- Produce verbose reasoning, chain-of-thought analysis, or intermediate calculation dumps in any response.
- Show generated Markdown content in responses when the instruction is to write a file.

---

---

*This playbook is the operational handbook for V1.3. It is a living document. Amendments are made when process lessons are learned, not when preferences change. Every amendment requires a recorded rationale.*

*Revision 2026-07-05: Added "Zero Known Failing Tests" engineering principle (§2), "Zero Known Failing Tests — Enforcement" testing rule (§7), "Freeze Integrity Check" review gate (§10), bridge-phase mandate in Category B workflow (§8), and Freeze Integrity Check in the Stopping Rule (§8). Derived from EPIC-01 Phase 6 implementation experience.*

*Revision 2026-07-06: Added Final Review (FR) as a mandatory review type (§10). FR closes an Epic; RR (Release Readiness Review) closes a Release Candidate; Go-Live Review closes the product release. FR integrated into Epic Workflow (§3), Definition of Done (§5), and Review Gate Summary (§10). Derived from EPIC-01 Final Review experience — FR methodology proven valuable and made permanent.*

*Revision 2026-07-14: Added Mini Architecture Freeze review gate (§10). Triggered when an additive ADR is accepted during implementation. Verifies no contradiction, ownership conflict, replay conflict, builder conflict, or freeze violation before implementation resumes. Derived from EPIC-02 Domain Discovery Review experience (ADR-035 lifecycle). Added to Review Gate Summary table.*

*Revision 2026-07-15: Added two engineering principles (§2): "Implementation Dependency Validation" — mandatory commit-boundary self-containment review performed during Implementation Plan authoring, before plan acceptance; and "Plan Correction Rule" — sequencing-only corrections to the Implementation Plan require only a Mini Architecture Freeze, not a full Architecture Freeze. Mini Architecture Freeze (§10) updated to cover both ADR-triggered and sequencing-correction triggers. Review Gate Summary (§10) updated with Implementation Dependency Validation gate. Stopping Rule (§8) updated with issue-classification step: sequencing issues apply Plan Correction Rule; architectural issues follow the full ADR path. Epic Workflow Step 1 (§3) updated to mandate Implementation Dependency Validation when the commit boundary table is drafted. Derived from EPIC-02 P3/C2 sequencing correction experience.*

*Revision 2026-07-15 (EPIC-03 close-out): Seven workflow improvements formalised from EPIC-03 Replay Engine implementation experience: (1) Macro Phase Lifecycle (§3) — added mandatory Architecture Freeze → Implementation Plan → Macro Phase → Architecture Checkpoint → Next Macro Phase lifecycle with diagram; (2) Cursor Chat Policy (§11) — formalised one-chat-per-macro-phase rule; new chat at every macro phase start, same chat for all sub-phases; (3) Architecture Checkpoint (§10) — added as mandatory review gate after every completed macro phase; produces PASS/WARNING/BLOCKER findings; explicitly authorises the next macro phase; added to Review Gate Summary; (4) Implementation Prompt Structure (§11) — defined 12 mandatory elements every Cursor implementation prompt must contain; (5) Regression Baseline Protocol (§11) — formalised that every completed phase updates the baseline and the next prompt must use the updated baseline; (6) Atomic Phase Commits (§6) — formalised that every sub-phase ends with one atomic commit; fallback git commands required when automated commit is unavailable; (7) Architecture-First Discipline (§2) — formalised as an engineering principle: frozen architecture is non-negotiable, no drift, no opportunistic refactoring, strict phase isolation.*

*Revision 2026-07-15 (EPIC-04 initialisation): Five governance improvements formalised from EPIC-04 initialisation experience: (1) Category B workflow resequenced (§8) — Architecture Discovery precedes Domain Contracts; Domain Contracts and Data Model precede Architecture Review / ADR authoring; ADR authoring is conditional, not prescribed; Implementation Plan is now an explicit numbered step; (2) Traceability Matrix (§8) — mandatory section within Domain Contracts; links every Master Plan requirement to a domain field, a consuming component, and a verification artifact; must be complete before Architecture Freeze; (3) Architecture Assumptions Register (§8) — mandatory artifact for every Category B epic; populated during Architecture Discovery; all assumptions must be VERIFIED before Architecture Freeze; maintained in the Architecture Discovery document; (4) Component Inventory (§8) — mandatory section within the Architecture Discovery document for UI-bearing epics; specifies every UI component with full data contract before domain contracts are authored; (5) Definition of Done and Architecture Exit Criteria (§8) — per-document DoDs defined for Architecture Discovery, Domain Contracts, Data Model, Architecture Review / ADR, Architecture Freeze, and Implementation Plan; Architecture Exit Criteria checklist formalises the implementation gate; all criteria must be satisfied before implementation begins. Derived from EPIC-04 Replay UI Experience initialisation process.*

*Revision 2026-07-16 (EPIC-04 Architecture Checkpoint A): Clarified Architecture Checkpoint timing (§3 Macro Phase Lifecycle, §10 Architecture Checkpoint, Review Gate Summary). Official Architecture Checkpoints execute ONLY after completion of the corresponding Macro Phase as defined by the Implementation Plan. Intermediate reviews may be performed when useful but are informal and do not replace the official checkpoint. Derived from EPIC-04 Macro Phase A experience — an intermediate review after Phase 2 was useful but must not be treated as Architecture Checkpoint A.*

*Revision 2026-07-16 (EPIC-04 Documentation Certification): Formalised Architecture Traceability Review as a mandatory CAR completion criterion for Category B epics (§10 CAR; cross-referenced from Epic Workflow, Definition of Done, Review Gate Summary, and Category B workflow). CAR is defined as architecture-conformance certification, not a code-quality review. Derived from EPIC-04 CAR experience — end-to-end component/ownership/dependency/data-source traceability was essential to certify frozen-architecture conformance.*

*Revision 2026-07-16 (EPIC-05 Documentation Certification): Formalised Documentation Certification rule that living status belongs in Epic Overview + Implementation Plan status headers; frozen Architecture Discovery / Domain Contracts / Data Model / Architecture Freeze bodies are not rewritten for close-out markers. Category B workflow Step 1 now requires a living `EPIC-NN-OVERVIEW.md` distinct from frozen Architecture Discovery. Derived from EPIC-05 Documentation Certification — EPIC-05 initially used Discovery as the only overview surface, which conflated historical discovery status with living certification markers.*

*Revision 2026-07-16 (EPIC-06 Initialization refinement): Formalised **Known Inputs** as a mandatory Category B EPIC Initialization section (before Architecture Assumptions Register). Known Inputs list only already existing artifacts for Discovery to inspect — no decisions, analysis, or assumptions. Also formalised architecture-neutral Initialization: Initialization identifies the problem space and must not propose presentation mechanisms or other design alternatives. Derived from EPIC-V13-06 Initialization refinement.*

*Revision 2026-07-16 (EPIC-06 Conversation Boundary Optimization): Added engineering principle "Conversation Boundary Optimization" (§2) — prefer continuing within the same implementation milestone or tightly coupled commit sequence; prefer a new conversation only after a natural architectural boundary; always balance shorter-context token savings against reconstruction cost. Stopping Rule (§8) updated so sequencing-only resume stays in the same conversation, while completed architectural boundaries may open a new one. Derived from EPIC-06 long-running implementation experience.*

*Revision 2026-07-16 (Version 1.0 editorial consolidation): Stabilised the Playbook as Version 1.0. Editorial-only: resolved duplicate section number and restored logical order (§8 Epic Planning Workflow, §9 Documentation Strategy, §10 Review Gates, §11 Cursor Usage); aligned §3 step prose with the 13-step lifecycle diagram; fixed Architecture Exit Criteria numbering collision (§8.7 vs former Implementation Plan DoD §8.6); unified CAR naming (Construction Architecture Review); reserved RR for Release Readiness Review and renamed epic-level regression step accordingly; aligned Category A/B close-out with FR + Epic Close; clarified Mini Architecture Freeze dual triggers; cross-linked Cursor Chat Policy to Conversation Boundary Optimization; fixed typo and stale cross-references. No process semantics changed.*
