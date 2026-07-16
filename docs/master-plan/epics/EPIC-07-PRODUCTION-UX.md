# EPIC-07 — Production UX: Architecture Discovery

**Status:** ARCHITECTURE DISCOVERY COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-07; Product Goal P-07  
**Playbook:** V13 Development Playbook Version 1.0 §8 Step 2 / §8.1  
**Precondition:** `EPIC-07-OVERVIEW.md` Initialization COMPLETE; HEAD at Initialization `5bd7ce4`; working tree clean  
**Authority:** Descriptive analysis only. Findings, assumptions, open issues, and review triggers. No architectural decisions. No ADR. No Domain Contracts. No Implementation Plan. No production code.

---

## 1. Executive Summary

EPIC-V13-07 hardens existing candidate-facing Gradio presentation surfaces to production quality. Discovery confirms a single live Blocks composition (`app/ui/app.py` → `UILayoutBuilder` + `UIEventOrchestrator`) covering session setup, typed question presentation, execution feedback, report delivery, replay navigation, and progress-trend (report-hosted).

No evidence was found in this Discovery pass that Production UX requires new LangGraph nodes or new persistent domain artifacts. Whether that remains true is **AA-01 (UNVERIFIED)** — not resolved here.

Material gaps for Master Plan scope include: incomplete candidate-facing fallbacks on some async boundaries; candidate-visible internal/raw error content on execution feedback paths; unwired alternate view modules; session-history loader stub; absent accessibility affordances for WCAG 2.1 AA / keyboard baseline; and ambiguity of Master Plan “language mode” vs current language dropdown.

All uncertainties are registered as Architecture Assumptions, Open Findings, or Review Triggers. None are resolved in this document.

---

## 2. Current Architecture

### 2.1 Composition / runtime UI flow

```
app/main.py
  → build_app()  (app/ui/app.py)
    → build_layout() / UILayoutBuilder.build()
    → bind_events() / UIEventOrchestrator
         ↕
    InterviewState  ←→  UIStateMachine  ←→  UIResponseBuilder  ←→  UIOutputAdapter
```

Live path is state-driven (ADR-003): UI renders from `InterviewState` / derived `UIResponse`; orchestration remains graph-owned for interview runtime. Replay is a separate entry via `ReplayEntryPoint` consuming `ReplaySession` (ADR-037). Report presentation consumes `FinalReportDTO.from_report` (ADR-033).

### 2.2 Affected subsystems

| Subsystem | Path cluster | Role in EPIC-07 |
|---|---|---|
| Layout shell | `app/ui/layout/` | Session config widgets, interview chrome, loader, report/replay/history sections |
| Event orchestration | `app/ui/bindings/` | Async start/submit/nav/export/replay wiring |
| State handlers | `app/ui/state_handlers/` | Intent → graph / export triggers |
| Response builders | `app/ui/builders/`, `app/ui/response/`, `app/ui/mappers/` | Question/feedback/loader presentation from `InterviewState` |
| Execution feedback | `app/ui/presenters/feedback/` | Candidate feedback markdown blocks (also used by runtime `feedback_node`) |
| Report presentation | `app/ui/views/report/`, `app/ui/dto/final_report_dto.py` | Deterministic HTML from `FinalReportDTO` (+ progress binder) |
| Replay presentation | `app/ui/replay/` | Read-only `ReplaySession` navigation / panels / error boundary |
| Progress | `progress_trend_panel` + `learning_progress_binder` | Longitudinal progress hosted in report |
| Unwired alternate views | `setup_view.py`, `interview_*_view.py`, `loading_utils.py`, `ErrorHintBuilder`, `ResultPresenter` | Present in tree; not referenced by live layout |

### 2.3 Ownership (current)

