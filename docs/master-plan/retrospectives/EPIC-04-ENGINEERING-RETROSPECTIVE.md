# EPIC-04 Engineering Retrospective

**Status:** COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-04  
**Epic Title:** Replay UI Experience  
**Playbook Category:** Category B — Major Architectural Epic  
**Epic Status at Retrospective:** CLOSED  
**Authority:** Post-close engineering retrospective. Does not amend historical EPIC planning or certification records.

---

## 1. Executive Summary

### Purpose

Capture reusable engineering lessons from EPIC-V13-04 so future Category B epics can apply proven workflow discipline without modifying closed EPIC documentation.

### Outcome

EPIC-V13-04 closed successfully. The candidate-facing Replay UI shipped as a read-only, LLM-free presentation layer consuming a frozen projection artifact. Category B planning, macro-phase implementation, Architecture Checkpoints, CAR (with Architecture Traceability), Final Regression Certification, Documentation Certification, and Final Review all completed with APPROVED / CERTIFIED outcomes.

### Overall Engineering Assessment

EPIC-04 demonstrated a mature Category B lifecycle: architecture frozen before code; implementation isolated by phase; review gates treated as conformance certification rather than style review; unrelated technical debt isolated from feature work. Workflow gaps discovered mid-epic (checkpoint timing; CAR traceability definition) were formalized into the Development Playbook during the epic and are now stable enough to reuse without further process invention before the next epic.

---

## 2. What Worked Well

### Architecture Freeze discipline

Implementation began only after Architecture Freeze APPROVED. Frozen constraints (no domain mutation, no LLM on render path, additive UI-state extension only) held through close-out. No Freeze Integrity Check was required for architectural drift.

### Domain-first Category B workflow

Architecture Discovery → Domain Contracts → Data Model → conditional ADR → Architecture Freeze → Implementation Plan produced implementable contracts before coding. Component Inventory and Traceability Matrix made consumer requirements explicit before field contracts were written.

### Conditional ADR policy

No new ADR was authored. Existing ADRs covered every architectural decision. Skipping proactive ADR authoring reduced documentation noise without weakening governance.

### Architecture Assumptions Register

Eight assumptions were registered early, driven to VERIFIED (two remaining CONDITIONALLY VERIFIED until Phase 6 enforcement). The register prevented silent “we assume this works” gaps at Freeze.

### Architecture Checkpoints

Mandatory checkpoints after Macro Phase A and Macro Phase B blocked premature advance and forced freeze conformance before the next macro phase / CAR.

### CAR as architecture-conformance certification

CAR verified component presence/absence, ownership, dependencies, and data-source fidelity against frozen documents — not code style. Architecture Traceability made “frozen vs shipped” auditable.

### Regression Certification

Full-suite green was required at every phase boundary and again at close-out. Baseline discipline (declare → update → certify) kept regressions visible.

### Documentation Certification

Close-out documentation was certified before Final Review, aligning status markers, assumption status, and gate outcomes without rewriting frozen planning history.

### Architecture Traceability

End-to-end mapping from frozen components to implemented artifacts confirmed C-01…C-10 present and excluded scope absent. Missing or extra production architecture components would have blocked FR.

### Technical Debt isolation

Pre-existing lint debt was cleaned in a dedicated chore commit outside Replay UI feature commits. Feature history remained bisectable; debt work did not masquerade as epic scope.

### Strict Allowed / Forbidden scope

Per-phase scope tables kept domain contracts, graph nodes, and projection writers untouched. Phase isolation prevented opportunistic refactors during feature delivery.

### Zero Known Failing Tests

Every phase and close-out gate left the suite green. No “known failing” milestones were accepted.

---

## 3. Engineering Challenges

Genuine challenges encountered during EPIC-04 (not invented):

1. **Official vs informal Architecture Checkpoint confusion**  
   An intermediate review after Phase 2 was useful but was initially treated as Architecture Checkpoint A, while the Implementation Plan defined Checkpoint A after Phase 3. This required a second, official checkpoint and a Playbook clarification.

2. **Temporary routing bridges across phase boundaries**  
   Phase 2 introduced temporary routing tokens until Phase 4 error/view consumers existed. Checkpoint A correctly accepted this as a WARNING with a named deletion target; the tokens were removed in Phase 4. Bridge lifetime management remains a recurring Category B tension.

3. **CONDITIONALLY VERIFIED assumptions at Freeze**  
   LLM-free enforcement and performance gates were architecturally sound at Freeze but not yet test-enforced. Full VERIFIED status depended on a dedicated late verification phase (Phase 6). Without that phase, Freeze would have over-claimed.

4. **Transitive integration surface under-specification risk**  
   Layout/bindings/orchestrator files were in Forbidden scope until Phase 5. The lesson surfaced that Allowed/Forbidden tables must enumerate transitive integration files explicitly, or phase agents can miss required wiring surfaces.

