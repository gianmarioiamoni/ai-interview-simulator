# EPIC-07 — Production UX: Architecture Review

**Status:** ARCHITECTURE REVIEW COMPLETE — Domain Contracts COMPLETE (see `EPIC-07-DOMAIN-CONTRACTS.md`)  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-07; Product Goal P-07  
**Playbook:** V13 Development Playbook Version 1.0  
**Precondition:** `EPIC-07-PRODUCTION-UX.md` Architecture Discovery COMPLETE; HEAD `d5d3fb4`; working tree clean  
**Authority:** Architectural decision disposition of Discovery assumptions, findings, missing decisions, and review triggers. No Domain Contracts. No Data Model. No Implementation Plan. No production code. No speculative ADR.

---

## 0. Playbook sequencing note

Category B formal **§8.4 Architecture Review / ADR (conditional)** is defined to run **after** Domain Contracts and Data Model. This document is the **Discovery Architecture Review** — it freezes only architectural decisions that can be confirmed from Master Plan + existing ADRs/ARC-01 without contracts or implementation knowledge.

- **New ADR at this step:** NONE  
- **Formal §8.4 ADR gate:** Remains open until after Domain Contracts + Data Model (AA-07)  
- **Next mandatory Category B step:** Domain Contracts (`EPIC-07-DOMAIN-CONTRACTS.md`)

---

## 1. Decision summary

| Decision ID | Decision | Disposition | Governing authority |
|---|---|---|---|
| AR-01 | EPIC-07 is presentation-plane polish only: **no** new LangGraph nodes; **no** new persistent domain artifacts | **Confirmed** by existing architecture | Master Plan §4 EPIC-V13-07; ARC-01; Playbook Runtime First / Product Before Features |
| AR-02 | Existing ADRs govern without modification at this review: ADR-003, ADR-019, ADR-033, ADR-037, ARC-01 (+ related language/report ADRs as needed) | **Confirmed** — **no new ADR** | Playbook §8.4 (no proactive ADR) |
| AR-03 | EPIC-07 architectural default: **no new `InterviewState` fields** | **Confirmed** as default; reopen ADR path only if Contracts later prove a field is required | ADR-003; Sole-Writer |
| AR-04 | Master Plan “language mode” means ADR-019 **session language mode** (`LanguageConfig` → `LanguageProfile.session_mode`: single / mixed), **not** UI locale (`en`/`it`) | **Confirmed** by existing architecture; **documentation alignment** of Master Plan wording may still be useful | ADR-019 |
| AR-05 | Progress view for EPIC-07 is the **report-hosted** longitudinal progress trend panel; **no** standalone progress application | **Confirmed** by existing architecture | EPIC-05 / CD-07; Master Plan Go-Live progress item |
| AR-06 | Live Gradio layout (`UILayoutBuilder` path) is the **sole** candidate-facing host; unwired alternate view modules must **not** be reconstituted as parallel live hosts | **Confirmed** | ADR-003; Single Ownership / Deletion Is Completion |
| AR-07 | Exact fate of unwired modules (delete now vs later debt) is **not** an architectural fork requiring ADR; deletion target is in-scope for epic completion hygiene | **Deferred** to Domain Contracts / Implementation Plan sequencing | Playbook Deletion Is Completion |
| AR-08 | Every async candidate boundary in EPIC-07 scope requires a **candidate-facing** fallback; silent UI recovery without candidate message is architecturally non-compliant | **Confirmed** (principle) | Master Plan EPIC-07 scope; Playbook Fail Fast; Master Plan “No silent fallbacks” |
| AR-09 | Candidate-facing surfaces must **not** expose internal state (tracebacks, raw exception objects, internal failure reasons) | **Confirmed** (principle) | Master Plan EPIC-07 purpose/scope |
| AR-10 | Exact error/empty/loading **contracts** (schemas, copy tables, component APIs) are **not** frozen here | **Deferred** to Domain Contracts | MD-01, MD-04, MD-05 |
| AR-11 | `FeedbackBundle` sole-writer remains on the runtime feedback path; EPIC-07 may change **presentation** of already-produced feedback only; must not change runtime ownership or scoring semantics | **Confirmed** | ARC-01; Single Writer; OF-09 / RT-02 |
| AR-12 | Session-history loader stub is **in-scope** for EPIC-07 production-quality / error-boundary completeness (candidate path into replay) | **Confirmed** (scope) | Master Plan replay + production UX; OF-05 |
| AR-13 | Accessibility **targets** remain those in Master Plan (keyboard primary flows; WCAG 2.1 AA for report and replay) | **Confirmed** (target) | Master Plan §4 / Go-Live / Success metric 6 |
| AR-14 | Accessibility **conformance approach** under Gradio constraints | **Deferred** — cannot resolve without implementation knowledge | MD-06 / AA-04 |
| AR-15 | EPIC-04 and EPIC-05 CLOSED surfaces are the Master Plan dependency polish targets; EPIC-06 is **not** a Master Plan dependency for EPIC-07 | **Confirmed** | Master Plan §4 Dependencies |
| AR-16 | Conditional new ADR (formal §8.4) | **Deferred** until after Domain Contracts + Data Model | Playbook §8.4; AA-07 |
| AR-17 | DOC-I-01 Phase-3-complete vs EPIC-07 deps | **Documentation alignment** (non-blocking); no Master Plan edit in this step | Initialization OF-10 |
| AR-18 | PROC-I-01 EPIC-06 living Overview not CLOSED | **Deferred** (process hygiene); does not alter AR-15 | RT-07 |