| Concern | Sole writer / owner (current) | Readers |
|---|---|---|
| Interview runtime computation | Graph / nodes (`reasoner_node` and direct deps per ARC-01) | UI via `InterviewState` |
| `InterviewState` live session fields | Graph + state handlers (start/submit/navigation) | UIStateMachine, UIResponseBuilder |
| `Report` | Report production path (frozen EPIC-01/05) | `FinalReportDTO.from_report` |
| `FinalReportDTO` | Factory `from_report` only | Report facade / sections / export |
| `ReplaySession` | `replay_node` / Replay Graph (frozen EPIC-03/04) | Replay UI panels |
| `LongitudinalProfile` → `LearningProgress` | Domain progress path; UI binder reads repo | `progress_trend_panel` |
| Gradio widget tree | `UILayoutBuilder` | Orchestrator bindings |
| Candidate HTML report | `ReportRenderer` + section renderers | `report_output` Gradio HTML |
| Replay HTML panels | Replay panel composers | Replay section Gradio HTML |

### 2.4 Existing runtime / async flows (candidate-facing)

| Flow | Trigger | Async? | Candidate surface today |
|---|---|---|---|
| Session start | Start button → `start_interview` | Yes (graph) | Setup widgets + global loader |
| Answer submit | Submit → submit handler → graph | Yes | Question editors + feedback + loader |
| Next / report generation | Next → navigation handler → graph | Yes | Loader; on graph exception: flags reset, **no candidate-facing error string observed** |
| Report render | Completion path → `_build_report` | Deterministic DTO→HTML | Report HTML; empty italic placeholder if absent |
| Export PDF/JSON | Download handlers | Yes (export) | `gr.Warning` on failure |
| Replay enter / nav / exit | Replay buttons → `ReplayEntryPoint` / coordinator | Enter triggers Replay Graph | Replay panels + `ReplayErrorBoundary` |
| Session history load | History dropdown / Replay from history | Intended async | Default `SessionLoader` returns `None` (stub) |
| Progress trend | Inside report build via binder | Persistence read | Insufficient-data / absent-trend copy |

### 2.5 Confirmed decisions (existing — governing ADR / constitution)

Discovery lists only already-frozen decisions. No new decisions.

| ID | Confirmed decision | Governing artifact |
|---|---|---|
| CD-01 | UI derives from `InterviewState`; UI must not own orchestration | ADR-003 |
| CD-02 | Runtime computes; projection never computes; UI is projection / intent | ARC-01 P-01; Playbook Runtime First |
| CD-03 | `Report` is sole authoritative scoring/report artifact for presentation | ADR-033; EPIC-01/05 freeze |
| CD-04 | `FinalReportDTO` sole factory is `from_report` | ADR-033; EPIC-05 |
| CD-05 | Replay UI consumes `ReplaySession`; LLM-free; read-only | ADR-037; EPIC-04 freeze |
| CD-06 | Replay has candidate-facing error boundary (no raw failure_reason) | EPIC-04 closed surface |
| CD-07 | Progress trend in report is sourced from longitudinal progress plane | EPIC-05 / binder path |
| CD-08 | Accessibility hardening for report (and related UX) deferred to EPIC-V13-07 | EPIC-01 / EPIC-05 Discovery notes |
| CD-09 | EPIC-07 Master Plan Dependencies are EPIC-04 and EPIC-05 only | Master Plan §4 / §8 |

### 2.6 Reusable components (existing)

- Live Gradio shell: `UILayoutBuilder`, `UILayoutComponents`, `UIEventOrchestrator`
- State projection: `UIStateMachine`, `UIResponseBuilder`, `UIOutputAdapter`, `UIResponse`
- Setup / interview widgets already in layout (role, seniority, language dropdown, typed displays/editors)
- Feedback pipeline blocks under `app/ui/presenters/feedback/`
- `simplify_execution_error` helper
- Report stack: `FinalReportDTO`, `ReportViewFacade`, `ReportViewModelBuilder`, `ReportRenderer`, section renderers, export handlers
- Replay stack: `ReplayEntryPoint`, `ReplayViewController`, panels, `ReplayErrorBoundary`, layout coordinator
- Progress: `bind_learning_progress`, `render_progress_trend_panel`
- Loader: `render_loader`, `LoaderStep` / `loader_mapper`, CSS spinner

---

## 3. Target Architecture (Master Plan — descriptive only)

Target is the Master Plan expected outcome, not a design selection:

- Every in-scope flow feels finished: session configuration; question presentation (written/coding/SQL); code execution feedback (test/syntax/runtime — candidate-friendly); report delivery without loading regressions on deterministic data; replay navigation; progress view.
- Every async boundary has a candidate-facing fallback.
- No placeholder states; no error surfaces exposing internal state.
- Accessibility baseline: keyboard navigation for primary flows; WCAG 2.1 AA for report and replay.

How these are achieved (mechanisms, contracts, ownership changes) is **out of scope for Discovery** and remains open (see Missing Decisions / Review Triggers).

---

## 4. Component Inventory

Live or directly relevant polish-target components. Fields describe **current** contracts. Gaps where a Master Plan requirement has no adequate consumer/fallback are noted in §6–§8 — not “solved” here.

### 4.1 Shell / orchestration

| ID | Component | Responsibility | Owner | Input data | Output | Dependencies | R/W | Domain / DTO fields consumed |
|---|---|---|---|---|---|---|---|---|
| C-01 | `UILayoutBuilder` | Builds live Gradio Blocks shell | UI layout | None (constructs widgets) | Widget tree + `gr.State` | Gradio; section renderers | Write (widget tree) | N/A (chrome) |
| C-02 | `UILayoutComponents` | Holds component references | UI layout | Builder outputs | Refs for bindings | C-01 | Read | N/A |
| C-03 | `UIEventOrchestrator` | Routes Gradio events to handlers | UI bindings | Widget events / state | Handler invocations | State handlers, validators, replay coordinator | Write (triggers) | `InterviewState` (via handlers) |
| C-04 | `UIStateMachine` | Maps runtime/replay context → `UIState` | UI state machine | `InterviewState` / replay context | `UIState` | ADR-003 | Read | `InterviewState` flags/fields |
| C-05 | `UIResponseBuilder` | Assembles `UIResponse` for all live areas | UI builders | `InterviewState`, report/replay/progress paths | `UIResponse` | Mappers, report facade, loader | Read | `InterviewState`, `FinalReportDTO`, loader fields |
| C-06 | `UIOutputAdapter` | Maps `UIResponse` → Gradio updates | UI adapters | `UIResponse` | `gr.update` map | Gradio | Read | Presentation fields on `UIResponse` |
| C-07 | Global loader (`render_loader` + CSS) | Async progress chrome | UI components / styles | `LoaderStep`, progress % | Loader HTML | `loader_mapper` | Read | `InterviewState.current_step`, `current_progress` |

### 4.2 Session configuration

| ID | Component | Responsibility | Owner | Input data | Output | Dependencies | R/W | Domain / DTO fields consumed |
|---|---|---|---|---|---|---|---|---|
| C-10 | Setup widgets (role, custom role, type, seniority, length, company, language, advanced context, Start) | Collect session config | UI layout | User input | Widget values | Gradio | Write (user) | Passed into start as primitives |
| C-11 | `InputValidator` | Enables Start when required fields present | UI bindings | Setup widget values | Interactive flag | C-10 | Read | N/A |
| C-12 | `start_interview` / start handler | Builds initial state; runs interview graph | UI state handlers | Config primitives | Updated `InterviewState` + UI updates | Graph runtime | Write / trigger | Creates/uses `InterviewState` |
| C-13 | `SetupView` (unwired) | Alternate setup view | UI views | — | — | Not bound by live layout | — | — |

**Gap note:** Master Plan names “language mode”; live UI exposes language dropdown `en`/`it` only; `LanguageProfile` has no references under `app/ui/`. Classification: OF-03 / AA-08.

### 4.3 Question presentation

| ID | Component | Responsibility | Owner | Input data | Output | Dependencies | R/W | Domain / DTO fields consumed |
|---|---|---|---|---|---|---|---|---|
| C-20 | Typed displays (`written` / `coding` / `database`) | Show question prompt / schema | UI layout + `DisplaySection` | `InterviewState` / `Question` | Markdown/HTML updates | `UIResponseBuilder` | Read | Question prompt, type-specific contract fields |
| C-21 | Typed editors | Capture candidate answer | UI layout + `editor_mapper` | User input + state | Editor values/visibility | Button/editor mappers | Write (user) | Answer fields via submit path |
| C-22 | `CounterSection` | Question i/n + attempts | UI response | `InterviewState` | Counter markdown | C-05 | Read | Question index / totals / attempts |
| C-23 | `ButtonMapper` | Submit / Retry / Next interactivity | UI response | State / quality gates | Button updates | C-05 | Read | Gating / awaiting flags |
| C-24 | `interview_*_view` modules (unwired) | Alternate typed containers | UI views | — | — | Not bound | — | — |

