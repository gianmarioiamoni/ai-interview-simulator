# EPIC-07 — Production UX: Domain Contracts

**Status:** DOMAIN CONTRACTS COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Domain Contracts (Playbook §8.2)  
**Precondition:** `EPIC-07-PRODUCTION-UX.md` COMPLETE; `EPIC-07-ARCHITECTURE-REVIEW.md` COMPLETE; HEAD `e31e83c`  
**Governing decisions:** AR-01…AR-15; ADR-003; ADR-019; ADR-033; ADR-037; ARC-01  
**Authority:** Field-level contracts, ownership, invariants, lifecycle, relationships, Traceability Matrix. No persistence schemas. No storage models. No algorithms. No Implementation Plan. No production code.  
**ADR assessment (this step):** No additional ADR required — see §8.

---

## 1. Purpose and Scope

EPIC-07 introduces **presentation-plane contracts** that harden candidate-facing UX on existing hosts. Per AR-01, this epic does **not** introduce new LangGraph nodes or new persistent domain artifacts.

**In scope (new / changed contract surfaces):**
- Candidate-facing async error / fallback messages
- Execution-error presentation policy (candidate-safe projection)
- Surface state (loading / empty / ready / error) for in-scope flows
- Session-configuration presentation including ADR-019 language mode
- Session-history list presentation (loader completeness)
- Accessibility presentation requirements (targets; not Gradio mechanism)
- Unwired-host deletion target declaration
- Ownership constraints for FeedbackBundle presentation polish

**Out of scope:**
- Persistence / storage schemas (Data Model later if needed; AR-01 forbids new persistent artifacts)
- Implementation algorithms, Gradio widget wiring, CSS
- New `InterviewState` fields (AR-03)
- Reconstituting unwired views as live hosts (AR-06)
- Standalone progress application (AR-05)
- Formal §8.4 ADR authoring (deferred; none required by this Contracts draft)

**MD-01 resolution:** Thin presentation contracts **are required**. Pure HTML/copy changes without contracts are insufficient to satisfy AR-08/AR-09/AR-04/AR-12 and Traceability.

---

## 2. Contract Catalog

| ID | Artifact | Kind | Persistence | Writer | Readers |
|---|---|---|---|---|---|
| EC-CF-01 | `CandidateFacingError` | UI-layer immutable value | None | Boundary handler that observed the failure | Live layout error surfaces; ReplayErrorBoundary (aligned) |
| EC-CF-02 | `AsyncBoundary` | Enum (closed set) | None | N/A (catalog) | Error producers / Traceability |
| EC-SS-01 | `SurfaceState` | UI-layer immutable value | None | `UIResponseBuilder` / surface assembler | Gradio adapters / panels |
| EC-EX-01 | `ExecutionErrorPresentation` | Presentation projection rules over existing execution fields | None | Presentation projector (UI); must not write `FeedbackBundle` | Feedback markdown surfaces |
| EC-SC-01 | `SessionConfigPresentation` | UI-layer config view inputs | None | Setup widgets → start handler (intent only) | Start path; validators |
| EC-SH-01 | `SessionHistoryItem` / `SessionHistoryListPresentation` | UI-layer list projection | None | Session history loader port (read) | History dropdown / replay-from-history |
| EC-AX-01 | `AccessibilityPresentationRequirements` | Requirements contract | None | N/A (normative) | Report + Replay + primary-flow hosts |
| EC-UH-01 | `UnwiredHostDeletionTarget` | Deletion inventory | None | EPIC-07 completion hygiene | Implementation Plan / CAR |
| — | Existing: `LanguageConfig` / `LanguageProfile` | Domain/App (ADR-019) | Existing | Unchanged (not EPIC-07 writer) | Session config presentation |
| — | Existing: `FeedbackBundle` | Runtime feedback artifact | Existing | Runtime feedback path only (AR-11) | FeedbackSection (read) |
| — | Existing: `FinalReportDTO` / `ReplaySession` / `LearningProgress` | Frozen presentation sources | Existing | Unchanged | Report / Replay / Progress panels |