**ADR creation:** None. No genuine unresolved architectural decision remains that cannot be governed by existing ADRs **for the decisions frozen above**. Contract-shaped gaps (MD-01/04/05/06) are Domain Contracts work, not ADR speculation.

---

## 2. Assumption dispositions

Authoritative statuses after this review. Discovery §6 register shall be updated to match.

| ID | Disposition | Status after review | Rationale (architecture only) |
|---|---|---|---|
| AA-01 | Confirmation by existing architecture | **VERIFIED** | AR-01 — presentation polish; no new nodes/persistent artifacts |
| AA-02 | Confirmation by existing architecture | **VERIFIED** | AR-02 — reuse ADR-003/019/033/037 + ARC-01; no ADR authored |
| AA-03 | Confirmation by existing architecture (default) | **VERIFIED** | AR-03 — default no new `InterviewState` fields; Contracts may only reopen via ADR path |
| AA-04 | Deferral | **UNVERIFIED** | AR-14 — Gradio WCAG achievability needs implementation evidence |
| AA-05 | Deferred at Review → verified at Contracts | **VERIFIED** (via Domain Contracts I-SS-02) | See `EPIC-07-DOMAIN-CONTRACTS.md` |
| AA-06 | Confirmation by existing architecture | **VERIFIED** | AR-15 — Master Plan deps are EPIC-04/05 only |
| AA-07 | Deferral | **UNVERIFIED** | AR-16 — formal §8.4 after Contracts + Data Model |
| AA-08 | Rejection (assumption false) | **INVALIDATED** | AR-04 — `en`/`it` locale dropdown ≠ ADR-019 language mode; response: EPIC-07 session-config polish must cover ADR-019 language mode as candidate-facing configuration concern |
| AA-09 | Confirmation by existing architecture | **VERIFIED** | AR-11 — presentation-only changes; sole-writer unchanged |
| AA-10 | Confirmation by existing architecture (partial) | **VERIFIED** | AR-06 — not reconstituted as live hosts; AR-07 defers delete-vs-later sequencing |
| AA-11 | Confirmation by existing architecture | **VERIFIED** | AR-12 — history stub in EPIC-07 scope |
| AA-12 | Confirmation by existing architecture | **VERIFIED** | AR-05 — report-hosted progress only |
| AA-13 | Deferral (process) | **UNVERIFIED** | AR-18 — EPIC-06 close-out process; not an architecture blocker per AR-15 |

**INVALIDATED response (AA-08):** Treat Master Plan “language mode” as ADR-019 session mode. Domain Contracts must trace session-configuration requirements to LanguageConfig/LanguageProfile mode surfaces (or explicit presentation of already-resolved mode). Do not treat UI locale as satisfying that requirement.

---

## 3. Open Findings dispositions

| ID | Disposition | Outcome |
|---|---|---|
| OF-01 | Confirmation — in-scope polish gap | **Remains open** as implementation/Contracts gap (placeholders/empty states). Not an ADR. |
| OF-02 | Confirmation — violates AR-08/AR-09 principles | **Remains open** as Contracts gap (MD-04/MD-05). Architectural principles frozen; mechanisms not. |
| OF-03 | Resolved architecturally via AR-04 / AA-08 INVALIDATED | **Closed as ambiguity**; becomes Contracts traceability for language mode |
| OF-04 | Confirmation via AR-06/AR-07 | **Remains open** as deletion/hygiene item (sequencing deferred) |
| OF-05 | Confirmation via AR-12 | **Remains open** as in-scope polish gap |
| OF-06 | Resolved architecturally via AR-05 / AA-12 VERIFIED | **Closed as ambiguity** |
| OF-07 | Confirmation via AR-08 | **Remains open** as Contracts gap (boundary inventory → fallbacks) |
| OF-08 | Confirmation via AR-13; approach deferred AR-14 | **Remains open** as a11y gap |
| OF-09 | Confirmation via AR-11; RT-02 retained | **Closed as ownership risk** (principle frozen); Contracts must not reassign FeedbackBundle writer |
| OF-10 | Documentation alignment / process deferral | **Remains open** (AR-17, AR-18) — non-architectural blockers for Contracts start |