### 4.4 Code execution feedback

| ID | Component | Responsibility | Owner | Input data | Output | Dependencies | R/W | Domain / DTO fields consumed |
|---|---|---|---|---|---|---|---|---|
| C-30 | `FeedbackSection` | Renders feedback markdown in live UI | UI response | `state.last_feedback_bundle` | Markdown | C-05 | Read | Feedback bundle content |
| C-31 | `FeedbackBuilder` + block pipeline | Builds `FeedbackBundle` | Presenters (also runtime feedback path) | Execution / evaluation inputs | `FeedbackBundle` | Blocks below | Write (bundle production — runtime-adjacent) | `ExecutionResult`, evaluation fields |
| C-32 | `RuntimeErrorBlock` | Runtime error feedback content | Presenters | Execution error | Markdown (includes truncated traceback content) | C-31 | Read | Execution error strings |
| C-33 | `FailureBlock` / `TestBreakdownBlock` / `SuccessBlock` / others | Test/result feedback blocks | Presenters | Execution / scores | Markdown | C-31 | Read | Test counts, scores, messages |
| C-34 | `FallbackBlock` | Generic limited-feedback copy | Presenters | Missing detail | Markdown | C-31 | Read | Absence of detail |
| C-35 | `simplify_execution_error` | Shortens selected error classes | UI utils | Raw error string | Short string | Question DTO path | Read | Error string |
| C-36 | `ErrorHintBuilder` (unwired) | Retry-time hints | UI response | Execution error | Hint text (may surface raw error) | Not bound | — | — |

### 4.5 Report delivery

| ID | Component | Responsibility | Owner | Input data | Output | Dependencies | R/W | Domain / DTO fields consumed |
|---|---|---|---|---|---|---|---|---|
| C-40 | `render_report_section` | Report Gradio chrome + export + Replay entry | UI layout | — | Widgets | Gradio | Chrome | N/A |
| C-41 | `FinalReportDTO` | Sole report presentation DTO | UI DTO | `Report` | DTO | `from_report` | Read | Full Report→DTO mapping |
| C-42 | `ReportViewFacade` / `build_report_markdown` | DTO (+ progress) → HTML | UI report views | `FinalReportDTO`, optional `LearningProgress` | HTML | Renderer, binder | Read | DTO section fields |
| C-43 | `ReportViewModelBuilder` | DTO → view-model | UI report | `FinalReportDTO` | VM | C-41 | Read | DTO fields |
| C-44 | `ReportRenderer` + section renderers | Compose report HTML sections | UI report | VM | HTML | Section modules | Read | VM fields |
| C-45 | Export handlers (PDF/JSON) | Produce downloads | UI state handlers | State → DTO | Download button updates | Export services | Trigger | `FinalReportDTO` |
| C-46 | `_build_report` / `_build_completion` empty/fail copy | Placeholder / failure presentation | `UIResponseBuilder` | Missing/failed report | Italic HTML / failure copy | C-05 | Read | Presence of report |

### 4.6 Replay navigation

| ID | Component | Responsibility | Owner | Input data | Output | Dependencies | R/W | Domain / DTO fields consumed |
|---|---|---|---|---|---|---|---|---|
| C-50 | `render_replay_section` | Replay Gradio chrome | UI layout | — | Widgets | Gradio | Chrome | N/A |
| C-51 | `ReplayEntryPoint` | Load `ReplaySession`; route success/error | UI replay | Session id | Controller or error boundary | Replay Graph | Trigger / read | `ReplaySession` |
| C-52 | `ReplayViewController` | Position cursor over session | UI replay | `ReplaySession` | Current record views | ADR-037 | Read | Timeline / question records |
| C-53 | Replay panels (question, execution, scoring, coaching, summary, nav) | Read-only panel HTML | UI replay | Session fields | HTML | Composer | Read | `ReplaySession` field set |
| C-54 | `ReplayErrorBoundary` | Candidate-facing replay failure UI | UI replay | Failure class | Safe message | C-51 | Read | Mapped failure (not raw reason) |
| C-55 | `ReplayLayoutCoordinator` | Enter/nav/exit layout snapshot | UI bindings | Events + state | Layout snapshot | C-51–C-54 | Read / trigger | `InterviewState.report` session id; `ReplaySession` |
| C-56 | Session history section + `SessionLoader` | List/select prior sessions | UI layout / bindings | Loader result | Dropdown choices | Default loader returns `None` | Read (intended) | Session history identities (when wired) |