---

## 3. Field Specifications

### 3.1 EC-CF-01 — `CandidateFacingError`

**Responsibility:** Carry a candidate-safe failure message for one async boundary. Never carries internal exception text.

**Kind:** UI-layer immutable value (`frozen=True`, `extra=forbid` when implemented).

| Field | Type | Default | Constraints |
|---|---|---|---|
| `boundary` | `AsyncBoundary` | — | Required; must be member of EC-CF-02 |
| `message_key` | `str` | — | Required; non-empty; stable catalog key |
| `message_text` | `str` | — | Required; non-empty; candidate-facing prose |
| `is_retryable` | `bool` | `False` | Required |
| `correlation_token` | `str \| None` | `None` | Optional opaque token for support; **must not** embed stack traces or exception class names |

**Sole writer:** The boundary handler that catches/observes the failure (start / submit / next-report / export / replay-enter / history-load). Exactly one writer per emission.

**Readers:** Live error/fallback UI surfaces; must render `message_text` only (not raw exception).

**Lifecycle:** Created at failure observation → rendered once (or until next successful state replaces surface) → discarded. Not persisted. Not written to `InterviewState`, `Report`, `ReplaySession`, or `SessionHistory`.

**Validation invariants:**
- I-CF-01: `message_text` must not contain traceback markers, exception type names, or file paths.
- I-CF-02: Silent recovery without emitting `CandidateFacingError` on a failed async boundary is forbidden (AR-08).
- I-CF-03: `failure_reason` / raw exception objects must not be copied into any field.

**Versioning / serialization (contract level):** Not a stored artifact. No `schema_version`. If logged, log `boundary` + `message_key` + optional `correlation_token` only.

**Relationships:** References `AsyncBoundary`. Orthogonal to `ReplayErrorBoundary` content rules (EPIC-04); must remain consistent with AR-09.

---

### 3.2 EC-CF-02 — `AsyncBoundary` (closed enum)

**Responsibility:** Enumerate every async candidate boundary that must have a candidate-facing fallback.

| Value | Boundary | Trigger path |
|---|---|---|
| `SESSION_START` | Start interview graph | Start button |
| `ANSWER_SUBMIT` | Submit answer graph | Submit |
| `NEXT_OR_REPORT` | Next question / report generation graph | Next |
| `REPORT_EXPORT` | PDF/JSON export | Export handlers |
| `REPLAY_ENTER` | Replay Graph load | Replay entry |
| `SESSION_HISTORY_LOAD` | History list load | History section |

**Invariants:**
- I-CF-04: The enum is closed for EPIC-07. Adding a new async candidate boundary requires Contracts revision + Freeze Integrity Check (not silent extension).
- I-CF-05: Every enum member must appear in Traceability Matrix with a consuming fallback surface.

**Sole writer:** N/A (catalog). **Lifecycle:** Frozen for EPIC-07.

---

### 3.3 EC-SS-01 — `SurfaceState`

**Responsibility:** Express presentation phase of a candidate surface without implying runtime recomputation.

| Field | Type | Default | Constraints |
|---|---|---|---|
| `surface_id` | `str` | — | Required; stable id (see catalog below) |
| `phase` | `SurfacePhase` | — | Required: `LOADING` \| `EMPTY` \| `READY` \| `ERROR` |
| `error` | `CandidateFacingError \| None` | `None` | Required when `phase=ERROR`; forbidden otherwise |
| `allows_loader` | `bool` | — | Required; see invariants |

**Surface id catalog (closed for EPIC-07):**

| `surface_id` | Host |
|---|---|
| `setup` | Session configuration |
| `question` | Question presentation |
| `feedback` | Code execution / feedback |
| `report` | Report delivery |
| `replay` | Replay navigation |
| `progress` | Report-hosted progress trend |
| `history` | Session history |

**Sole writer:** Surface assembler (`UIResponseBuilder` or equivalent sole presentation assembler).  
**Readers:** Gradio adapter / panel renderers.  
**Lifecycle:** Ephemeral per UI response cycle. Not persisted.

