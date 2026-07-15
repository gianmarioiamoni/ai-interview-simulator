# EPIC-04 — Replay UI Experience

**Status:** IMPLEMENTATION PLAN ACCEPTED — Implementation ready to begin  
**Date:** 2026-07-15  
**Epic ID:** EPIC-V13-04  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-04  
**Roadmap Phase:** Phase 3 — User Experience  
**Precondition:** EPIC-V13-03 CLOSED; `ReplaySession` contract frozen (ADR-037); `replay_node` implemented, deterministic, LLM-free, regression-tested.

---

## 1. Business Objective

Deliver the candidate-facing session replay interface backed by `ReplaySession`. Candidates must be able to navigate any completed session question-by-question, inspect answers, scores, and coaching notes, without any LLM calls or answer re-submission.

---

## 2. Architectural Objective

Implement the Replay UI as a strictly read-only, LLM-free presentation layer consuming `ReplaySession` as its sole data source. No UI component may trigger computation, invoke services, or bypass the `ReplaySession` contract.

---

## 3. Dependencies on Previous EPICs

| EPIC | Status | Dependency |
|---|---|---|
| EPIC-V13-01 | CLOSED | `Report` is the sole scoring artifact; `ReplaySession` reads `Report`-consistent fields |
| EPIC-V13-02 | CLOSED | `LongitudinalProfile` established; cross-session data stable |
| EPIC-V13-03 | CLOSED | `ReplaySession` frozen; `replay_node` implemented, deterministic, LLM-free |

---

## 4. Prerequisites (Definition of Ready)

- [ ] EPIC-03 Final Review passed and CLOSED
- [ ] `ReplaySession` frozen (`frozen=True`, `extra=forbid`, ADR-037 D3)
- [ ] `replay_node` deterministic, LLM-free, regression-tested
- [ ] ADR-037 D3 field set sufficiency pre-verified at EPIC-03 Architecture Freeze
- [ ] No open P0/P1 findings from EPIC-03 affecting replay contracts

---

## 5. Expected Deliverables

- Question-by-question navigation (forward/backward controls)
- Per-question display: question text, candidate answer, execution result (coding questions), dimensional scores, coaching notes
- Session-level summary panel
- Navigation progress indicator
- Responsive layout (mobile, tablet, desktop)
- Zero LLM calls from any UI component (enforced by architectural test)
- Read-only, no re-submission controls
- Production-quality UX (no placeholder states, no internal error surfaces)

---

## 6. ADR Policy

Existing ADRs shall be reused whenever possible. Candidate existing ADRs for this epic:

| ADR | Applicability |
|---|---|
| ADR-037 (Replay Engine Architecture) | D3 governs `ReplaySession` field set consumed by this epic |
| ADR-033 (Unified Report Architecture) | Replay link integration point; relevant to EPIC-05 |
| ADR-003 (State-Driven UI) | Must be evaluated for replay navigation state — may govern without modification |

A new ADR shall be created **only if** a genuine unresolved architectural decision remains after Domain Contracts and Data Model documents are produced. Do not create ADRs proactively.

---

## 7. Implementation Risk Level

**Medium**

| Risk | Severity | Mitigation |
|---|---|---|
| `ReplaySession` field set (ADR-037 D3) insufficient for UI requirements | HIGH — blocking | Verify AA-01 during Architecture Discovery |
| Navigation state management requires new design decision not covered by ADR-003 | MEDIUM | Evaluate ADR-003 during Architecture Discovery (AA-03) |
| Performance for long sessions (20+ questions) | MEDIUM | Profile with 20-question fixture before shipping (Master Plan explicit) |
| New UI library dependency required for responsive layout | LOW | Confirm existing stack sufficiency (AA-07) |

---

## 8. Estimated Implementation Size

**Medium** — frontend components, navigation logic, responsive layout. No new domain contracts, no new LangGraph nodes, no new builders. Scope bounded to the `ReplaySession` consumer layer.

---

