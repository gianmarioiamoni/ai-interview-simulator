# EPIC-07 — Production UX: Data Model Specification

**Status:** DATA MODEL COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Data Model (Playbook §8.3)  
**Precondition:** `EPIC-07-DOMAIN-CONTRACTS.md` COMPLETE; HEAD `a8b1b9d`  
**Governing:** AR-01…AR-15; EC-* contracts; ADR-003; ADR-019; ADR-033; ADR-037; ARC-01  
**Authority:** Frozen field tables, serialization model, DTO inventory, reconstruction completeness, versioning, data-model validation. No runtime algorithms. No UI behaviour. No Domain Contracts edits. No Implementation Plan. No production code.  
**Persistence:** None for EPIC-07 EC-* artifacts (AR-01).

---

## 1. Purpose and Scope

Freeze the complete data shapes for EPIC-07 presentation-plane contracts so Implementation can be mechanical.

**Models:**
- Ephemeral presentation values (EC-CF-01, EC-SS-01, EC-EX-01, EC-SC-01, EC-SH-01)
- Closed enumerations and catalogs (EC-CF-02, SurfacePhase, message keys, empty-copy keys)
- Normative accessibility requirement rows (EC-AX-01)
- Deletion-target inventory rows (EC-UH-01)
- Read-only consumption inventory of existing DTOs (no field changes)

**Non-goals:** Persistent schemas; storage migrations; algorithms; widget behaviour; Domain Contract text changes.

---

## 2. Serialization Model

| Rule ID | Rule |
|---|---|
| SM-01 | All EPIC-07 EC-* values are **ephemeral, process-local**. They are not written to disk, SQLite, `SessionHistory`, `Report`, or `ReplaySession`. |
| SM-02 | In-memory shape when implemented: immutable structured values (`frozen=True`, `extra=forbid` or equivalent). |
| SM-03 | Optional **diagnostic log serialization** (not persistence): JSON object with only safe keys — see §2.1. |
| SM-04 | No `schema_version` on EC-* values (non-stored). Document revision is this Data Model version. |
| SM-05 | Existing stored artifacts retain their ADR/epic serialization unchanged. EPIC-07 must not alter wire/storage shapes of `Report`, `FinalReportDTO`, `ReplaySession`, `LanguageProfile`, or history records. |
| SM-06 | Fail-fast at assemble time if a required catalog key is missing or an enum value is unknown. |

### 2.1 Diagnostic log payload (optional)

Allowed keys only:

| Key | Type | When |
|---|---|---|
| `boundary` | `AsyncBoundary` string | Error emission |
| `message_key` | `str` | Error emission |
| `correlation_token` | `str \| null` | Error emission |
| `surface_id` | `str` | Surface assemble |
| `phase` | `SurfacePhase` string | Surface assemble |

Forbidden in any serialization: exception type, traceback, file paths, raw `failure_reason`, internal stack frames.

---

## 3. Closed Enumerations (frozen)

### 3.1 `AsyncBoundary`

| Value | Ordinal |
|---|---|
| `SESSION_START` | 1 |
| `ANSWER_SUBMIT` | 2 |
| `NEXT_OR_REPORT` | 3 |
| `REPORT_EXPORT` | 4 |
| `REPLAY_ENTER` | 5 |
| `SESSION_HISTORY_LOAD` | 6 |

### 3.2 `SurfacePhase`

| Value |
|---|
| `LOADING` |
| `EMPTY` |
| `READY` |
| `ERROR` |

### 3.3 `ExecutionErrorKind`

| Value |
|---|
| `SYNTAX` |
| `RUNTIME` |
| `SQL` |
| `TEST_FAILURE` |
| `UNKNOWN_SAFE` |

### 3.4 `surface_id` catalog

| `surface_id` |
|---|
| `setup` |
| `question` |
| `feedback` |
| `report` |
| `replay` |
| `progress` |
| `history` |

---

## 4. Frozen Field Tables

### 4.1 `CandidateFacingError` (EC-CF-01)

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `boundary` | `AsyncBoundary` | Yes | — | Enum member |
| `message_key` | `str` | Yes | — | Must exist in §5.1 catalog |
| `message_text` | `str` | Yes | — | Non-empty; equals catalog text for `message_key` |
| `is_retryable` | `bool` | Yes | `False` | — |
| `correlation_token` | `str \| null` | No | `null` | If set: non-empty; no `.py` path segments; no `Traceback` substring |