**Validation invariants:**
- I-SS-01: `phase=LOADING` is permitted only when an async boundary for that surface is in flight (`allows_loader=True` and processing intent active).
- I-SS-02: Deterministic surfaces with data already available (`report` after `FinalReportDTO` ready; `replay` after successful `ReplaySession`; `progress` after binder result) **must not** use `phase=LOADING` (AR-05 / AA-05 contract).
- I-SS-03: `phase=EMPTY` must use finished candidate copy — no “TODO”, “placeholder”, italic internal stubs, or unfinished-feeling developer chrome (OF-01).
- I-SS-04: `phase=ERROR` requires `error: CandidateFacingError` with matching `AsyncBoundary` where applicable.
- I-SS-05: `progress` surface is report-hosted only (AR-05); no standalone `surface_id` for a separate progress app.

**Versioning / serialization:** Not stored. No schema_version.

---

### 3.4 EC-EX-01 — `ExecutionErrorPresentation`

**Responsibility:** Project existing execution/feedback inputs into candidate-safe feedback text. Does **not** own or rewrite `FeedbackBundle` production (AR-11).

**Inputs consumed (existing — not redefined):**
- Execution result fields already available to feedback presentation (status, error string, test summary fields as produced by runtime)
- `FeedbackBundle` content for read/display

**Presentation fields (output value):**

| Field | Type | Constraints |
|---|---|---|
| `kind` | `ExecutionErrorKind` | Closed: `SYNTAX` \| `RUNTIME` \| `SQL` \| `TEST_FAILURE` \| `UNKNOWN_SAFE` |
| `candidate_message` | `str` | Non-empty; candidate-safe |
| `detail_lines` | `tuple[str, ...]` | Optional; each line must satisfy I-EX-01 |
| `shows_traceback` | `bool` | **Must be `False`** |

**Sole writer (of this projection value):** UI presentation projector for feedback display.  
**Forbidden writer:** This contract must not become sole writer of `FeedbackBundle`. Runtime feedback path remains sole writer of `FeedbackBundle` (AR-11).

**Readers:** Feedback markdown surface (`FeedbackSection` / blocks acting as presentation).

**Lifecycle:** Ephemeral per feedback render. Not persisted.

**Validation invariants:**
- I-EX-01: `candidate_message` and `detail_lines` must not include traceback frames, absolute paths, or exception class names.
- I-EX-02: `shows_traceback` is always `False` for EPIC-07 (AR-09). Any presentation path that renders traceback content is a contract violation.
- I-EX-03: Mapping from raw execution error text → `kind` / `candidate_message` is presentation projection only; must not call LLM; must not alter scores.
- I-EX-04: When insufficient structured detail exists, use `kind=UNKNOWN_SAFE` with generic candidate-safe copy — never raw last-line dump of internal error text.

**Versioning / serialization:** Not stored.

**Relationships:** Reads runtime execution/feedback artifacts; writes only `ExecutionErrorPresentation` ephemeral value.

---

### 3.5 EC-SC-01 — `SessionConfigPresentation`

**Responsibility:** Candidate-facing session configuration inputs required by Master Plan (role, seniority, language mode), plus existing setup fields already on the live host.

| Field | Type | Source authority | Mandatory | Notes |
|---|---|---|---|---|
| `role` | existing role input type | Setup widgets | Yes | Existing |
| `seniority` | existing seniority input type | Setup widgets | Yes | Existing |
| `language_mode` | `Literal["single","mixed"]` | ADR-019 `LanguageConfig` / derived `LanguageProfile.session_mode` | Yes | **Not** UI locale |
| `enabled_languages` | ordered language ids per ADR-019 | `LanguageConfig.enabled_languages` | Yes | Drives mode |
| `ui_locale` | `Literal["en","it"]` \| existing locale control | Setup widgets | Optional for EPIC-07 MP | Distinct from `language_mode` (AR-04) |
| `interview_type` | existing | Setup widgets | Yes | Existing |
| `interview_length` | existing | Setup widgets | Yes | Existing |
| `company` | existing | Setup widgets | As today | Existing |