### 4.7 Progress view

| ID | Component | Responsibility | Owner | Input data | Output | Dependencies | R/W | Domain / DTO fields consumed |
|---|---|---|---|---|---|---|---|---|
| C-60 | `bind_learning_progress` | Load longitudinal progress for report | UI report binder | Candidate identity / repo | `LearningProgress` or absence | LongitudinalProfile repo, ProgressTracker | Read | `LongitudinalProfile` → `LearningProgress` |
| C-61 | `render_progress_trend_panel` | Progress trend UI inside report | UI report sections | `LearningProgress` | HTML (incl. insufficient-data) | C-42 | Read | Session count, trend fields |

### 4.8 Inventory completeness statement

All live polish-target host surfaces for Master Plan EPIC-07 flows are enumerated above. Unwired modules are listed as non-live. Domain artifact field-level consumer completeness for any **new** presentation contracts is deferred to Domain Contracts (Traceability Matrix) — Discovery does not invent those contracts.

---

## 5. Current vs Target (gap map)

| Master Plan requirement | Current observation | Gap class |
|---|---|---|
| No placeholder states | Report empty italic HTML; replay empty labels; feedback FallbackBlock; setup placeholders on inputs | OF-01 |
| No internal error surfaces | `RuntimeErrorBlock` traceback content; `simplify_execution_error` may return last raw line; navigation graph failure silent to candidate | OF-02 |
| Session configuration incl. language mode | Role/seniority/language dropdown present; language **mode** / `LanguageProfile` not in UI | OF-03 |
| Question presentation (written/coding/SQL) | Live typed displays/editors exist; alternate views unwired | OF-04 (dual surface debt) |
| Candidate-friendly execution feedback | Partial simplification; traceback/raw paths remain | OF-02 |
| Report delivery — no loading regressions on deterministic data | Loader tied to processing flags; whether report path still shows unjustified spinners | AA-05 |
| Replay navigation production quality | EPIC-04 surface exists with error boundary; empty-state labels remain | OF-01 / OF-05 |
| Progress view | Report-hosted trend panel with insufficient-data states | OF-06 (standalone vs report-hosted scope) |
| Error boundary completeness on every async boundary | Replay covered; start/submit/nav/export/history incomplete or inconsistent | OF-07 |
| Keyboard nav primary flows; WCAG 2.1 AA report+replay | No aria/keyboard/a11y affordances observed under `app/ui/` in Discovery scan | OF-08 |
| Unwired dead alternate UI modules | Present beside live layout | OF-04 / RT-03 |

---

## 6. Architecture Assumptions Register