5. **Commit-boundary granularity vs delivery practicality**  
   The Implementation Plan specified six atomic panel commits for Phase 4; delivery consolidated panel renderers into one phase commit while still leaving the suite green. Granular commit tables remain valuable for dependency validation, but over-fragmentation can be impractical when panels share fixtures and invariants.

---

## 4. Workflow Improvements Adopted

These improvements entered the Development Playbook during EPIC-04 and remain operative.

### 4.1 Category B planning resequence + governance artifacts (EPIC-04 initialisation)

**Why it emerged:** UI-bearing Category B work needed consumer inventory and assumption tracking before contracts and ADRs.

**Problem solved:** Prevented writing domain contracts without known consumers; prevented proactive ADRs; made Freeze exit criteria objective.

**Reusable because:** Applies to any Category B epic introducing contracts, persistent artifacts, builders, UI surfaces, or serialization shape.

**Playbook locations:** §8 Category B workflow; Traceability Matrix; Architecture Assumptions Register; Component Inventory; per-document DoD; Architecture Exit Criteria.

### 4.2 Official Architecture Checkpoint timing (Macro Phase A experience)

**Why it emerged:** Intermediate Phase 2 review was mistaken for Checkpoint A.

**Problem solved:** Distinguishes useful informal reviews from the official macro-phase gate that alone authorizes the next macro phase.

**Reusable because:** Any multi-macro-phase Category B epic benefits from the same timing rule.

**Playbook locations:** §3 Macro Phase Lifecycle; §9 Architecture Checkpoint; Review Gate Summary.

### 4.3 Architecture Traceability Review inside CAR (Documentation Certification)

**Why it emerged:** CAR needed an explicit end-to-end frozen-architecture conformance check, not a code-quality review.

**Problem solved:** Certifies component inventory fidelity, ownership, dependencies, and data sources against Discovery/Contracts/Data Model/Freeze/Plan.

**Reusable because:** Mandatory for every Category B epic; technology-agnostic.

**Playbook locations:** §9 CAR; Epic Workflow Step 5; Definition of Done; Category B workflow; Review Gate Summary.

---

## 5. Workflow Improvements Considered but NOT Adopted

| Candidate | Disposition | Why |
|---|---|---|
| Author a new ADR for REPLAY UI-state / navigation | Rejected | Existing ADRs already governed the decisions; Playbook §8.4 forbids proactive ADRs |
| Extend runtime session state to carry REPLAY mode | Rejected | UI-layer signal + additive state-machine parameter preserved ownership and avoided domain mutation |
| Include optional audit panel in V1.3 scope | Deferred / excluded | Master Plan non-goal for candidate-facing MVP; binary exclusion recorded at Domain Contracts |
| Treat intermediate mid-macro-phase reviews as official Architecture Checkpoints | Rejected | Would authorize next macro phase before declared checkpoint scope is complete |
| Persist every checkpoint/CAR transcript as a frozen epic planning document | Not adopted | Gate outcomes are recorded in Overview / close-out status; regenerating historical certification prose into planning docs would blur freeze history |
| Mandate one commit per panel/component regardless of phase cohesion | Not forced as Playbook rule | Dependency Validation still requires self-contained boundaries; forcing micro-commits when fixtures/invariants are shared adds process cost without architecture benefit |

---

## 6. Engineering Metrics

| Metric | Value |
|---|---|
| Implementation phases | 6 (Phases 1–6) |
| Macro phases | 2 (A: Phases 1–3; B: Phases 4–6) |
| Architecture Checkpoints | 2 — Checkpoint A APPROVED; Checkpoint B APPROVED |
| Planning / freeze certifications | Architecture Discovery COMPLETE; Domain Contracts COMPLETE; Data Model COMPLETE; Architecture Freeze APPROVED; Implementation Plan ACCEPTED |
| Close-out certifications | CAR APPROVED (Architecture Traceability); Final Regression CERTIFIED; Documentation Certification COMPLETE; Final Review / FAR APPROVED; Epic CLOSED |
| Initial regression baseline | 6574 passing, 0 failures |
| Final regression baseline | 6637 passing, 0 failures |
| Test growth | +63 |
| Replay UI / REPLAY state-machine tests at close-out | 63 green (suite subset reported at Regression Certification) |
| EPIC-04-related commits (init → close) | 16 total: 6 epic planning/docs commits; 6 implementation feat/test commits; 1 tech-debt chore; 3 playbook/workflow commits |
| Planned production commit boundaries | 11 (C1–C11); Phase 4 delivered as one phase commit rather than six panel commits |
| Documentation created | `EPIC-04-OVERVIEW.md`, `EPIC-04-REPLAY-UI.md`, `EPIC-04-DOMAIN-CONTRACTS.md`, `EPIC-04-DATA-MODEL.md`, `EPIC-04-ARCHITECTURE-FREEZE.md`, `EPIC-04-IMPLEMENTATION-PLAN.md` |
| Playbook revisions during EPIC-04 | 3 (Category B governance; checkpoint timing; CAR Architecture Traceability) |
| New ADRs authored | 0 |
| Open P0/P1 findings at close | 0 |
| Architecture Assumptions at close | AA-01…AA-08 all VERIFIED |