**Sole writer (of presentation values):** Candidate via setup widgets (intent).  
**Sole producer of domain `LanguageProfile`:** Existing `InterviewSetup` / ADR-019 path — **unchanged**; EPIC-07 does not re-own it.  
**Readers:** Start validator + start handler (intent → existing setup pipeline).

**Lifecycle:** Ephemeral until Start; then consumed by existing LanguageConfig→LanguageProfile resolution. Not a new persistent artifact.

**Validation invariants:**
- I-SC-01: `language_mode="mixed"` iff `len(enabled_languages) > 1` (ADR-019).
- I-SC-02: `language_mode="single"` iff `len(enabled_languages) == 1`.
- I-SC-03: Satisfying Master Plan “language mode” via `ui_locale` alone is a contract violation (AA-08 INVALIDATED / AR-04).
- I-SC-04: EPIC-07 must expose candidate-facing control(s) sufficient to set `language_mode` / `enabled_languages` consistent with ADR-019 (may reuse existing programming-language controls if they already determine mode; must not rely on locale dropdown).
- I-SC-05: No new `InterviewState` field is introduced for these values (AR-03); flow uses existing setup → graph intent path.

**Versioning / serialization:** Not a stored EPIC-07 artifact; ADR-019 artifacts retain their existing versioning.

---

### 3.6 EC-SH-01 — `SessionHistoryListPresentation`

**Responsibility:** Candidate-facing list of replayable sessions for history → replay entry (AR-12).

**Item fields:**

| Field | Type | Constraints |
|---|---|---|
| `session_id` | `str` | Required; non-empty |
| `display_label` | `str` | Required; non-empty; candidate-safe |
| `session_date` | existing date/str presentation | Optional if absent → omit, do not show “null” |
| `role_label` | `str \| None` | Optional |

**List fields:**

| Field | Type | Constraints |
|---|---|---|
| `items` | `tuple[SessionHistoryItem, ...]` | May be empty |
| `phase` | `SurfacePhase` | `LOADING` \| `EMPTY` \| `READY` \| `ERROR` |
| `error` | `CandidateFacingError \| None` | Required if `phase=ERROR`; `boundary=SESSION_HISTORY_LOAD` |

**Sole writer:** Session history loader presentation adapter (reads existing history port/repo; does not invent persistence).  
**Readers:** History dropdown / Replay-from-history controls.  
**Lifecycle:** Ephemeral list projection per load. Not a new persistent store.

**Validation invariants:**
- I-SH-01: Stub loader returning silent `None` without `EMPTY` or `ERROR` surface is forbidden.
- I-SH-02: Empty successful load → `phase=EMPTY` with finished candidate copy (not placeholder chrome).
- I-SH-03: Load failure → `phase=ERROR` + `CandidateFacingError(boundary=SESSION_HISTORY_LOAD)`.
- I-SH-04: Selecting an item yields `session_id` only to Replay entry (ADR-037 / EPIC-04); no LLM; no recompute.

**Versioning / serialization:** Not stored by EPIC-07.

---

### 3.7 EC-AX-01 — `AccessibilityPresentationRequirements`

**Responsibility:** Normative accessibility requirements at contract level (AR-13). Mechanism under Gradio remains deferred (AR-14 / AA-04 / MD-06) — **not** specified here.

| Requirement ID | Statement | Applies to |
|---|---|---|
| AX-01 | Primary flows must be operable via keyboard (no keyboard trap on primary controls) | Setup start, submit/next, report actions, replay nav, history→replay |
| AX-02 | Report HTML surface must target WCAG 2.1 AA | `report` surface |
| AX-03 | Replay HTML surface must target WCAG 2.1 AA | `replay` surface |
| AX-04 | Candidate-facing errors/empty/loading text must be perceivable with the surface (not icon-only) | All surfaces using EC-SS-01 / EC-CF-01 |
| AX-05 | Decorative chrome must not be the sole carrier of meaning for scores/errors | Report + Replay |

