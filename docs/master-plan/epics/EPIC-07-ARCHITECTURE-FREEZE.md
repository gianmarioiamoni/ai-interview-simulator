# EPIC-07 — Production UX: Architecture Freeze

**Status:** ARCHITECTURE FREEZE APPROVED  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Architecture Freeze (Playbook §8.5 / §8.7 planning subset)  
**Precondition:** Overview, Discovery, Architecture Review, Domain Contracts, Data Model COMPLETE; HEAD `f95c17c`; working tree clean  
**Authority:** Formal gate between planning and Implementation Plan. Production code must not begin until Freeze APPROVED **and** Implementation Plan accepted (§8.7).  
**Governing:** AR-01…AR-15; EC-*; DM-*; ADR-003; ADR-019; ADR-033; ADR-037; ARC-01

---

## Save Token (precondition)

| Check | Result |
|---|---|
| Working tree | Clean |
| HEAD | `f95c17c` — docs(epic-07): freeze Production UX data model |
| Stash | None |

---

## 1. Architecture Freeze Certification

### ARCHITECTURE FREEZE: APPROVED

| Gate | Result |
|---|---|
| Architecture Discovery (§8.1) | PASS |
| Component Inventory (UI-bearing) | PASS — `EPIC-07-PRODUCTION-UX.md` §4 |
| Domain Contracts (§8.2) | PASS — `EPIC-07-DOMAIN-CONTRACTS.md` |
| Data Model (§8.3) | PASS — `EPIC-07-DATA-MODEL.md` |
| Traceability Matrix | PASS — Contracts §7 (15/15); Data Model §8 |
| Architecture Assumptions | PASS — §6 (no UNVERIFIED) |
| Ownership / sole-writer | PASS — §4 |
| Data Model internal consistency | PASS — §3 |
| Formal §8.4 ADR Gate | **SKIP** — §2 |
| BLOCKER findings | NONE |
| Category B Exit Criteria (planning subset) | PASS — §8 |
| Implementation Plan (§8.6) | NOT YET — next step |

**Production code:** NOT authorized by this Freeze alone.  
**Next authorized planning step:** Implementation Plan (`EPIC-07-IMPLEMENTATION-PLAN.md`).

---

## 2. Formal §8.4 ADR Gate

| Check | Result |
|---|---|
| Genuine unresolved architectural decision after Contracts + Data Model? | **No** |
| Existing ADRs evaluated for applicability? | **Yes** |
| New ADR required? | **No** |
| Architectural conflict classified? | **None** |
| **ADR Gate result** | **SKIP** |

### Why SKIP

| Concern | Governing authority (reuse) |
|---|---|
| UI derives from state; no UI orchestration ownership | ADR-003 |
| Language mode (single/mixed) | ADR-019 (`LanguageConfig` / `LanguageProfile.session_mode`) |
| Report sole presentation source / `FinalReportDTO.from_report` | ADR-033 (unchanged; EPIC-07 read-only polish) |
| ReplaySession read-only LLM-free UI | ADR-037 + EPIC-04 freeze (unchanged) |
| Runtime vs projection; Fail Fast; Single Writer | ARC-01 + Playbook principles |
| Ephemeral presentation contracts (errors, surfaces, catalogs) | Same class as EPIC-04 UI-layer values; no new persistent domain artifact (AR-01) |

**ADR count authored in EPIC-07 planning:** 0  
**AA-07:** VERIFIED by this SKIP record.

---

## 3. Data Model Internal Consistency

| Check | Verdict |
|---|---|
| Every EC-* contract has a frozen field table in Data Model | PASS |
| Enums closed and catalog-complete (`AsyncBoundary` × message keys) | PASS |
| `SurfacePhase` / `surface_id` / empty-copy keys aligned | PASS |
| ExecutionErrorKind × base messages aligned; `shows_traceback=False` literal | PASS |
| SessionConfig language_mode rules match ADR-019 (DM-V-SC-01/02/03) | PASS |
| Serialization model forbids persistence of EC-* (SM-01…SM-06) | PASS |
| Existing DTO shapes explicitly unchanged (§6 inventory) | PASS |
| Reconstruction completeness: all in-scope surfaces have sources (§7) | PASS |
| No speculative persistence introduced | PASS |