**DM validation:** DM-V-CF-01 — `message_text` must equal catalog entry for `message_key` (single source of copy).

### 4.2 `SurfaceState` (EC-SS-01)

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `surface_id` | `str` | Yes | — | Member of §3.4 |
| `phase` | `SurfacePhase` | Yes | — | Enum member |
| `error` | `CandidateFacingError \| null` | Conditional | `null` | Required iff `phase=ERROR`; else must be `null` |
| `allows_loader` | `bool` | Yes | — | See DM-V-SS-* |
| `empty_copy_key` | `str \| null` | Conditional | `null` | Required iff `phase=EMPTY`; must exist in §5.2 |

**DM validation:**
- DM-V-SS-01: `phase=ERROR` ↔ `error != null`
- DM-V-SS-02: `phase=EMPTY` ↔ `empty_copy_key != null`
- DM-V-SS-03: `surface_id ∈ {report, replay, progress}` ∧ data-ready ⇒ `phase ≠ LOADING`
- DM-V-SS-04: `allows_loader=False` ⇒ `phase ≠ LOADING`

### 4.3 `ExecutionErrorPresentation` (EC-EX-01)

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `kind` | `ExecutionErrorKind` | Yes | — | Enum member |
| `candidate_message` | `str` | Yes | — | Non-empty; must match §5.3 for `kind` unless `TEST_FAILURE` detail override rule below |
| `detail_lines` | `tuple[str, ...]` | No | `()` | Each line: no traceback/path/exception-class patterns |
| `shows_traceback` | `bool` | Yes | `False` | **Literal `False` only** |

**DM validation:**
- DM-V-EX-01: `shows_traceback == False` always
- DM-V-EX-02: For `kind ∈ {SYNTAX, RUNTIME, SQL, UNKNOWN_SAFE}`, `candidate_message` equals §5.3 catalog
- DM-V-EX-03: For `kind=TEST_FAILURE`, `candidate_message` equals §5.3 base text; `detail_lines` may carry candidate-safe test labels only (no raw stderr dumps)

### 4.4 `SessionConfigPresentation` (EC-SC-01)

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `role` | `str` | Yes | — | Non-empty (existing role vocabulary) |
| `seniority` | `str` | Yes | — | Non-empty (existing seniority vocabulary) |
| `language_mode` | `Literal["single","mixed"]` | Yes | — | Derived rule DM-V-SC-01 |
| `enabled_languages` | `tuple[str, ...]` | Yes | — | Length ≥ 1; language ids per ADR-019 |
| `ui_locale` | `Literal["en","it"] \| null` | No | `null` | Distinct from `language_mode` |
| `interview_type` | `str` | Yes | — | Existing vocabulary |
| `interview_length` | `str` | Yes | — | Existing vocabulary |
| `company` | `str \| null` | No | `null` | — |

**DM validation:**
- DM-V-SC-01: `language_mode == "mixed"` ↔ `len(enabled_languages) > 1`
- DM-V-SC-02: `language_mode == "single"` ↔ `len(enabled_languages) == 1`
- DM-V-SC-03: Presence of `ui_locale` alone never satisfies language-mode completeness

### 4.5 `SessionHistoryItem` / `SessionHistoryListPresentation` (EC-SH-01)

**Item**

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `session_id` | `str` | Yes | — | Non-empty |
| `display_label` | `str` | Yes | — | Non-empty; candidate-safe |
| `session_date` | `str \| null` | No | `null` | If null, omit from label composition |
| `role_label` | `str \| null` | No | `null` | — |

**List**

| Field | Type | Required | Default | Validation |
|---|---|---|---|---|
| `items` | `tuple[SessionHistoryItem, ...]` | Yes | `()` | — |
| `phase` | `SurfacePhase` | Yes | — | Enum |
| `error` | `CandidateFacingError \| null` | Conditional | `null` | If ERROR: `boundary=SESSION_HISTORY_LOAD` |
| `empty_copy_key` | `str \| null` | Conditional | `null` | If EMPTY: must be `empty.history.none` |