**Sole writer:** N/A (normative).  
**Readers:** Report/Replay/primary-flow hosts; verification tests.  
**Lifecycle:** Frozen requirements for EPIC-07.  
**Invariants:**
- I-AX-01: Non-goals exclude i18n and dark mode (Master Plan).
- I-AX-02: Conformance **approach** is out of contract scope (Data Model / Implementation may record evidence; AA-04 stays UNVERIFIED until evidence).

**Versioning:** Requirement set version for EPIC-07 is implicit document version; no stored schema.

---

### 3.8 EC-UH-01 — `UnwiredHostDeletionTarget`

**Responsibility:** Declare unwired alternate modules as deletion targets (AR-06/AR-07). Sequencing belongs to Implementation Plan; contract forbids reconstitution as live hosts.

| Field | Type | Constraints |
|---|---|---|
| `module_path` | `str` | Required |
| `status` | `Literal["DELETE_TARGET"]` | Required |
| `may_be_live_host` | `bool` | Must be `False` |

**Closed inventory (from Discovery):**
- `app/ui/views/setup_view.py`
- `app/ui/views/interview_written_view.py`
- `app/ui/views/interview_coding_view.py`
- `app/ui/views/interview_database_view.py`
- `app/ui/utils/loading_utils.py` (unwired helpers)
- `app/ui/response/sections/error_hint_builder.py`
- `app/ui/presenters/result_presenter.py`

**Invariants:**
- I-UH-01: No `DELETE_TARGET` module may be rebound as a live candidate host in EPIC-07.
- I-UH-02: Epic completion hygiene requires deletion or an explicit Freeze-approved deferral to Technical Debt with milestone (Deletion Is Completion).

**Lifecycle:** Listed at Contracts → deleted or debt-registered by Epic Close.

---

### 3.9 Existing artifact ownership constraints (unchanged writers)

| Artifact | Sole writer (unchanged) | EPIC-07 permission |
|---|---|---|
| `FeedbackBundle` | Runtime feedback path | Read + candidate-safe presentation projection only (EC-EX-01) |
| `Report` / `FinalReportDTO` | Existing report/`from_report` | Read-only presentation polish |
| `ReplaySession` | `replay_node` / Replay Graph | Read-only; EPIC-04 contracts remain |
| `LanguageProfile` | ADR-019 InterviewSetup path | Read/config intent only via EC-SC-01 |
| `LearningProgress` | Existing progress path | Read-only via report-hosted progress |
| `InterviewState` | Graph + existing handlers | **No new fields** (AR-03) |

---

## 4. Artifact Relationships

```
LanguageConfig / LanguageProfile (ADR-019)
        ↑ intent
SessionConfigPresentation (EC-SC-01)
        ↓ Start (existing)
InterviewState (unchanged shape)
        ↓
UIResponse / SurfaceState (EC-SS-01) ──┬── question / feedback
                                       ├── report (FinalReportDTO) + progress (LearningProgress)
                                       ├── replay (ReplaySession) + ReplayErrorBoundary
                                       └── history (EC-SH-01)

Async failure ──► CandidateFacingError (EC-CF-01) ──► SurfaceState.phase=ERROR

Execution fields / FeedbackBundle ──► ExecutionErrorPresentation (EC-EX-01) ──► feedback surface
```

No EPIC-07 contract writes persistent domain artifacts.

---

## 5. Lifecycle Summary

| Contract | Create | Mutate | Persist | Destroy |
|---|---|---|---|---|
| EC-CF-01 | On async failure | Immutable | No | Next successful surface replace |
| EC-SS-01 | Each UI assemble | Immutable per cycle | No | Next assemble |
| EC-EX-01 | Each feedback render needing error projection | Immutable | No | Next render |
| EC-SC-01 | Setup interaction | Widget updates until Start | No | Consumed at Start |
| EC-SH-01 | History load | Replace on reload | No | Leave history surface |
| EC-AX-01 | N/A (normative) | Frozen | No | N/A |
| EC-UH-01 | Contracts listing | Status→deleted | No | Removed from codebase |