Statuses updated by `EPIC-07-ARCHITECTURE-REVIEW.md` (Discovery Architecture Review). Remaining `UNVERIFIED` items require Domain Contracts / Data Model / formal §8.4 / process close-out — not inventable at Discovery.

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|
| AA-01 | EPIC-07 can be delivered without new persistent domain artifacts or new LangGraph nodes | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-01 | Presentation-plane polish only |
| AA-02 | Existing frozen ADRs (ADR-003, ADR-019, ADR-033, ADR-037, ARC-01, related) govern presentation boundaries without modification | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-02 | No ADR authored at Review |
| AA-03 | No new `InterviewState` fields are required for Production UX | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-03 | Default; reopen only via ADR path if Contracts prove need |
| AA-04 | Report and replay WCAG 2.1 AA + primary-flow keyboard navigation are achievable on existing host surfaces | **INVALIDATED** | EPIC-07-DATA-MODEL.md §11 | Achievability not a modelling fact; AX rows frozen; impl verification obligation |
| AA-05 | Deterministic report/replay data paths already eliminate justified loading spinners; remaining loading/error regressions are presentation-only | **VERIFIED** | EPIC-07-DOMAIN-CONTRACTS.md I-SS-02 | Deterministic no-loader rule frozen at Contracts |
| AA-06 | EPIC-04 and EPIC-05 CLOSED surfaces are the complete polish targets required by Master Plan Dependencies | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-15 | EPIC-06 not a Master Plan dependency |
| AA-07 | Conditional ADR step can be skipped | **VERIFIED** | EPIC-07-DATA-MODEL.md §13 | Formal §8.4 ADR authoring SKIP |
| AA-08 | Master Plan “language mode” is satisfied by the existing language dropdown (`en`/`it`) without a distinct language-mode control or `LanguageProfile` UI binding | **INVALIDATED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-04 | Language mode = ADR-019 session mode; locale ≠ mode |
| AA-09 | Production UX polish of execution feedback may modify presenter blocks without changing runtime sole-writer of `FeedbackBundle` | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-11 | Presentation only |
| AA-10 | Unwired alternate view modules are out-of-scope debt for EPIC-07 unless they are on a live candidate path | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-06 / AR-07 | Not reconstituted as live hosts; delete timing deferred |
| AA-11 | Session history loader stub is in-scope for EPIC-07 error-boundary / production-quality completeness | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-12 | In EPIC-07 scope |
| AA-12 | Progress view Master Plan item is fully scoped to the report-hosted trend panel (no standalone progress page) | **VERIFIED** | EPIC-07-ARCHITECTURE-REVIEW.md AR-05 | Report-hosted only |
| AA-13 | No open P0/P1 findings from prior epics block polish of EPIC-04/05 surfaces | **VERIFIED** | EPIC-07-DATA-MODEL.md §11 | No prior-epic P0/P1 alters EPIC-07 ephemeral shapes |

---

## 7. Open Findings

| ID | Finding | Class | Related |
|---|---|---|---|
| OF-01 | Placeholder / empty-state copy exists on report, replay, and feedback fallback paths | Gap | AA-05, C-46, C-53, C-34 |
| OF-02 | Candidate-visible internal/raw execution error content remains on feedback path; navigation graph failure lacks candidate-facing message | Gap / Fail-fast UX | AA-09, C-32, C-35, navigation handler |
| OF-03 | “Language mode” Master Plan term does not map 1:1 to observed UI (`LanguageProfile` unused in `app/ui/`) | Ambiguity | AA-08 |
| OF-04 | Parallel unwired view modules coexist with live layout (dual-surface / dead-code risk) | Structural debt | AA-10, RT-03 |
| OF-05 | Replay empty labels and history loader stub leave unfinished-feeling paths | Gap | AA-11, C-56 |
| OF-06 | Progress view exists only as report-hosted trend panel | Scope ambiguity | AA-12 |
| OF-07 | Async boundaries are not uniformly wrapped in candidate-facing error boundaries | Gap | AA-05, navigation/export/start/history |
| OF-08 | No accessibility (ARIA/keyboard/WCAG) affordances observed in UI scan for report/replay/primary flows | Gap | AA-04 |
| OF-09 | `FeedbackBuilder` path is runtime-adjacent; polish may touch components also used by `feedback_node` | Ownership risk | AA-09, RT-02 |
| OF-10 | DOC-I-01 / PROC-I-01 from Initialization remain open (Phase sequencing vs deps; EPIC-06 not CLOSED) | Process / docs | AA-06, AA-13 |

---

## 8. Missing Decisions (open items — not resolved)

| ID | Missing decision | Blocks |
|---|---|---|
| MD-01 | Whether any new presentation/error-boundary contracts are required vs pure HTML/copy/CSS changes on existing hosts | Domain Contracts necessity |
| MD-02 | Normative meaning of Master Plan “language mode” for EPIC-07 | AA-08 / setup scope |
| MD-03 | Whether unwired view modules are deleted, ignored, or reconstituted as live hosts | AA-10 / Deletion Is Completion |
| MD-04 | Candidate-facing error contract for graph failures on start/submit/next/report | OF-02 / OF-07 |
| MD-05 | Candidate-facing policy for execution traceback / raw error lines | OF-02 |
| MD-06 | Accessibility conformance approach under Gradio constraints for WCAG 2.1 AA | AA-04 |
| MD-07 | Whether session history loader completion is EPIC-07 vs later ops epic | AA-11 |
| MD-08 | Whether progress view requires any surface beyond report trend panel | AA-12 |