**DM validation:**
- DM-V-SH-01: `phase=READY` ⇒ `error is null` (items may be non-empty)
- DM-V-SH-02: `phase=EMPTY` ⇒ `items == ()` ∧ `empty_copy_key == "empty.history.none"`
- DM-V-SH-03: `phase=ERROR` ⇒ `error.boundary == SESSION_HISTORY_LOAD`

### 4.6 Accessibility requirement rows (EC-AX-01)

| requirement_id | statement | applies_to_surfaces | verification_artifact_type |
|---|---|---|---|
| `AX-01` | Primary flows keyboard-operable; no keyboard trap on primary controls | `setup`, `question`, `feedback`, `report`, `replay`, `history` | Keyboard path test |
| `AX-02` | Report targets WCAG 2.1 AA | `report` | Report a11y audit/test |
| `AX-03` | Replay targets WCAG 2.1 AA | `replay` | Replay a11y audit/test |
| `AX-04` | Errors/empty/loading text perceivable (not icon-only) | all | Copy presence test |
| `AX-05` | Decorative chrome not sole meaning carrier for scores/errors | `report`, `replay` | A11y audit/test |

### 4.7 Unwired host deletion rows (EC-UH-01)

| module_path | status | may_be_live_host |
|---|---|---|
| `app/ui/views/setup_view.py` | `DELETE_TARGET` | `False` |
| `app/ui/views/interview_written_view.py` | `DELETE_TARGET` | `False` |
| `app/ui/views/interview_coding_view.py` | `DELETE_TARGET` | `False` |
| `app/ui/views/interview_database_view.py` | `DELETE_TARGET` | `False` |
| `app/ui/utils/loading_utils.py` | `DELETE_TARGET` | `False` |
| `app/ui/response/sections/error_hint_builder.py` | `DELETE_TARGET` | `False` |
| `app/ui/presenters/result_presenter.py` | `DELETE_TARGET` | `False` |

---

## 5. Copy / Message Catalogs (frozen)

### 5.1 `CandidateFacingError.message_key` catalog

| message_key | boundary | is_retryable | message_text |
|---|---|---|---|
| `err.session_start.failed` | `SESSION_START` | `True` | We could not start your interview. Please try again. |
| `err.answer_submit.failed` | `ANSWER_SUBMIT` | `True` | We could not submit your answer. Please try again. |
| `err.next_or_report.failed` | `NEXT_OR_REPORT` | `True` | Something went wrong loading the next step. Please try again. |
| `err.report_export.failed` | `REPORT_EXPORT` | `True` | Export failed. Please try again. |
| `err.replay_enter.failed` | `REPLAY_ENTER` | `True` | We could not open this replay. Please try again or choose another session. |
| `err.session_history_load.failed` | `SESSION_HISTORY_LOAD` | `True` | We could not load your session history. Please try again. |

### 5.2 Empty-state copy keys

| empty_copy_key | surface_id | message_text |
|---|---|---|
| `empty.report.unavailable` | `report` | Your report is not available for this session. |
| `empty.replay.no_questions` | `replay` | This replay has no questions to show. |
| `empty.progress.insufficient` | `progress` | Complete more sessions to see your progress trend. |
| `empty.history.none` | `history` | No previous sessions yet. |
| `empty.feedback.none` | `feedback` | No feedback is available for this answer yet. |
| `empty.question.none` | `question` | No question is available right now. |

### 5.3 Execution error base messages

| kind | candidate_message |
|---|---|
| `SYNTAX` | There is a syntax error in your code. |
| `RUNTIME` | Your code hit a runtime error. |
| `SQL` | There is a problem with your SQL. |
| `TEST_FAILURE` | Some tests did not pass. |
| `UNKNOWN_SAFE` | We could not run your code successfully. |

---

## 6. DTO Field Inventory (consumption — no shape changes)

EPIC-07 reads existing DTOs/artifacts; it does **not** add fields to them.