---

## 6. Versioning & Serialization Rules (contract level)

| Rule | Statement |
|---|---|
| V-01 | EPIC-07 presentation contracts are **non-persistent**; they have no storage `schema_version`. |
| V-02 | Existing persisted artifacts (`Report`, `ReplaySession`, `LanguageProfile`, history records) retain their governing ADR/epic versioning — EPIC-07 must not alter stored shapes. |
| V-03 | If a presentation contract is ever logged, payload is limited to enum/keys/safe messages — never raw exceptions. |
| V-04 | Adding fields to EC-* contracts after Freeze requires Freeze Integrity Check. |
| V-05 | `AsyncBoundary` and `SurfacePhase` are closed enumerations for EPIC-07. |

---

## 7. Traceability Matrix

Every Master Plan EPIC-V13-07 requirement → contract field(s) → consuming component(s) → verification artifact.

| # | Master Plan Requirement | Domain Contract / Field | Consuming Component | Verification Artifact |
|---|---|---|---|---|
| R-01 | Session configuration (role, seniority, language mode) | EC-SC-01 `role`, `seniority`, `language_mode`, `enabled_languages` | C-10 setup widgets; C-11 validator; C-12 start | Test: language_mode single/mixed consistent with enabled_languages; locale alone insufficient |
| R-02 | Question presentation (written, coding, SQL) | EC-SS-01 `surface_id=question` + existing question fields via InterviewState | C-20/C-21/C-22/C-23 | Test: typed surfaces READY/EMPTY/ERROR only; no placeholder chrome |
| R-03 | Code execution feedback candidate-friendly (test/syntax/runtime) | EC-EX-01 all fields; I-EX-01…04 | C-30 FeedbackSection; presentation blocks | Architectural + unit: `shows_traceback=False`; no exception class/path in output |
| R-04 | Report delivery — no loading spinners on deterministic data | EC-SS-01 I-SS-02 for `report` | C-05/C-40–C-44 | Test: when FinalReportDTO ready and not processing → phase≠LOADING |
| R-05 | Replay navigation production quality | EC-SS-01 `replay`; existing EPIC-04 ReplaySession fields | C-50–C-55 | Test: empty/error use EC-SS/EC-CF; no unfinished labels |
| R-06 | Progress view | EC-SS-01 `progress` + existing LearningProgress | C-60/C-61 | Test: report-hosted only; insufficient-data = EMPTY finished copy |
| R-07 | Error boundary completeness (every async boundary) | EC-CF-02 all values + EC-CF-01 | Boundary handlers + error surfaces | Architectural test: each AsyncBoundary failure emits CandidateFacingError |
| R-08 | No placeholder states | EC-SS-01 I-SS-03 | All surfaces | Test/audit: forbidden placeholder patterns absent on READY/EMPTY |
| R-09 | No internal error surfaces | EC-CF-01 I-CF-01; EC-EX-01 I-EX-01/02 | Feedback + async errors | Test: traceback/raw exception not rendered |
| R-10 | No unhandled loading regressions | EC-SS-01 I-SS-01/I-SS-02 | Loader + surfaces | Test: loader only when allows_loader and in-flight |
| R-11 | Keyboard navigation primary flows | EC-AX-01 AX-01 | Primary-flow hosts | A11y test: keyboard path for primary controls |
| R-12 | WCAG 2.1 AA report and replay | EC-AX-01 AX-02/AX-03 | Report + Replay hosts | A11y audit/tests for report + replay |
| R-13 | Session history → replay usable (AR-12) | EC-SH-01 | C-56 history section | Test: EMPTY/ERROR/READY; stub silent None forbidden |
| R-14 | Sole live host; unwired not parallel | EC-UH-01 | Live layout only | Architectural test: DELETE_TARGET modules not imported by live bind path |
| R-15 | FeedbackBundle ownership preserved | §3.9 + EC-EX-01 writer rules | Runtime writer; UI reader | Architectural test: UI path does not assign FeedbackBundle writer |