---

## 9. Risks

| ID | Risk | Likelihood | Impact | Class |
|---|---|---|---|---|
| R-01 | Scope creep into new product features under “production quality” | Medium | High | Product Before Features |
| R-02 | Feedback polish accidentally changes runtime scoring/feedback semantics | Medium | High | Single Writer / OF-09 |
| R-03 | Accessibility target infeasible on current Gradio stack without platform change | Medium | High | AA-04 |
| R-04 | EPIC-06 unfinished close-out creates report-surface churn during polish | Medium | Medium | PROC-I-01 |
| R-05 | Silent graph-failure path leaves candidates in unexplained states | High (observed) | High | OF-02 / OF-07 |
| R-06 | Dual live vs unwired views cause inconsistent fixes | Medium | Medium | OF-04 |

---

## 10. Review Triggers

| ID | Trigger | When |
|---|---|---|
| RT-01 | Architecture Review / conditional ADR | If Domain Contracts + Data Model leave a genuine unresolved decision (e.g., MD-01/MD-04/MD-06) |
| RT-02 | Ownership / Single-Writer review | Before any change to `FeedbackBuilder` / feedback blocks shared with `feedback_node` |
| RT-03 | Deletion Is Completion review | If Discovery→Contracts marks unwired modules in-scope for removal |
| RT-04 | Freeze Integrity Check | Before any frozen planning doc change after Freeze |
| RT-05 | Mini Architecture Freeze | Sequencing-only Implementation Plan corrections later (Playbook Plan Correction Rule) |
| RT-06 | Master Plan clarification | If AA-08 / DOC-I-01 require Product Master Plan text change |
| RT-07 | EPIC-06 Final Review / Epic Close | Process hygiene before or alongside EPIC-07 implementation (not Master Plan dep) |
| RT-08 | CAR Architecture Traceability | Mandatory at epic end (Category B) |

**Explicit non-trigger at this step:** No ADR creation. No Implementation Plan. No code.

---

## 11. Dependencies & constraints (inherited)

| Dependency | Status | Discovery note |
|---|---|---|
| EPIC-V13-04 | CLOSED | Replay polish target present |
| EPIC-V13-05 | CLOSED | Report polish / a11y target present |
| EPIC-V13-06 | Not CLOSED in living Overview | Report explainability fields may already be on DTO; not a Master Plan EPIC-07 dependency |
| ARC-01 / ADR-003 / ADR-033 / ADR-037 | Accepted / frozen | Confirmed decisions CD-01–CD-05 |
| Regression baseline | Not re-run | Still last recorded 6708 / 0 at EPIC-06 init — AA not created; open process note |

---

## 12. §8.1 Definition of Done checklist

| Criterion | Status |
|---|---|
| Current state vs target state analysis complete | YES (§2, §3, §5) |
| All affected subsystems identified | YES (§2.2) |
| All confirmed decisions listed with governing ADR | YES (§2.5) |
| All missing decisions listed as open items | YES (§8) |
| All risks identified and classified | YES (§9) |
| Component Inventory complete (UI-bearing) | YES (§4) |
| Architecture Assumptions Register populated (UNVERIFIED allowed) | YES (§6) — post-Review statuses applied |
| No code produced or modified | YES |

---

## 13. Recommendation (process only)

**Architecture Review:** `EPIC-07-ARCHITECTURE-REVIEW.md` — COMPLETE (Discovery disposition; formal §8.4 ADR gate remains after Contracts + Data Model).

**Next Playbook step:** Domain Contracts (`EPIC-07-DOMAIN-CONTRACTS.md`) under AR-01–AR-15; Traceability Matrix required before Freeze.

---

*Architecture Discovery is a frozen analysis artifact after acceptance of subsequent gates. Living workflow status remains in `EPIC-07-OVERVIEW.md`.*