| Source artifact | Fields consumed by EPIC-07 polish | EPIC-07 may modify source shape? |
|---|---|---|
| `FinalReportDTO` | Existing report section fields (read-only HTML polish / a11y) | **No** |
| `ReplaySession` | Existing EPIC-04 consumed field set (read-only) | **No** |
| `LearningProgress` | Existing trend / session_count fields for progress EMPTY/READY | **No** |
| `FeedbackBundle` | Existing feedback content for display; errors via EC-EX-01 projection | **No** |
| `LanguageConfig` / `LanguageProfile` | `enabled_languages` / `session_mode` (via EC-SC-01) | **No** |
| History port records | Identity fields projected into `SessionHistoryItem` | **No** new store |
| `InterviewState` | Existing flags/fields only | **No** new fields |

**New DTO-like values introduced (ephemeral only):** `CandidateFacingError`, `SurfaceState`, `ExecutionErrorPresentation`, `SessionConfigPresentation`, `SessionHistoryListPresentation`.

---

## 7. Reconstruction Completeness

Every candidate surface/panel must reconstruct its presentation from declared sources without LLM calls and without new persistent reads beyond existing ports.

| Surface / Panel | Source fields / catalogs | Complete? |
|---|---|---|
| Setup | EC-SC-01 field table | YES |
| Question displays/editors | Existing InterviewState/Question fields + EC-SS-01 `question` | YES |
| Feedback | FeedbackBundle + EC-EX-01 + EC-SS-01 `feedback` + §5.2/§5.3 | YES |
| Report HTML | FinalReportDTO (unchanged) + EC-SS-01 `report` + §5.2 | YES |
| Progress trend | LearningProgress + EC-SS-01 `progress` + `empty.progress.insufficient` | YES |
| Replay panels | ReplaySession (EPIC-04 set) + EC-SS-01 `replay` + §5.1/§5.2 | YES |
| Replay error | EC-CF-01 / aligned ReplayErrorBoundary + §5.1 `err.replay_enter.failed` | YES |
| History | EC-SH-01 + §5.1/§5.2 | YES |
| Async failures (all boundaries) | §3.1 × §5.1 | YES |
| A11y requirements | §4.6 rows | YES (requirements complete; evidence at implementation) |
| Unwired deletion | §4.7 rows | YES |

**Gap result:** No missing source field for an in-scope surface. No speculative persistence required for completeness.

---

## 8. Traceability (Data Model ↔ Contracts ↔ Master Plan)

| DM section | Contract | Master Plan / AR refs |
|---|---|---|
| §4.1, §5.1 | EC-CF-01/02 | R-07, R-09; AR-08/AR-09 |
| §4.2, §5.2 | EC-SS-01 | R-02, R-04, R-05, R-06, R-08, R-10 |
| §4.3, §5.3 | EC-EX-01 | R-03, R-09; AR-11 |
| §4.4 | EC-SC-01 | R-01; AR-04 |
| §4.5 | EC-SH-01 | R-13; AR-12 |
| §4.6 | EC-AX-01 | R-11, R-12; AR-13 |
| §4.7 | EC-UH-01 | R-14; AR-06/AR-07 |
| §6 | Existing DTO inventory | R-15; AR-01/AR-03 |

Contracts Traceability Matrix (§7) remains authoritative for requirement→component→test mapping; this section freezes data completeness.

---

## 9. Versioning

| Item | Version rule |
|---|---|
| EPIC-07 Data Model document | `2026-07-16` / DATA MODEL COMPLETE |
| EC-* ephemeral values | No storage schema_version |
| Message catalogs §5 | Frozen; post-Freeze change ⇒ Freeze Integrity Check |
| Enums §3 | Closed; extension ⇒ Freeze Integrity Check |
| Existing persisted artifacts | Unchanged ownership of versioning |

---

## 10. Extensibility (next epics)

| Concern | Evaluation |
|---|---|
| New async boundary | Add enum member + catalog row via Freeze Integrity Check; do not silently extend |
| New surface_id | Same as above |
| i18n of message catalogs | Out of V1.3 (Master Plan non-goal); catalogs are English candidate copy |
| Persistent UX telemetry store | Out of EPIC-07; would require new ADR + persistent artifact epic |
| Standalone progress app | Forbidden by AR-05 / I-SS-05 |
| InterviewState UX flags | Forbidden by AR-03 unless ADR reopen |

---

