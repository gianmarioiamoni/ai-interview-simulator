# V1.3 Development Playbook

**Status:** ACTIVE — Operational Handbook  
**Date:** 2026-07-05  
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

A migration is not done until the legacy artifact is deleted from the codebase. Deprecated-but-not-deleted code is not a milestone milestone. It is a debt item. Every migration increment must have an explicit deletion target, and that target must be closed before the epic is marked done.

### Small Incremental Changes

Every change addresses one logical concern. Mixed commits — where a refactor, a feature, and a test fix are bundled together — obscure history, complicate review, and make bisection impossible. One logical change per commit. One concern per pull request.

### One Responsibility per Component

A component that does two things should be two components. This applies to nodes, services, pipelines, builders, and engines. File size approaching 200 lines during design is a signal to decompose before implementation, not after.

### Product Before Features

V1.3 is the production release. Completion and correctness of committed epics take priority over adding new scope. If a new idea surfaces during implementation, it is assessed against the Deferred Features list in the Master Plan. If it is not already there, it belongs there — not in V1.3.

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
4. Implementation
        ↓
5. Architectural Review (CAR)
        ↓
6. Regression
        ↓
7. Documentation Update
        ↓
8. Epic Close
```

### Step 1 — Epic Planning

Read the epic definition in the Master Plan. Confirm preconditions (prior epics, dependencies). Identify all artifacts the epic will produce, modify, or delete. Identify all `InterviewState` fields the epic touches and verify their declared ownership. Identify whether any new ADR or PAT is required before implementation can begin.

### Step 2 — Architecture Governance

If the epic introduces a new design decision, a new pattern, or a modification to a frozen contract, the governance step is mandatory before any code is written. This may include: drafting and accepting a new ADR; evaluating a proposed pattern through the standard PAT governance process; or proposing an amendment to the Architecture Constitution. No governance artifact is adopted without completing the normal review process. This step may be lightweight for straightforward epics and thorough for foundational ones (e.g., EPIC-V13-01, EPIC-V13-02).

### Step 3 — Contract Definition

Define all new domain contracts before writing implementation code. All contracts are `frozen=True` (or equivalent). All contracts use `extra=forbid`. No implementation begins on any component whose contract is not frozen.

### Step 4 — Implementation

Implement against frozen contracts and accepted ADRs. Each commit addresses one logical concern. No mixed refactors. No silent fallbacks. Every new `InterviewState` field must have a declared sole writer at the moment of addition. Every reconstruction path must explicitly enumerate every field it copies (Reconstruction Completeness). Dead code is deleted, not deprecated.

### Step 5 — Architectural Review (CAR)

After implementation is complete, perform a Construction Architecture Review. Verify: layering compliance (no domain-to-infrastructure imports); single ownership (no new dual-path violations); constitutional compliance (no computation in projection paths); PAT compliance (all operative patterns followed); and that all `InterviewState` fields have declared ownership. P0/P1 findings block the epic from advancing. P2/P3 findings are registered in the Technical Debt Register.

### Step 6 — Regression

Run the full test suite. All V1.2 acceptance criteria must continue to pass. All new epic acceptance criteria must pass. Zero failures permitted to close the epic.

### Step 7 — Documentation Update

Update all affected documents: the Master Plan (if epic scope changed), the Architecture Guide, relevant ADRs (status update), the INDEX (new frozen components, new ADRs), and the Technical Debt Register (new findings or closed items). Documentation is not optional and is not deferred.

### Step 8 — Epic Close

The epic is closed when: all acceptance criteria are satisfied; zero P0/P1 architectural findings remain open; all documentation is updated; all legacy artifacts targeted for deletion are deleted; and the regression suite passes in full.

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
- The full regression suite passes with zero failures.
- All new ADRs are in Accepted status.
- All affected documentation has been updated (Architecture Guide, INDEX, ADRs, Technical Debt Register).
- The Technical Debt Register reflects all P2/P3 findings from this epic with target milestones.
- No deprecated-but-not-deleted artifacts from this epic remain in the codebase.

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

### Regression Baseline

The V1.2 regression suite is the baseline. It must pass in full at every epic boundary. Any regression introduced by a V1.3 increment must be fixed before the increment is merged — regressions are never deferred to the end of an epic.

### Test Count Target

Total passing tests ≥ 2,500 at V1.3 release gate (Master Plan §5).

---

## 8. Documentation Strategy

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

Documentation updates are part of the Epic Close checklist (§3, Step 8). An epic whose implementation is complete but whose documentation has not been updated is not done.

---

## 9. Review Gates

### When to Trigger an ADR

Trigger an ADR before beginning any implementation that involves a design decision not already governed by an accepted ADR. An ADR is required; it is not a best-practice recommendation. Implementation is blocked until the ADR is accepted. See §8 for V1.3-specific ADR triggers.

### When to Trigger a CAR (Construction Architecture Review)

Trigger a CAR at the close of every epic (mandatory). Additionally trigger a CAR when: a mid-epic audit finds a structural violation; a previously unknown dependency between two epics is discovered; or an implementation increment introduces a change to a frozen contract. The CAR is not a heavyweight ceremony — it is a focused structural review against the Architecture Constitution, the operative PATs, and the epic's stated scope. P0/P1 findings block the epic from closing.

### When to Trigger an RR (Release Readiness Review)

Trigger the Release Readiness Review when all epics are closed and all go-live checklist items in the Master Plan (§5) are believed to be satisfied. The RR is the final gate before the V1.3 release tag. It verifies all Success Metrics (Master Plan §9), runs the full regression suite, confirms zero open P0/P1 findings, and validates all production deployment criteria. The RR is not a review of code — it is a review of evidence: test results, deployment validation records, performance baseline reports, and architecture audit reports.

### Review Gate Summary

| Gate | Trigger | Blocks |
|---|---|---|
| ADR | New design decision before implementation | Implementation start |
| CAR | Epic implementation complete | Epic close |
| CAR (mid-epic) | Structural violation discovered during implementation | Continuation of affected increment |
| RR | All epics closed; go-live checklist believed complete | V1.3 release tag |

---

## 10. Cursor Usage Guidelines

### Purpose of Cursor in V1.3

Cursor accelerates implementation and documentation work. It does not replace architectural judgment, ADR authoring decisions, or epic planning. Every Cursor output is reviewed before it is accepted into the codebase or documentation.

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

## 8. Epic Planning Workflow

The EPIC-01 planning process established the standard workflow for V1.3 epics. This section formalises that workflow and makes it mandatory for all subsequent epics.

Two categories of epic exist. The category determines the mandatory pre-implementation workflow. Misclassifying an epic as Category A when it belongs in Category B is a process violation.

---

### Category A — Standard Epics

Applies to epics that do not introduce new domain contracts, new persistent artifacts, new builders, new immutable models, or new serialization contracts.

**Mandatory workflow:**

1. **Master Plan** — Epic scope, purpose, dependencies, and success criteria defined in the Master Plan or in a dedicated epic planning document under `docs/master-plan/epics/`.
2. **Architecture Review** — An explicit review pass that identifies affected subsystems, confirms no missing decisions, and declares the epic ready for ADR.
3. **ADR** — One or more ADRs frozen in `docs/decisions/` that cover every architectural decision the epic requires.
4. **Implementation** — Incremental implementation against frozen decisions. No architectural choices during coding.
5. **CAR (Change Acceptance Report)** — Confirms the implementation satisfies the ADR decisions and the epic's success criteria.
6. **RR (Regression Report)** — Confirms the full test suite passes and no regressions were introduced.
7. **Epic Freeze** — Epic is declared complete. No further changes to the epic scope.

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

1. **Master Plan** — Epic scope, purpose, dependencies, non-goals, and success criteria.
2. **Architecture Review** — Full analysis of current state, target state, all affected subsystems, open decisions, and structural gaps. Produces a structured report of confirmed decisions, missing decisions, and risks. Does not produce code.
3. **ADR** — One or more ADRs in `docs/decisions/` that freeze every architectural decision identified in the Architecture Review. Implementation cannot begin until all blocking ADR decisions are frozen.
4. **Domain Contracts** — A dedicated domain contract specification document under `docs/master-plan/epics/`. Specifies the complete field set, types, validation invariants, ownership, lifecycle, and relationships of every new artifact. Precise enough that implementation is mechanical.
5. **Data Model Specification** — A dedicated data model document. Resolves all open modelling decisions left by the Domain Contracts document. Freezes the complete field tables for all affected artifacts. Verifies replay completeness. Evaluates future extensibility.
6. **Architecture Freeze** — A formal gate (described below). Implementation cannot begin before Architecture Freeze passes.
7. **Implementation** — Incremental implementation against frozen contracts. No architectural choices during coding. If an unresolved question emerges, apply the Stopping Rule (below).
8. **CAR (Change Acceptance Report)** — Confirms the implementation satisfies all ADR decisions, domain contracts, and data model specifications.
9. **RR (Regression Report)** — Confirms the full test suite passes with no regressions.
10. **Epic Freeze** — Epic is declared complete. No further scope additions.

---

### Architecture Freeze

Architecture Freeze is a mandatory gate between the planning phase (steps 1–5 of Category B) and the implementation phase (step 7). It is not a document — it is a verification checkpoint.

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

### Document Responsibilities

Each planning document has a unique responsibility. Documents must not duplicate each other's content. If the same information appears in two documents, one of them is wrong.

| Document | Unique Responsibility |
|----------|-----------------------|
| **Master Plan** | Epic scope, purpose, product goals, dependencies, non-goals, success criteria. Does not specify field-level data. |
| **Architecture Review** | Analysis of current state vs target state. Identifies affected subsystems, confirmed decisions, missing decisions, and risks. Produces findings only — no decisions. |
| **ADR** | Freezes decisions. Evaluates alternatives. Records rationale. Specifies migration impact. Each decision is owned by exactly one ADR. |
| **Domain Contracts** | Field-level specification of every new or changed artifact: types, defaults, constraints, validators, ownership, lifecycle. Does not evaluate alternatives (that is the ADR's job). |
| **Data Model Specification** | Resolves all open modelling questions left by the Domain Contracts document. Freezes complete field tables. Verifies replay completeness. Evaluates extensibility. Does not re-specify invariants (that is the Domain Contracts' job). |
| **CAR (Change Acceptance Report)** | Post-implementation verification that the implementation matches the frozen decisions. Records any deviations and their justification. |
| **RR (Regression Report)** | Test suite results. Regression counts. No architectural content. |
| **Epic Freeze** | Declaration that the epic is complete, all criteria are met, and the codebase is stable. |

---

### Stopping Rule

If, during implementation, an unresolved architectural question emerges — a decision that was not covered by the ADR, Domain Contracts, or Data Model documents — the following process is mandatory:

1. **Stop implementation immediately.** Do not make the architectural decision in code. Do not proceed with an assumption.
2. **Return to the Architecture Review / ADR phase.** Document the question, evaluate alternatives, and freeze a decision in a new or amended ADR.
3. **Update the affected planning documents** (Domain Contracts or Data Model Specification) if the decision changes any specified field, type, invariant, or ownership rule.
4. **Declare a new Architecture Freeze** for the affected scope before resuming.
5. **Resume implementation** only after the decision is frozen and the planning documents are updated.

**Architectural decisions must never be made while coding.** A decision made in code is a decision that bypasses all review, rationale recording, and traceability. It is a process violation regardless of whether the decision is technically correct.

---

*This playbook is the operational handbook for V1.3. It is a living document. Amendments are made when process lessons are learned, not when preferences change. Every amendment requires a recorded rationale.*
