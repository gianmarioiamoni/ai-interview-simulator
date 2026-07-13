# EPIC-02 Overview — Cross-Session Profile Continuity

**Epic ID:** EPIC-V13-02  
**Status:** PLANNED  
**Phase:** Phase 2 — Core Domain  
**Date:** 2026-07-06  
**Master Plan Reference:** §4 EPIC-V13-02

---

## 1. Purpose

Define and implement `LongitudinalProfile` — the persistent, cross-session accumulation of `CandidateProfileSnapshot` instances. After every session completion, the platform updates the candidate's longitudinal record, enabling behavioral profile tracking and progress measurement across sessions rather than within a single session.

---

## 2. Business Value

A candidate who completes multiple sessions receives no cross-session continuity in V1.2. Every session starts from zero. EPIC-02 corrects this: after the Epic ships, a returning candidate's coaching is informed by their entire session history, and their progress view reflects real behavioral trends rather than isolated session snapshots. This is the foundational capability that differentiates the platform from a one-shot assessment tool.

---

## 3. Dependencies

### Hard Dependencies (blocking)

- **EPIC-01 (EPIC-V13-01) — Closed.** `Report` must be the sole authoritative scoring artifact before longitudinal profile accumulation can reference scoring data. EPIC-01 is closed; this dependency is satisfied.

### Soft Dependencies (informing but not blocking)

- **V1.2 `CandidateProfileSnapshot` contract** — exists and is frozen. EPIC-02 activates it as a cross-session accumulation unit.
- **V1.2 `SessionHistory` persistence** — exists and is operational. EPIC-02 relies on it as the source of per-session snapshot data.
- **V1.2 `CandidateIdentity` schema** — defined; not yet active as a cross-session anchor. EPIC-02 activates this anchor.
- **V1.2 `LanguageCapability` reserved concept** — defined in the domain freeze; EPIC-02 activates it for cross-session accumulation.

### Downstream Dependents

- **EPIC-V13-05 (Unified Report):** requires `LongitudinalProfile` for the progress trend panel.
- **EPIC-V13-06 (Explainability):** may reference behavioral profile features as evidence anchors.
- **EPIC-V13-09 (Performance Baseline):** must profile `KnowledgePipeline` cross-session update cost.

---

## 4. Scope

- Define the `LongitudinalProfile` domain contract: field set, types, validation invariants, sole writer, declared readers, and lifecycle.
- Define the `LongitudinalProfile` ownership model: who writes it, when (on session completion), and under which node.
- Define the storage schema and schema versioning policy for `LongitudinalProfile` persistence.
- Establish `CandidateIdentity` as the active cross-session anchor.
- Activate `CandidateProfileSnapshot` as the unit of accumulation.
- Extend `ProgressTracker` to derive `LearningProgress` from both dimensional scores and behavioral profile trends.
- Define the cross-session `ObservationStore` accumulation policy: make the persistence boundary explicit (Observations were session-scoped in V1.2).
- Activate `LanguageCapability` for cross-session accumulation.
- Enforce the Reconstruction Completeness PAT on all `LongitudinalProfile` and `CandidateProfileSnapshot` reconstruction paths.

---

## 5. Non-Goals

- Cohort-level benchmarking (`PeerBenchmark` — V2).
- Organisation-level profiles (`OrganisationProfile` — V2).
- Authentication or candidate identity federation (V2).
- `GoalTrack` — V1.3 stretch goal only; not a V1.3 commitment.
- Comparative analysis between candidates.
- Any change to scoring logic, dimension weights, or calibration constants.

---

## 6. Expected Architectural Impact

- **New frozen domain contract:** `LongitudinalProfile` (`frozen=True`, single builder, `extra=forbid`).
- **New builder:** `LongitudinalProfileBuilder` — assembles `CandidateProfileSnapshot` instances into the longitudinal record. Must satisfy P-05 (Builders Assemble; Engines Compute).
- **New sole writer:** A designated LangGraph node (to be decided by ADR) is the sole writer of `LongitudinalProfile` per P-02 (Single Ownership).
- **`InterviewState` impact:** One or more new fields for `LongitudinalProfile` reference. Each new field requires a declared sole writer at the moment of addition.
- **`ProgressTracker` extension:** Extended to consume behavioral profile trends from `LongitudinalProfile`. This is an additive change; no existing `ProgressTracker` contract is broken.
- **`ObservationStore` policy change:** Persistence boundary becomes explicit. This may require an ADR if the policy change affects the V1.2 frozen `SessionHistory` schema.
- **PAT compliance:** The `LongitudinalProfileBuilder` is subject to the Sole-Writer Node PAT and the Reconstruction Completeness PAT.

---

## 7. Runtime Impact