---

## 4. Missing Decisions dispositions

| ID | Disposition | Outcome |
|---|---|---|
| MD-01 | **Deferral** — Domain Contracts | Cannot freeze whether new presentation contracts are required without writing those contracts. Architecture allows either pure host polish or thin presentation contracts under AR-01/AR-02. |
| MD-02 | **Confirmation by existing architecture** | Closed by AR-04 (ADR-019 language mode). |
| MD-03 | **Partial confirmation + deferral** | Not reconstituted as live hosts (AR-06). Delete-now vs later (AR-07) deferred — not inventable without implementation sequencing. |
| MD-04 | **Deferral** — Domain Contracts | Principle frozen (AR-08); error contract shape needs Contracts. |
| MD-05 | **Deferral** — Domain Contracts | Principle frozen (AR-09); raw-error policy tables need Contracts. |
| MD-06 | **Deferral** — cannot resolve without implementation knowledge | Target frozen (AR-13); Gradio conformance approach remains open. |
| MD-07 | **Confirmation by existing architecture** | Closed by AR-12 — session history loader completeness is EPIC-07 scope. |
| MD-08 | **Confirmation by existing architecture** | Closed by AR-05 — report-hosted progress only. |

---

## 5. Review Triggers dispositions

| ID | Disposition | Outcome |
|---|---|---|
| RT-01 | Retain | Formal §8.4 after Contracts + Data Model |
| RT-02 | Retain / reinforce | Mandatory before any FeedbackBuilder / shared block change (AR-11) |
| RT-03 | Retain | Deletion review when Implementation Plan sequences unwired-module removal |
| RT-04 | Retain | Post-Freeze only |
| RT-05 | Retain | Plan Correction Rule later |
| RT-06 | Retain (optional) | DOC-I-01 / language-mode wording alignment — non-blocking |
| RT-07 | Retain | EPIC-06 FR/Close process hygiene |
| RT-08 | Retain | Category B CAR Traceability at epic end |

---

## 6. Rejected options (explicit)

| Rejected claim | Reason |
|---|---|
| New ADR required now for Production UX | No genuine unresolved architectural decision beyond existing ADRs for AR-01–AR-15; contract gaps ≠ ADR gaps |
| UI locale `en`/`it` satisfies Master Plan “language mode” | Conflicts with ADR-019 session mode semantics (AA-08 INVALIDATED) |
| Standalone progress application required in EPIC-07 | Conflicts with EPIC-05 report-hosted progress architecture (AR-05) |
| Unwired views become second live host | Violates single live composition / ADR-003 clarity (AR-06) |
| EPIC-06 must close before EPIC-07 Domain Contracts | Not a Master Plan dependency (AR-15); process only |

---

## 7. Remaining open items (non-resolved)

| ID | Class | Notes |
|---|---|---|
| AA-04, AA-07, AA-13 | UNVERIFIED assumptions | Deferred (AA-05 verified at Domain Contracts) |
| OF-01, OF-02, OF-04, OF-05, OF-07, OF-08, OF-10 | Remaining findings | Contracts / process / polish gaps |
| MD-01, MD-03 (delete timing), MD-04, MD-05, MD-06 | Deferred missing decisions | Contracts or implementation knowledge |
| RT-01…RT-08 | Active triggers | As listed |
| Formal §8.4 ADR skip/confirm | Pending | After Contracts + Data Model |

---

## 8. Acceptance (this step)

| Criterion | Status |
|---|---|
| Every Discovery AA / OF / MD / RT dispositioned | YES |
| Only architectural decisions frozen | YES |
| No Domain Contracts authored | YES |
| No Data Model authored | YES |
| No Implementation Plan | YES |
| No production code / tests | YES |
| No proactive ADR | YES (ADR count = 0) |
| Unresolvable items classified as deferral | YES |

---

## 9. Recommendation

**Next engineering task:** Domain Contracts for EPIC-V13-07 — Traceability Matrix from Master Plan requirements through AR-01–AR-15 constraints; include language-mode (ADR-019), async fallback principles (AR-08/AR-09), progress report-host (AR-05), history-loader scope (AR-12), and FeedbackBundle ownership (AR-11). Do not author ADR in the next step unless Contracts drafting surfaces a genuine decision not covered by existing ADRs.

---

*Living workflow status: `EPIC-07-OVERVIEW.md`. Discovery descriptive body remains historical; assumption statuses updated to match this review.*