## 9. Architecture Assumptions Register

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|
| AA-01 | `ReplaySession` field set (ADR-037 D3) is sufficient to render all UI panels defined in Master Plan §4 EPIC-V13-04 | VERIFIED | EPIC-04-REPLAY-UI.md §5 | Verified by Architecture Discovery Traceability Matrix: all 17 requirements mapped to source fields; no gap found |
| AA-02 | No LLM call is reachable from any Replay UI component render path | CONDITIONALLY VERIFIED | EPIC-04-ARCHITECTURE-FREEZE.md | Architectural constraint confirmed; enforcement test required in implementation |
| AA-03 | ADR-003 (State-Driven UI) governs replay navigation state without requiring a new ADR | VERIFIED | EPIC-04-DOMAIN-CONTRACTS.md §2.2 | Navigation position is UI-scoped ephemeral cursor; ADR-003 governs without modification; no new ADR required |
| AA-04 | ADR-037 requires no modification to satisfy EPIC-04 UI requirements | VERIFIED | EPIC-04-RELAY-UI.md §5 | Verified by Architecture Discovery: all requirements covered by existing ADR-037 D3 field set |
| AA-05 | Replay UI is fully read-only; no write path to `InterviewState`, `SessionHistory`, or any domain artifact | VERIFIED | EPIC-04-DOMAIN-CONTRACTS.md §6 | Formally verified: read-only constraint table complete; `current_position` and `ReplayContext` are ephemeral UI-layer state |
| AA-06 | `ReplaySession` is produced on demand per request; no caching or persistence is needed at the UI layer | VERIFIED | ADR-037 D1 §1.4 | ADR-037 D1 §1.4 confirms no persistence; Architecture Discovery confirms UI receives session in memory |
| AA-07 | Responsive layout (mobile, tablet, desktop) is achievable within the existing frontend stack without new dependencies | VERIFIED | EPIC-04-DATA-MODEL.md §6 | Gradio framework confirmed; `gr.Row`, `gr.Column`, custom CSS injection sufficient for all three breakpoints; no new dependency required |
| AA-08 | Performance is acceptable for sessions of 20+ questions without architectural changes | CONDITIONALLY VERIFIED | EPIC-04-DATA-MODEL.md §7 | O(1) navigation confirmed; no architectural blocker; profiling gates (load time, navigation step, memory) required in Implementation Plan |

**All assumptions must reach status VERIFIED before Architecture Freeze.**

---

## 10. Architecture Workflow

```
EPIC Initialization  ← COMPLETE
        ↓
Architecture Discovery  ← COMPLETE
  → EPIC-04-REPLAY-UI.md
  → Inventory ReplaySession fields (ADR-037 D3)
  → Map fields to all UI display requirements (populates Traceability Matrix)
  → Identify field gaps (blocking if any UI requirement has no source field)
  → Produce Component Inventory section
  → Evaluate ADR-003, ADR-033, ADR-037 applicability
  → Update Architecture Assumptions Register (AA-01, AA-03, AA-04)
        ↓
Domain Contracts  ← COMPLETE
  → EPIC-04-DOMAIN-CONTRACTS.md
  → All component props contracts
  → Navigation state contract
  → Per-question display contract
  → Session summary panel contract
  → Traceability Matrix (complete)
  → Field-to-component mapping (every ReplaySession field traced)
  → Verify AA-05
        ↓
Data Model  ← COMPLETE
  → EPIC-04-DATA-MODEL.md
  → Resolve open modelling questions from Domain Contracts
  → Freeze component data model field tables
  → Verify replay completeness: every UI panel sourced from ReplaySession
  → Verify AA-06, AA-07, AA-08
  → All Architecture Assumptions must be VERIFIED at end of this step
        ↓
Architecture Review / ADR  (conditional)  ← COMPLETE (skipped — no new ADR required)
  → Evaluate: does any genuine unresolved architectural decision remain?
    YES → Author new ADR; freeze decision
    NO  → Skip; record this decision in Architecture Freeze document
  → Verify AA-02 enforcement mechanism
        ↓
Architecture Freeze  ← APPROVED
  → EPIC-04-ARCHITECTURE-FREEZE.md
  → All Architecture Exit Criteria satisfied (§8.6 of Playbook)
  → All Architecture Assumptions VERIFIED
  → Traceability Matrix and Component Inventory referenced
  → Zero open issues in any planning document
        ↓
Implementation Plan  ← ACCEPTED
  → EPIC-04-IMPLEMENTATION-PLAN.md
  → Commit boundary table + Implementation Dependency Validation
  → Phase breakdown
  → Regression baseline declared (6574 passing)
        ↓
Implementation
```

---

## 11. Architecture Exit Criteria

Implementation may begin only if **ALL** of the following are true:

- [ ] Architecture Discovery complete (§8.1 DoD satisfied)
- [ ] Component Inventory complete
- [ ] Traceability Matrix complete
- [ ] Domain Contracts frozen (§8.2 DoD satisfied)
- [ ] Data Model frozen (§8.3 DoD satisfied)
- [ ] All Architecture Assumptions status = VERIFIED
- [ ] No BLOCKER findings in any planning document
- [ ] ADR decisions complete (if any ADR was required)
- [ ] Architecture Freeze declared (§8.5 DoD satisfied)
- [ ] Implementation Plan accepted (§8.6 DoD satisfied; Dependency Validation passed)

---

## 12. Required Architecture Documents

| # | Document | Mandatory |
|---|---|---|
| 1 | `EPIC-04-REPLAY-UI.md` | Yes — Architecture Discovery |
| 2 | `EPIC-04-DOMAIN-CONTRACTS.md` | Yes — Domain Contracts |
| 3 | `EPIC-04-DATA-MODEL.md` | Yes — Data Model |
| 4 | New ADR (if required) | Conditional — only if unresolved decision after step 3 |
| 5 | `EPIC-04-ARCHITECTURE-FREEZE.md` | Yes — Architecture Freeze gate |
| 6 | `EPIC-04-IMPLEMENTATION-PLAN.md` | Yes — Implementation Plan |