**Status:** 15/15 Master Plan / Review-scoped requirements mapped. No unmet requirement under AR-01–AR-15. No dead EC-* field without consumer.

---

## 8. ADR Assessment (explicit)

| Question | Result |
|---|---|
| Does Contracts drafting require a **new** ADR? | **No** |
| Why | Language mode governed by ADR-019; UI state by ADR-003; report by ADR-033; replay by ADR-037; runtime/projection by ARC-01; presentation contracts are UI-layer non-persistent values (same class as EPIC-04 NavigationState/ReplayContext) |
| Formal §8.4 after Data Model | Still required to **confirm skip**; AA-07 remains UNVERIFIED until that gate |
| If later Contracts/Data Model conflict with AR-03 (need InterviewState field) | Stop → ADR path (AR-03 reopen) — not silent field add |

---

## 9. Architecture Assumptions — Contracts impact

| ID | Status after Contracts | Notes |
|---|---|---|
| AA-01 | **VERIFIED** (unchanged) | Reinforced: no persistent artifacts in catalog |
| AA-02 | **VERIFIED** (unchanged) | §8 — no new ADR |
| AA-03 | **VERIFIED** (unchanged) | I-SC-05; no InterviewState fields |
| AA-04 | UNVERIFIED | EC-AX-01 defines targets only; approach deferred |
| AA-05 | **VERIFIED** | I-SS-02 freezes deterministic no-loader rule |
| AA-06 | **VERIFIED** (unchanged) | |
| AA-07 | UNVERIFIED | Formal §8.4 pending Data Model |
| AA-08 | **INVALIDATED** (unchanged) | I-SC-03/04 encode response |
| AA-09 | **VERIFIED** (unchanged) | EC-EX-01 |
| AA-10 | **VERIFIED** (unchanged) | EC-UH-01 |
| AA-11 | **VERIFIED** (unchanged) | EC-SH-01 |
| AA-12 | **VERIFIED** (unchanged) | I-SS-05 |
| AA-13 | UNVERIFIED | Process |

Discovery register (`EPIC-07-PRODUCTION-UX.md` §6) must be updated to mark AA-05 **VERIFIED**.

---

## 10. Open Issues (explicit non-blockers for Contracts DoD)

| ID | Item | Class |
|---|---|---|
| OI-01 | Gradio WCAG conformance approach (MD-06 / AA-04) | Deferred — implementation knowledge / evidence |
| OI-02 | Unwired module delete sequencing order (AR-07) | Deferred — Implementation Plan |
| OI-03 | Formal §8.4 ADR skip confirmation (AA-07) | After Data Model |
| OI-04 | DOC-I-01 / PROC-I-01 | Process / docs |
| OI-05 | Exact candidate copy strings for each `message_key` | Data Model / content tables (not algorithms) |

---

## 11. §8.2 Definition of Done Checklist

| Criterion | Status |
|---|---|
| Every new or changed artifact has complete field specification | YES §3 |
| Every artifact has sole writer, readers, lifecycle | YES §2–§5 |
| Traceability Matrix complete | YES §7 (15/15) |
| No untraced (dead) field | YES |
| No unmet Master Plan requirement | YES |
| No alternatives evaluation (ADR territory) | YES |
| No persistence/storage schemas | YES |
| No implementation algorithms | YES |
| No additional ADR created | YES (§8 classified) |

---

## 12. Recommendation

**Next engineering task:** Data Model Specification (`EPIC-07-DATA-MODEL.md`) — freeze presentation field tables / message-key catalogs / surface completeness; verify AA-04 evidence plan; keep AA-07 for formal §8.4. No Implementation Plan until Architecture Freeze.

---

*Domain Contracts are frozen for field/ownership/invariant purposes once Architecture Freeze passes. Living status: `EPIC-07-OVERVIEW.md`.*