- A new pipeline execution path runs on session completion: after `Report` is produced, `LongitudinalProfile` is updated with the new `CandidateProfileSnapshot`.
- This path must be a LangGraph node per P-04 (LangGraph Is the Sole Runtime Orchestrator).
- The path must be non-fatal (session completion must not fail if longitudinal update fails) — to be confirmed by ADR.
- No LLM calls are permitted in the longitudinal update path. Snapshot assembly is deterministic from stored features.
- The update is write-once per session: idempotent re-execution must not create duplicate snapshots.
- Storage write latency for `LongitudinalProfile` persistence must not degrade the session close SLO (report generation < 3s).

---

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `LongitudinalProfile` ownership decision is contentious (which node writes it, when exactly) | Medium | High | Resolve with a dedicated ADR before any implementation begins; do not proceed without a written decision |
| `CandidateIdentity` schema design collides with V2 auth requirements | Low | Medium | Design `CandidateIdentity` to be nullable/anonymous in V1.3; document V2 migration path in ADR |
| `ObservationStore` accumulation policy change breaks V1.2 `SessionHistory` schema | Medium | High | Audit `SessionHistory` schema before committing to the policy; if schema change required, follow schema versioning policy |
| `LongitudinalProfile` schema versioning policy not established early, causing migration cost later | Medium | Medium | Declare versioning policy in the first `LongitudinalProfile` ADR; do not ship without it |
| Behavioral trend computation produces misleading output when fewer than 3 sessions exist | Medium | Medium | Enforce explicit "insufficient data" state for < 3 sessions; never extrapolate from a single session |
| `LongitudinalProfileBuilder` accumulates complexity over time if snapshot assembly logic is complex | Low | Medium | Apply SRP strictly: builder only assembles; any derivation logic belongs in a separate engine |

---

## 9. Definition of Done

EPIC-02 is done when all of the following are true:

- `LongitudinalProfile` domain contract is frozen (`frozen=True`, `extra=forbid`, sole builder, declared sole writer).
- After every session completion, `LongitudinalProfile` is updated with the new `CandidateProfileSnapshot`.
- `CandidateIdentity` is active as the cross-session anchor; `LongitudinalProfile` is queryable by `CandidateIdentity`.
- `ProgressTracker` derives `LearningProgress` from both dimensional scores and behavioral profile trends.
- `ObservationStore` cross-session accumulation policy is explicit, documented, and implemented.
- `LanguageCapability` is activated for cross-session accumulation.
- Schema versioning policy for `LongitudinalProfile` is declared and implemented.
- Reconstruction Completeness PAT is enforced on all `LongitudinalProfile` and `CandidateProfileSnapshot` reconstruction paths.
- All new `InterviewState` fields have declared sole writers.
- No LLM calls occur in the longitudinal update path (enforced by architectural test).
- All new domain contracts are covered by contract tests (immutability, `extra=forbid`, sole builder).
- `LongitudinalProfile` accumulates correctly across a synthetic 10-session test dataset.
- Storage write does not degrade session close SLO.
- CAR performed; all P0/P1 findings resolved.
- FR (Final Review) performed and produces Closed outcome.
- Full regression suite passes with zero failures.
- All affected documentation updated (Architecture Guide, INDEX, ADRs, Technical Debt Register).

---

## 10. Required ADRs

The following ADR decisions must be frozen before implementation begins. ADRs are not written here — this section identifies the decisions that require ADR governance.

| Decision | Blocking? |
|---|---|
| `LongitudinalProfile` ownership model: which node writes it, on what trigger, and under what failure semantics | Yes |
| `CandidateIdentity` activation model: anonymous vs. identified anchor in V1.3 | Yes |
| `ObservationStore` cross-session accumulation policy: whether V1.2 `SessionHistory` schema requires amendment | Yes (if schema change required) |
| `LongitudinalProfile` schema versioning policy | Yes |
| Non-fatal semantics for the longitudinal update path (should session completion fail if profile update fails?) | Yes |

---

## 11. Planning Classification

**Category:** Category B — Major Architectural Epic

**Rationale:** EPIC-02 introduces a new frozen domain contract (`LongitudinalProfile`), a new persistent artifact written to storage, a new builder (`LongitudinalProfileBuilder`), new `InterviewState` fields, and a new schema. All Category B criteria apply.

**Mandatory Pre-Implementation Workflow:**

1. Master Plan (this document provides the epic reference)
2. Architecture Review (full analysis: current state → target state; affected subsystems; confirmed and missing decisions; risks)
3. ADR(s) — all five decisions identified in §10 must be frozen
4. Domain Contracts document (`EPIC-02-DOMAIN-CONTRACTS.md`)
5. Data Model Specification (`EPIC-02-DATA-MODEL.md`)
6. Architecture Freeze (gate: all decisions frozen, all open issues resolved)
7. Implementation (incremental, against frozen contracts, zero known failing tests at every phase)
8. CAR
9. FR
10. Epic Close

**Implementation cannot begin before Architecture Freeze passes.**

---

*This document is the authoritative overview for EPIC-02. It does not contain implementation details, ADR content, or domain contract specifications. Those are produced in the Category B pre-implementation workflow.*