## 11. Architecture Assumptions — final Data Model statuses

| ID | Status | Verification / Response |
|---|---|---|
| AA-01 | **VERIFIED** | §2 SM-01; no persistent EC-* |
| AA-02 | **VERIFIED** | §13 — existing ADRs sufficient |
| AA-03 | **VERIFIED** | §6 InterviewState unchanged |
| AA-04 | **INVALIDATED** | Claim “already known achievable on Gradio” is not a modelling fact. **Response:** Accessibility **requirements and verification artifact types** are frozen in §4.6; residual platform conformance is an **Implementation verification obligation**, not an open architectural decision and not an ADR trigger. |
| AA-05 | **VERIFIED** | DM-V-SS-03 / DM-V-SS-04 |
| AA-06 | **VERIFIED** | Unchanged |
| AA-07 | **VERIFIED** | §13 — formal §8.4 ADR step **SKIP** |
| AA-08 | **INVALIDATED** | Unchanged response (ADR-019 mode); encoded in DM-V-SC-* |
| AA-09 | **VERIFIED** | §4.3 / §6 FeedbackBundle |
| AA-10 | **VERIFIED** | §4.7 |
| AA-11 | **VERIFIED** | §4.5 |
| AA-12 | **VERIFIED** | progress surface only |
| AA-13 | **VERIFIED** | No prior-epic P0/P1 alters EPIC-07 ephemeral data shapes; EPIC-06 process hygiene remains non-data-model |

**UNVERIFIED remaining:** none.

Discovery register must be updated to match.

---

## 12. Open modelling questions from Domain Contracts — resolution

| OI / MD | Resolution |
|---|---|
| OI-05 message catalogs | **Resolved** — §5 frozen |
| OI-01 a11y approach | **Classified** — not modelling; Implementation verification under §4.6 (AA-04 INVALIDATED response) |
| OI-02 delete sequencing | **Deferred** — Implementation Plan (data inventory frozen in §4.7) |
| OI-03 §8.4 | **Resolved** — SKIP (§13) |
| OI-04 process docs | **Non-modelling** — remains process open issue |
| MD-01 contracts necessity | Already resolved at Contracts; Data Model confirms shapes |
| MD-04/MD-05 error contracts | **Resolved** — §4.1/§4.3/§5 |
| MD-06 Gradio approach | Same as OI-01 |

---

## 13. Formal §8.4 ADR Gate — re-evaluation

| Check | Result |
|---|---|
| Genuine unresolved architectural decision after Contracts + Data Model? | **No** |
| Existing ADRs cover language mode, UI state, report, replay, runtime/projection? | **Yes** (ADR-019, ADR-003, ADR-033, ADR-037, ARC-01) |
| New persistent artifact or InterviewState field required? | **No** |
| Architectural conflict detected? | **None** — classify none for ADR creation |
| **Gate decision** | **SKIP** formal §8.4 ADR authoring |
| Record where? | Architecture Freeze must explicitly record ADR step skipped and why (Playbook §8.4 / §8.5) |
| AA-07 | **VERIFIED** by this decision |

**Next Playbook step:** Architecture Freeze (`EPIC-07-ARCHITECTURE-FREEZE.md`) — not Implementation Plan.

---

## 14. §8.3 Definition of Done Checklist

| Criterion | Status |
|---|---|
| Open modelling questions from Domain Contracts resolved | YES §12 |
| Complete field tables frozen | YES §3–§5 |
| Replay / UI panel source completeness verified | YES §7 |
| Extensibility evaluated | YES §10 |
| All Architecture Assumptions VERIFIED or INVALIDATED | YES §11 |
| INVALIDATED entries have architectural response | YES AA-04, AA-08 |
| No runtime algorithms / UI behaviour / Domain Contract edits | YES |

---

## 15. Recommendation

**Architecture Freeze:** APPROVED — see `EPIC-07-ARCHITECTURE-FREEZE.md` (§8.4 ADR SKIP recorded).  
**Next engineering task:** Implementation Plan (`EPIC-07-IMPLEMENTATION-PLAN.md`).

---

*Data Model is a frozen specification artifact after Architecture Freeze. Living status: `EPIC-07-OVERVIEW.md`.*