---

## 4. Ownership Model (no conflicts)

| Artifact / concern | Sole writer | Readers | Conflict? |
|---|---|---|---|
| `CandidateFacingError` | Boundary handler that observed failure | Error/fallback surfaces | None |
| `SurfaceState` | UIResponseBuilder / sole surface assembler | Gradio adapters / panels | None |
| `ExecutionErrorPresentation` | UI presentation projector | Feedback surfaces | None |
| `FeedbackBundle` | Runtime feedback path only (AR-11) | UI read-only | None |
| `SessionConfigPresentation` | Candidate widgets (intent) | Start validator/handler | None |
| `LanguageProfile` | Existing ADR-019 InterviewSetup path | Config / runtime (unchanged) | None |
| `SessionHistoryListPresentation` | History loader presentation adapter | History / replay-from-history | None |
| `FinalReportDTO` | `from_report` only | Report hosts (read-only polish) | None |
| `ReplaySession` | `replay_node` / Replay Graph | Replay UI (read-only) | None |
| `LearningProgress` | Existing progress path | Progress panel (read-only) | None |
| `InterviewState` | Graph + existing handlers | UI | **No new fields** (AR-03) |
| Unwired DELETE_TARGET modules | N/A (must not be live hosts) | Deletion hygiene | None |

**Ownership conflicts remaining:** **None**.

---

## 5. Frozen Architectural Decisions (summary)

| ID | Decision | Status |
|---|---|---|
| AR-01 | Presentation-plane polish only; no new nodes; no new persistent artifacts | FROZEN |
| AR-02 | Reuse existing ADRs; no new ADR at Review | FROZEN — confirmed by §8.4 SKIP |
| AR-03 | No new `InterviewState` fields | FROZEN |
| AR-04 | Language mode = ADR-019 session mode (not UI locale) | FROZEN |
| AR-05 | Progress = report-hosted trend only | FROZEN |
| AR-06 | Sole live Gradio host; unwired not parallel hosts | FROZEN |
| AR-07 | Delete sequencing → Implementation Plan (inventory frozen) | FROZEN (scope); sequencing not architecture |
| AR-08 / AR-09 | Candidate-facing async fallbacks; no internal error exposure | FROZEN |
| AR-10 | Error/empty/loading contracts | FROZEN in Contracts + Data Model |
| AR-11 | FeedbackBundle writer unchanged | FROZEN |
| AR-12 | Session history loader in EPIC-07 scope | FROZEN |
| AR-13 | A11y targets (keyboard + WCAG 2.1 AA report/replay) | FROZEN |
| AR-14 | Gradio conformance approach | Implementation verification (not ADR) |
| AR-15 | Master Plan deps = EPIC-04 + EPIC-05 only | FROZEN |

---

## 6. Architecture Assumptions Register — Freeze disposition

**Rule applied (this Freeze):** every assumption is `VERIFIED` or `INVALIDATED` with documented rationale; **none** remain `UNVERIFIED`.