---

## 7. Lessons Learned

Reusable guidance for future Category B epics:

1. **Freeze before code, then treat freeze as law.** Architecture-first delivery worked because Forbidden scope and checkpoints enforced it.
2. **Discover consumers before contracts.** Component Inventory + Traceability Matrix prevented dead fields and unmet requirements.
3. **Register assumptions early; close them with evidence.** CONDITIONALLY VERIFIED is acceptable at Freeze only when a named later phase owns enforcement tests.
4. **Do not invent ADRs.** Reuse accepted ADRs; record skip rationale in Architecture Freeze when no unresolved decision remains.
5. **Official checkpoints are macro-phase gates.** Informal reviews are useful; they never authorize the next macro phase.
6. **CAR certifies architecture conformance.** For Category B, Architecture Traceability is mandatory completion criteria, not optional commentary.
7. **Temporary bridges need named deletion targets.** Accept WARNINGs only when the removal phase is explicit and reached before CAR.
8. **Isolate unrelated debt.** Repo hygiene commits must not mix into feature phase commits.
9. **Allowed/Forbidden tables must include transitive integration surfaces.** Layout, bindings, and orchestrators are architecture surfaces, not afterthoughts.
10. **Regression baseline is a workflow artifact.** Every phase prompt and close-out certification must reference the updated count, not the epic-open count.
11. **Commit tables validate dependency order; phase cohesion may consolidate delivery.** Prefer dependency-safe boundaries over ceremonial micro-commits when shared fixtures dominate.

---

## 8. Recommendations for Future EPICs

Broadly reusable only:

1. Keep the Category B sequence and Architecture Exit Criteria unchanged for the next major architectural epic.
2. Require Architecture Traceability as part of every Category B CAR before Final Review.
3. Preserve the official-vs-informal Architecture Checkpoint distinction.
4. Keep conditional ADR policy: evaluate existing ADRs first; author only for genuine unresolved decisions.
5. For any CONDITIONALLY VERIFIED assumption at Freeze, name the verification phase and tests in the Implementation Plan.
6. Isolate pre-existing technical debt into separate chore commits with zero behavioural change.
7. At Implementation Plan time, validate Allowed/Forbidden scope for transitive integration modules, not only primary feature files.
8. Prefer named deletion targets for any temporary bridge accepted at a checkpoint.
9. Continue Zero Known Failing Tests and Regression Baseline Protocol without exception.
10. Capture post-close engineering lessons in `docs/master-plan/retrospectives/` rather than rewriting closed epic documents.

---

## 9. Playbook Stability Assessment

### Assessment

The Development Playbook appears **stable** after EPIC-04.

EPIC-04 exercised the full Category B lifecycle and produced three evidence-based Playbook amendments (governance artifacts at initialisation; checkpoint timing; CAR Architecture Traceability). Close-out completed without discovering an additional missing gate, sequencing rule, or review type.

### Recommendation on further Playbook modification

**No additional workflow modification is recommended before the next EPIC.**

Apply the current Playbook as written. Amend only if the next epic surfaces a genuine, reusable process gap that is not already covered by §2 principles, §8 Category B workflow, or §9 review gates.

### Retrospective scope note

This retrospective intentionally does not modify the Playbook. Prior EPIC-04 Playbook updates already absorbed the reusable workflow lessons.

---

## Sources

Reviewed for this retrospective (not modified):

- `docs/master-plan/V13-DEVELOPMENT-PLAYBOOK.md`
- `docs/master-plan/epics/EPIC-04-OVERVIEW.md`
- `docs/master-plan/epics/EPIC-04-REPLAY-UI.md`
- `docs/master-plan/epics/EPIC-04-DOMAIN-CONTRACTS.md`
- `docs/master-plan/epics/EPIC-04-DATA-MODEL.md`
- `docs/master-plan/epics/EPIC-04-ARCHITECTURE-FREEZE.md`
- `docs/master-plan/epics/EPIC-04-IMPLEMENTATION-PLAN.md`
- EPIC-04 certification outcomes recorded at close-out: Architecture Checkpoints A/B, CAR (Architecture Traceability), Final Regression Certification, Documentation Certification, Final Review / FAR, Epic Close

---

*Post-close Engineering Retrospective for EPIC-V13-04. Historical EPIC documents remain authoritative for freeze-time decisions; this document captures engineering process lessons only.*