| ID | Status | Freeze disposition |
|---|---|---|
| AA-01 | VERIFIED | Presentation-only; no persistent EC-* |
| AA-02 | VERIFIED | Existing ADRs govern; §8.4 SKIP |
| AA-03 | VERIFIED | No new InterviewState fields |
| AA-04 | INVALIDATED | Rationale: “already achievable on Gradio” is not an architectural premise. Response: AX requirement rows + verification artifact types frozen (Data Model §4.6); residual conformance = Implementation verification obligation; **not** an ADR trigger |
| AA-05 | VERIFIED | Deterministic no-loader rules (DM-V-SS-03/04) |
| AA-06 | VERIFIED | Polish targets = EPIC-04/05 |
| AA-07 | VERIFIED | §8.4 ADR SKIP recorded in §2 |
| AA-08 | INVALIDATED | Rationale: locale ≠ language mode. Response: ADR-019 session mode + EC-SC-01 / DM-V-SC-* |
| AA-09 | VERIFIED | FeedbackBundle presentation-only polish |
| AA-10 | VERIFIED | Unwired modules not live hosts; DELETE_TARGET inventory frozen |
| AA-11 | VERIFIED | History loader in scope; EC-SH-01 / DM §4.5 |
| AA-12 | VERIFIED | Report-hosted progress only |
| AA-13 | VERIFIED | No prior-epic P0/P1 alters EPIC-07 ephemeral shapes |

**UNVERIFIED count:** 0  
**Note on Playbook §8.7 wording (“all VERIFIED”):** INVALIDATED-with-documented-response is treated as a **resolved** assumption under §8.3 and the EPIC-07 Freeze Assumptions rule; it is not an open modelling gap and does not block this Freeze.

---

## 7. Inherited presentation completeness

| Topic | Verdict |
|---|---|
| `FinalReportDTO` ← `Report` mapping | **Inherited PASS** — unchanged by EPIC-07 (ADR-033 / EPIC-05); polish is read-only |
| Replay panel sources from `ReplaySession` | **Inherited PASS** — EPIC-04 + Data Model §7 |
| EPIC-07 surface reconstruction completeness | **PASS** — Data Model §7 |
| LLM-free UI / replay boundaries | **PASS** — ADR-037 / ARC-01 / AR-01 |

---

## 8. §8.7 Architecture Exit Criteria — planning subset

| Criterion | Status |
|---|---|
| Architecture Discovery complete (§8.1) | PASS |
| Component Inventory complete | PASS |
| Traceability Matrix complete | PASS |
| Domain Contracts frozen (§8.2) | PASS |
| Data Model frozen (§8.3) | PASS |
| Architecture Assumptions resolved (no UNVERIFIED) | PASS — §6 |
| No BLOCKER findings open | PASS |
| ADR decisions complete (where required) | PASS — none required; Gate SKIP |
| Architecture Freeze declared (§8.5) | **PASS — this document** |
| Implementation Plan accepted (§8.6) | **PENDING** — next step |

---

## 9. Non-blocking open items (explicitly non-architectural)

| ID | Item | Class | Allowed after Freeze? |
|---|---|---|---|
| NI-01 | Unwired module delete commit sequencing | Implementation Plan | Yes |
| NI-02 | Gradio/platform a11y evidence collection | Implementation verification | Yes |
| NI-03 | DOC-I-01 / PROC-I-01 process documentation | Process hygiene | Yes |
| NI-04 | Exact test file names / phase commit order | Implementation Plan | Yes |

These are **not** open architectural questions and do **not** reopen Contracts, Data Model, or ADR Gate.

---

## 10. Remaining architectural decisions

| Question | Result |
|---|---|
| Any remaining architectural decision? | **None** |
| ADR required before Implementation Plan? | **No** |
| Stop before implementation due to conflict? | **No** |

---

## 11. Implementation readiness statement

| Question | Answer |
|---|---|
| Architecture Freeze approved? | **YES** |
| Formal §8.4 ADR Gate | **SKIP** |
| Ready for **Implementation Plan**? | **YES** |
| Ready for **production code**? | **NO** — blocked until Implementation Plan accepted (§8.6 / §8.7) |

---

## 12. Recommendation

**Next engineering task:** Produce `EPIC-07-IMPLEMENTATION-PLAN.md` (phases, commit boundaries, Implementation Dependency Validation, regression baseline). No production code in that step.

---

*Architecture Freeze APPROVED. Living status: `EPIC-07-OVERVIEW.md`.*
