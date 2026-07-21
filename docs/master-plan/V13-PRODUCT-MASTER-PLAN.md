# V1.3 Product Master Plan

**Status:** ACTIVE — Authoritative Roadmap  
**Date:** 2026-07-05  
**Precondition:** V1.2 RC2 frozen, stable, clean  
**Authority:** This document supersedes all prior V1.3 planning notes and governs all V1.3 development decisions.

---

## 1. V1.3 Vision

### Vision Statement

V1.3 is the production release.

V1.1 built the evaluation engine. V1.2 built the knowledge pipeline and established coaching continuity within a session. V1.3 closes the remaining gap: it connects sessions into a longitudinal narrative, makes the full knowledge history inspectable and replayable, and brings the platform to the production-quality standard required for real candidates in real interviews.

V1.3 is not an expansion of scope. It is the completion of the architecture that V1.2 established.

### Why V1.3 Is the Last Planned Release Before Production

V1.2 left three categories of known incompleteness:

1. **Scoring pipeline residue.** `InterviewEvaluation` survives as a V1.1 artifact. `Report` is not yet the sole authoritative scoring artifact. The `FinalReportDTO` still routes through `interview_evaluation`.
2. **Cross-session continuity gap.** `CandidateProfile` is session-scoped. There is no `LongitudinalProfile` that accumulates `CandidateProfileSnapshot` instances across sessions. Progress tracking exists for dimensional scores; behavioral profile continuity does not.
3. **Replay runtime is incomplete.** The contracts (`ReplayMetadata`, `ReplayFeatureEngine`, `CandidateProfileSnapshot`) exist. The `replay_node` does not.

Additionally, V1.2 deferred UX hardening, deployment configuration, and the performance baseline needed for production. V1.3 addresses all of these.

When V1.3 is complete, the platform will be:
- Architecturally self-consistent (no legacy scoring residue).
- Longitudinally continuous (cross-session profile accumulation).
- Fully replayable (session history navigable without LLM calls).
- Production-deployable (environment configuration, observability, error resilience).
- UX-complete (all user flows polished to production standard).

### Success Criteria

V1.3 is complete when:

- The scoring pipeline migration is done: `Report` is the sole authoritative scoring artifact; `InterviewEvaluation` is deleted.
- A `LongitudinalProfile` is produced after every session and queryable cross-session.
- The Replay runtime reconstructs any stored session deterministically, without LLM calls.
- The Unified Report renders all session artifacts (scores, narrative, coaching, replay link, progress trend) from a single data source.
- The platform runs without degradation under a sustained 50-session load test baseline.
- All production deployment criteria are satisfied (§7).

---

## 2. Product Goals

### P-01 — Complete the Scoring Pipeline Migration

Retire `InterviewEvaluation`. Extend `Report` to be the sole authoritative artifact for all scoring data. Update `FinalReportDTO` and all presentation consumers to read from `Report` only. This is not a new feature — it is the completion of a migration that V1.2 deliberately deferred.

### P-02 — Cross-Session Profile Continuity

Define and implement `LongitudinalProfile` — the persistent, cross-session accumulation of `CandidateProfileSnapshot` instances. Establish who owns it, when it is updated, and where it is stored. Enable progress tracking to be driven by behavioral profile trends, not only dimensional score trends.

### P-03 — Replay Engine

Implement `replay_node` as a closed, non-LLM reconstruction pipeline. The node consumes a `SessionHistory` and produces a `CandidateProfile` deterministically from stored features. The Replay UI navigates the reconstructed session without any live computation.

### P-04 — Replay UI Experience

Build the candidate-facing session replay interface. Question-by-question navigation. Answer display. Score display. Coaching note display. No re-submission. No LLM calls from the UI.

### P-05 — Unified Report

Produce a single, cohesive session report that renders all artifacts — dimensional scores, behavioral profile, narrative coaching, study recommendations, session metadata, and a link to replay — from `Report` alone. No dual reads from `Report` and `SessionHistory`.

### P-06 — Explainability

Make every coaching assertion traceable to its evidence source. Every `NarrativeInsight` must surface its `Observation` anchor in the report UI. Every `CoachingAction` must surface its `KnowledgeGap` origin. Candidates should be able to ask "why was this said?" and receive a direct answer grounded in their session data.

### P-07 — Production UX

Polish every user-facing flow to production quality. Session configuration, question presentation, answer submission, code execution feedback, report delivery, replay navigation, and progress views must all meet a production UX standard. Eliminate all placeholder states, loading regressions, and error surfaces that expose internal state to the candidate.

### P-08 — Deployment & Operations

Define and implement the production deployment configuration. Environment-parameterised settings, structured logging, health endpoints, observability hooks, and graceful shutdown. The platform must be deployable to a production environment with documented operational runbooks.

### P-09 — Performance & Scalability Baseline

Establish and verify the performance baseline required for production launch. Define SLOs for session latency, report generation time, and replay load. Run load tests. Document bottlenecks. Address any P0 performance issues before the release gate.

### P-10 — Final Architecture Cleanup

Complete the technical debt register deferred from V1.2 RC2. Enforce all new PATs established by V1.2 (Cascading Closure, Projection Artifact, Runtime First / Projection Later, Sole-Writer Node, Reconstruction Completeness). Retire all `deprecated` fields and dead code. Ensure the codebase enters production with zero known architectural violations.

---

## 3. Guiding Principles

V1.3 operates under the same architectural constitution established in `ARC-01-ARCHITECTURE-CONSTITUTION.md`. The following principles are directly operative in V1.3 work and must be consulted before any design decision.

### From the Architecture Constitution

**P-01 — The Runtime Computes; Projection Never Computes.**  
The computation/projection boundary is constitutionally protected. All V1.3 work must preserve it. The `replay_node` is the sole controlled exception — a closed recomputation under explicit flag, not a live session computation.

**P-02 — Single Ownership.**  
The scoring pipeline migration must follow this principle strictly. The transition from `InterviewEvaluation` to `Report` must disable the old artifact in the same migration increment as the new one is activated. No parallel production paths.

**P-03 — Immutable Domain Contracts.**  
`LongitudinalProfile`, `ReplaySession`, and any new V1.3 artifacts must be `frozen=True` with single builders.

**P-04 — LangGraph Is the Sole Runtime Orchestrator.**  
`replay_node` and any V1.3 nodes must be LangGraph nodes. No coordinator objects, no service chains, no sequential runners outside the graph.

**P-05 — Builders Assemble; Engines Compute.**  
The `LongitudinalProfileBuilder` assembles snapshots. The `ReplayEngine` computes reconstruction. These responsibilities must not be mixed.

### From the Retrospective

The following lessons from `V1.2-ARCHITECTURE-RETROSPECTIVE.md` are directly binding on V1.3:

- **No parallel production paths.** The V1.2 dual-path mistake must not recur. Every migration activates the new path as the sole path, behind a feature flag if necessary, while disabling the legacy path immediately.
- **No temporary bridges.** If a bridge is needed, it must have a hard deletion date declared at creation and no more than one consumer.
- **No silent fallbacks.** Every conditional path that changes behavior without an observable error is prohibited. Fail-fast with `RuntimeError` is the default.
- **Deletion is migration completion.** A migration is not done until the legacy artifact is deleted. Deprecation without deletion is not a migration milestone.
- **Declare the computation/projection boundary before the first increment.** V1.3 must not repeat the seven-increment reversal that V1.2 required to move computation out of session close.

### From the Pattern Freeze

All six PATs in `V1.2-PATTERN-FREEZE.md` are in effect. The four emerging patterns documented in the retrospective (Cascading Closure, Projection Artifact, Runtime First / Projection Later, Sole-Writer Node) must be formally registered as PATs before the first V1.3 migration increment.

The Reconstruction Completeness PAT must be declared and enforced for all V1.3 immutable object reconstruction paths.

---

## 4. Major Epics

---

### EPIC-V13-01 — Scoring Pipeline Migration

**Purpose:**  
Complete the V1.2 RC3-deferred migration: retire `InterviewEvaluation` as a routing and presentation artifact. Make `Report` the sole authoritative source of scoring data for the presentation layer.

**Scope:**  
Extend `ReportBuilder` to accept and embed scoring dimensions currently held in `InterviewEvaluation`. Update `FinalReportDTO` to read exclusively from `Report`. Update all `UIStateMachine` routing conditions that reference `interview_evaluation`. Delete `InterviewEvaluation` and all its construction paths once the migration is complete. Remove the `report_output: str | None` dead field from `InterviewState` (**done** — field absent; EPIC-V13-10 CLN-07 docs certification).

**Expected Outcome:**  
`Report` is the single artifact consumed by all presentation consumers. `InterviewEvaluation` does not exist in the codebase. `InterviewState` contains no dead fields from V1.1. The scoring pipeline is architecturally self-consistent with the V1.2 Constitution.

**Dependencies:**  
V1.2 `Report` contract (complete). V1.2 `ReportBuilder` (complete). V1.2 `SessionHistory` persistence (complete).

**Non-Goals:**  
Changing scoring logic, dimension weights, or calibration constants. This is a migration, not a scoring redesign.

---

### EPIC-V13-02 — Cross-Session Profile Continuity

**Purpose:**  
Define and implement `LongitudinalProfile` — the persistent, cross-session accumulation of `CandidateProfileSnapshot` instances that enables behavioral profile tracking across sessions.

**Scope:**  
Define the `LongitudinalProfile` domain contract, its ownership model, its storage schema, and the trigger for its update (on session completion). Establish the relationship between `LongitudinalProfile` and `CandidateIdentity`. Extend `ProgressTracker` to derive `LearningProgress` from both dimensional scores and behavioral profile trends. Define the cross-session `ObservationStore` accumulation policy for V1.3 (Observations were session-scoped in V1.2; this epic makes the persistence boundary explicit).

**Expected Outcome:**  
After every session, a `LongitudinalProfile` is updated with the new `CandidateProfileSnapshot`. Progress tracking reflects behavioral feature trends, not only dimensional scores. The `LanguageCapability` reserved concept (defined in V1.2 domain freeze) is activated for cross-session accumulation.

**Dependencies:**  
EPIC-V13-01 (scoring pipeline clean — `Report` is authoritative before longitudinal profile accumulates report-derived artifacts). V1.2 `CandidateProfileSnapshot` (complete). V1.2 `SessionHistory` persistence (complete). V1.2 `CandidateIdentity` schema (defined; not yet active as cross-session anchor).

**Non-Goals:**  
Cohort-level benchmarking (`PeerBenchmark` is V2). Organisation-level profiles (`OrganisationProfile` is V2). Authentication or candidate identity federation (V2). Goal tracking (`GoalTrack` may be addressed if effort allows but is not a V1.3 commitment).

---

### EPIC-V13-03 — Replay Engine

**Purpose:**  
Implement `replay_node` as a closed, deterministic session reconstruction pipeline that consumes a `SessionHistory` and produces a navigable session view without any LLM calls.

**Scope:**  
Implement `replay_node` following the Cascading Closure PAT: it is a non-fatal, write-once node. Define `ReplaySession` as the output artifact of `replay_node`. The node reads `SessionHistory.transcript` and stored features; it does not invoke `KnowledgePipeline`, `FeatureEngine`, or any LLM-backed service. The `ReplayFeatureEngine` contracts defined in V1.2 must be activated and integrated. Validate that domain invariant I-11 ("Replay never invokes LLM calls") is enforced by architectural test.

**Expected Outcome:**  
Any stored `SessionHistory` can be reconstructed into a `ReplaySession` deterministically. The reconstruction is idempotent. The replay pipeline is independently testable. The output is the sole input for the Replay UI.

**Dependencies:**  
EPIC-V13-01 (scoring pipeline migrated — `ReplaySession` must read from `Report`-consistent data). V1.2 `ReplayMetadata`, `ReplayFeatureEngine`, `CandidateProfileSnapshot` contracts (complete). V1.2 `SessionHistory` persistence (complete).

**Non-Goals:**  
Re-submission of answers in replay mode. Comparative replay (comparing two sessions side by side). AI commentary during replay. These are V2+ features.

---

### EPIC-V13-04 — Replay UI Experience

**Purpose:**  
Build the candidate-facing session replay interface backed by `ReplaySession`.

**Scope:**  
Question-by-question navigation with forward and backward controls. Display of question, candidate answer, execution result (for coding questions), dimensional scores, and coaching notes per question. Session-level summary panel. Navigation progress indicator. No re-submission controls. No LLM calls from any UI component. Responsive layout (mobile, tablet, desktop).

**Expected Outcome:**  
Candidates can navigate any stored session in full detail. Every score and coaching note is visible. The experience is read-only and deterministic. The UI is production-quality.

**Dependencies:**  
EPIC-V13-03 (Replay Engine complete — UI consumes `ReplaySession`).

**Non-Goals:**  
Side-by-side session comparison. Annotation or bookmarking. Sharing or exporting replay. These are V2 UX extensions.

---

### EPIC-V13-05 — Unified Report

**Purpose:**  
Produce a single, cohesive session report that renders all session artifacts from `Report` as the sole data source, eliminating dual reads and legacy routing.

**Scope:**  
Audit and consolidate all report rendering paths. Ensure `FinalReportDTO` (post-EPIC-V13-01) is the sole consumer API for report data. Add a replay entry point in the report (link to `ReplaySession`). Add a progress trend panel sourced from `LongitudinalProfile` (post-EPIC-V13-02). Validate that no report section reads from `SessionHistory` directly when the data is available in `Report`. The Unified Report shall expose stable report surfaces (narrative, coaching, and related DTO fields) consumed later by EPIC-V13-06; explainability implementation remains owned exclusively by EPIC-V13-06.

**Expected Outcome:**  
One data source. One report. Every report section is traceable to `Report` fields. The Unified Report is the primary deliverable of every completed session.

**Dependencies:**  
EPIC-V13-01 (scoring pipeline). EPIC-V13-02 (longitudinal profile for trend panel). EPIC-V13-03 (replay link).

**Non-Goals:**  
PDF export, email delivery, or sharing. These are V2 distribution concerns. Explainability anchors, evidence-panel UX, and coaching origin surfacing are owned by EPIC-V13-06 — not implemented in EPIC-V13-05.

---

### EPIC-V13-06 — Explainability

**Status:** CAR COMPLETE — PASS WITH OBSERVATIONS (0 P0/P1); Final Review AUTHORIZED — 2026-07-22  

**Purpose:**  
Make every coaching assertion traceable to its evidence source, surfaced in the report UI.

**Scope:**  
Every `NarrativeInsight` must render its `Observation` anchor in the report (domain invariant I-15 must be visible to the candidate, not only enforced internally). Every `CoachingAction` must render its `KnowledgeGap` origin. Design the UI affordance (expandable evidence panel, inline anchor reference, or tooltip — decision deferred to UX design phase). Validate that all `NarrativeInsight` objects carry valid `evidence_anchor` references before the report is rendered; fail gracefully if an insight has no anchor.

**Expected Outcome:**  
Candidates can trace every piece of coaching advice back to a specific observation in their session. The platform is explainable by design, not by documentation.

**Dependencies:**  
EPIC-V13-05 (Unified Report — explainability is a report section, not a standalone feature). EPIC-V13-01 (clean scoring data).

**Non-Goals:**  
AI-generated explanations of explanations. Natural language "why" query interface (V2+). Audit trails for enterprise compliance (V2).

---

### EPIC-V13-07 — Production UX

**Status:** CLOSED — 2026-07-17  

**Purpose:**  
Bring every user-facing flow to production quality: no placeholder states, no error surfaces that expose internal state, no unhandled loading regressions.

**Scope:**  
Session configuration flow (role, seniority, language mode). Question presentation (written, coding, SQL). Code execution feedback (test results, syntax errors, runtime errors — all candidate-friendly). Report delivery flow (no loading spinners on deterministic data). Replay navigation. Progress view. Error boundary completeness (every async boundary has a candidate-facing fallback). Accessibility baseline (keyboard navigation for primary flows, WCAG 2.1 AA target for report and replay).

**Expected Outcome:**  
A candidate who has never used the platform can complete a session, receive a report, and navigate replay without encountering any state that feels unfinished or internal.

**Dependencies:**  
EPIC-V13-04 (Replay UI). EPIC-V13-05 (Unified Report).

**Non-Goals:**  
Onboarding tours, tooltips, or help overlays (nice-to-have, not blocking). Internationalisation (V2). Dark mode (V2 UX concern).

---

### EPIC-V13-08 — Deployment & Operations

**Status:** CLOSED WITH OBSERVATIONS — 2026-07-20  

**Purpose:**  
Define and implement the production deployment configuration, observability infrastructure, and operational runbooks.

**Scope:**  
Environment-parameterised configuration (`settings.py` fully environment-driven; no hardcoded paths or API keys). Structured logging (every node emits structured log events with session_id, node name, duration, and outcome). Health endpoint (readiness check for LLM connectivity, database connectivity, execution sandbox). Graceful shutdown (in-flight sessions handled on SIGTERM). LLM call observability (per-call token usage, latency, model tier — already partially implemented in V1.2 cost telemetry). Deployment runbook (local, staging, production). Database migration runbook (SQLite schema versioning policy from V1.2 extended).

**Expected Outcome:**  
The platform can be deployed to a production environment with zero manual configuration. An operator can diagnose a session failure from logs alone. The health endpoint gates deployment in CI.

**Dependencies:**  
EPIC-V13-01 (no legacy artifacts in the deployment artifact). EPIC-V13-10 (architecture cleanup — no dead code in the deployed build).

**Non-Goals:**  
Container orchestration (Kubernetes, ECS). Autoscaling. Multi-region deployment. These are V2 infrastructure concerns. SaaS billing and subscription management are V2.

---

### EPIC-V13-09 — Performance & Scalability Baseline

**Status:** CLOSED — 2026-07-21  

**Purpose:**  
Establish and verify the performance baseline required for production, and resolve any P0 bottlenecks before the release gate.

**Scope:**  
Define SLOs: session question latency (P99 < 8s end-to-end for a written question evaluation cycle), report generation time (< 3s from session close), replay load time (< 1s for any stored session), database read latency (< 100ms for any `SessionHistory` query). Run load test: 50 consecutive sessions, no degradation. Profile `reasoner_node` for the highest-latency path. Profile `KnowledgePipeline` for cross-session profile update cost. Document bottlenecks. Address P0 issues (those that violate SLOs under baseline load). Defer P1/P2 optimisations to V2.

**Expected Outcome:**  
The platform meets its defined SLOs under baseline load. All P0 performance issues are resolved. A performance baseline report is available as a release artifact.

**Dependencies:**  
EPIC-V13-01 (clean pipeline — no legacy overhead). EPIC-V13-03 (replay engine — replay must meet load SLO). EPIC-V13-08 (structured logging — required for latency measurement).

**Non-Goals:**  
Horizontal scaling. Distributed caching (Redis). CDN configuration. Query optimisation beyond the SQLite baseline. These are V2 performance concerns.

---

### EPIC-V13-10 — Final Architecture Cleanup

**Status:** **CLOSED WITH OBSERVATIONS** (0 P0/P1) — 2026-07-21  


**Purpose:**  
Complete the V1.2 technical debt register and enforce all V1.3 PAT requirements, leaving the codebase in a state suitable for long-term production maintenance.

**Scope:**  
Formalize the four emerging PATs from the V1.2 retrospective as official registered patterns (Cascading Closure, Projection Artifact, Runtime First / Projection Later, Sole-Writer Node). Declare and enforce the Reconstruction Completeness PAT. Audit every `deprecated` annotation and either delete the artifact or promote it. Audit every field in `InterviewState` for declared sole writer and declared readers (per the V1.2 retrospective lesson). Enforce PAT-06 corollary: services may not call other services in a way that implements routing logic. Retire any dead test infrastructure from V1.2 migration scaffolding.

**Expected Outcome:**  
Zero known architectural violations. Zero `deprecated` artifacts without a deletion milestone. Zero `InterviewState` fields without a declared owner. All six original PATs and five new PATs are registered, named, and enforced by architectural tests where possible.

**Dependencies:**  
EPIC-V13-01 (scoring pipeline migration complete before architecture audit can close the scoring residue findings).

**Non-Goals:**  
New feature implementation. Test coverage expansion beyond architectural enforcement. Performance optimisation. These are addressed by their respective epics.

---

## 5. Go-Live Checklist

The following must be true before V1.3 is declared complete.

### Architecture

- [ ] `InterviewEvaluation` deleted from codebase. No reference to it remains in any production path.
- [x] `report_output: str | None` dead field removed from `InterviewState`. *(certified EPIC-V13-10 P6 / CLN-07 — not present on `InterviewState`; UI HTML `report_output` surface is unrelated)*
- [ ] `Report` is the sole authoritative scoring artifact consumed by all presentation consumers.
- [ ] `LongitudinalProfile` is produced and persisted after every session completion.
- [ ] `replay_node` is implemented, non-fatal, write-once, and LLM-free.
- [ ] Domain invariant I-11 ("Replay never invokes LLM calls") is enforced by an architectural test.
- [x] All four emerging PATs from the V1.2 retrospective are formally registered. *(EPIC-V13-10 — INDEX Official Patterns OP-01…04 + P-08; dual PAT/OP namespaces)*
- [x] Reconstruction Completeness PAT is declared and all reconstruction paths are audited. *(EPIC-V13-10 — ARC-01 P-08; AT-06)*
- [x] Zero `InterviewState` fields without a declared sole writer. *(EPIC-V13-10 — Ownership Matrix 43/43; AT-01; authorized writer sets)*
- [x] Zero deprecated artifacts without a deletion milestone. *(EPIC-V13-10 — stubs deleted; `TD-EP10-001` dual-model residual registered with deferred redesign milestone)*

### Product

- [ ] Unified Report renders all session artifacts from `Report` as the sole data source.
- [ ] Every `NarrativeInsight` surfaces its evidence anchor in the report UI.
- [ ] Every `CoachingAction` surfaces its `KnowledgeGap` origin in the report UI.
- [ ] Replay UI navigates any stored session question-by-question with correct data.
- [ ] Progress view reflects behavioral profile trends (from `LongitudinalProfile`), not only dimensional scores.
- [ ] All primary user flows are production-quality with no placeholder states or internal error surfaces.
- [ ] Accessibility: keyboard navigation for primary flows; WCAG 2.1 AA for report and replay.

### Engineering

- [ ] All defined SLOs met under 50-session load test.
- [ ] Structured logging: every node emits structured events with session_id, node name, duration, outcome.
- [ ] Health endpoint active and used as CI deployment gate.
- [ ] Environment-parameterised configuration: no hardcoded paths, keys, or environment assumptions.
- [ ] Graceful shutdown verified under SIGTERM.
- [ ] Database migration runbook documented and tested.

### Testing

- [ ] All V1.2 acceptance criteria continue to pass (full regression).
- [ ] `replay_node` reconstructs stored sessions deterministically across 20 test fixtures.
- [ ] Scoring pipeline migration: 100% of report presentation tests read from `Report`, zero from `InterviewEvaluation`.
- [ ] `LongitudinalProfile` accumulates correctly across synthetic 10-session dataset.
- [ ] Total test suite ≥ 2,500 passing tests.
- [ ] Zero P0/P1 open issues at release gate.

### Documentation

- [ ] All V1.3 ADRs authored, reviewed, and merged.
- [ ] Deployment runbook complete and reviewed.
- [ ] Performance baseline report published as a release artifact.
- [ ] Architecture Constitution updated to reflect any V1.3 amendments.
- [ ] Pattern registry updated with all new PATs.

### Release

- [ ] V1.3 release tag created with changelog.
- [ ] All V1.2 features regression-verified at release gate.
- [ ] Performance baseline report attached to release.

---

## 6. Deferred Features

The following are intentionally out of V1.3 scope. This list exists to prevent scope creep.

| Feature | Target | Reason |
|---|---|---|
| REST API public surface | V2 | Requires auth layer, multi-tenant infra, API versioning |
| Enterprise Analytics dashboard | V2 | Requires PostgreSQL + organisation model |
| Multi-modal input (video, screen share) | V2 | Infrastructure investment exceeds V1.3 scope |
| SaaS subscription / billing | V2 | Business model concern |
| Peer benchmarking | V2 | Requires cohort data volume |
| `CandidateIdentity` federation | V2 | Requires authentication layer |
| `OrganisationProfile` | V2 | Requires multi-tenant architecture |
| `LiveCoachingEvent` | V2 | Requires real-time streaming |
| Evaluated follow-up (ADR-010 Model B) | Deferred indefinitely | Model complexity vs. session quality trade-off unresolved |
| Framework-level coding questions | Beyond V1.x | Requires container-based execution environment |
| Multi-file coding projects | Beyond V1.x | Breaks sandbox isolation model |
| PDF export / email delivery | V2 | Distribution infrastructure concern |
| Side-by-side session comparison | V2 | UX complexity; requires cohort context |
| AI-generated "why" query interface | V2+ | Requires conversational retrieval layer |
| Dark mode | V2 UX | Not blocking for production launch |
| Internationalisation | V2 | Scope exceeds V1.3 |
| `GoalTrack` | V1.3 stretch / V2 | Not blocking; activatable if effort allows |
| Container orchestration / autoscaling | V2 infrastructure | Beyond single-instance baseline scope |

---

## 7. Risks

### Technical Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Scoring pipeline migration scope expands (ReportBuilder redesign grows complex) | Medium | Bound the migration to field-level extension; do not redesign `ReportBuilder` interface; use TCP pattern strictly |
| `LongitudinalProfile` ownership decision is contentious (who writes it, when) | Medium | Resolve with a dedicated ADR before implementation begins; do not proceed without written decision |
| Replay reconstruction produces non-deterministic output (stored features are ambiguous) | Low | Require explicit field-level declaration for every `ReplaySession` reconstruction path (Reconstruction Completeness PAT) |
| New PAT declarations create friction with existing code that was written before the PATs were formal | Medium | Treat PAT activation as a cleanup sprint, not a blocker for feature work; log violations for EPIC-V13-10 |
| Performance SLOs are not met and require architectural changes not scoped in V1.3 | Low | Run preliminary load test in EPIC-V13-09 early; escalate P0 findings immediately; do not defer performance to post-release |
| `CandidateIdentity` schema collision with V2 auth requirements | Low | Design `CandidateIdentity` to be nullable/anonymous in V1.3; document the V2 migration path explicitly in ADR |

### Product Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Explainability evidence anchors are sparse (many insights have weak or missing anchors) | Medium | Validate anchor coverage across 20 test sessions before Explainability epic ships; do not ship with silent anchor suppression |
| Unified Report complexity degrades perceived report quality | Medium | User-test report layout with real session data before shipping; validate that consolidation does not reduce readability |
| Replay UI performance is unacceptable for long sessions (20+ questions) | Low | Profile replay rendering with a 20-question session fixture during EPIC-V13-04; address before shipping |
| Progress view misleads candidates when `LongitudinalProfile` has fewer than 3 sessions | Medium | Show explicit "insufficient data" state for < 3 sessions; never extrapolate trends from a single session |

### Maintenance Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| V1.2 test suite becomes brittle as scoring pipeline migration progresses | Medium | Run V1.2 regression in CI on every EPIC-V13-01 increment; fix regressions immediately, not at the epic boundary |
| Architecture Constitution amendments accumulate without formal review | Low | Require an architectural review before any V1.3 ADR that proposes an exception to a constitutional principle |
| `LongitudinalProfile` schema versioning policy is not established early enough, causing migration cost later | Medium | Declare the schema versioning policy in the first `LongitudinalProfile` ADR; do not ship without it |

---

## 8. Roadmap

Epics are sequenced by dependency and risk. No sprint planning is implied.

### Phase 1 — Foundation (prerequisite for all other epics)

**Architecture Governance (EPIC-V13-10 — governance phase)**  
Phase 1 begins with the architectural governance work required to support the remaining V1.3 implementation. This work precedes the first migration increment and may include: evaluation of proposed PATs against the existing pattern registry; authoring of new ADRs for any V1.3 design decisions not yet formally documented; targeted amendments to the Architecture Constitution where V1.3 introduces genuinely new concerns; and clarification of existing architectural rules where ambiguity has been identified. Proposed PATs and ADRs follow the normal governance process — no pattern or decision becomes official until it has completed that process. This is not the full EPIC-V13-10 cleanup — that audit runs throughout V1.3 and closes at Phase 5.

**EPIC-V13-01 (Scoring Pipeline Migration)**  
The highest-dependency epic. Everything downstream of the scoring pipeline depends on `Report` being authoritative. This must be completed and validated before EPIC-V13-05 (Unified Report) and before any replay or longitudinal artifacts accumulate scoring data.

### Phase 2 — Core Domain (after Phase 1 complete)

**EPIC-V13-02 (Cross-Session Profile Continuity)**  
Depends on clean scoring data (EPIC-V13-01). Can run in parallel with EPIC-V13-03.

**EPIC-V13-03 (Replay Engine)**  
Depends on EPIC-V13-01 (replay must read from `Report`-consistent data). Can run in parallel with EPIC-V13-02.

### Phase 3 — User Experience (after Phase 2 complete)

**EPIC-V13-04 (Replay UI Experience)**  
Depends on EPIC-V13-03 (Replay Engine).

**EPIC-V13-05 (Unified Report)**  
Depends on EPIC-V13-01, EPIC-V13-02, EPIC-V13-03. Does not depend on EPIC-V13-06.

**EPIC-V13-06 (Explainability)** — **CAR COMPLETE — PASS WITH OBSERVATIONS**; Final Review AUTHORIZED (2026-07-22)  
Depends on EPIC-V13-05 (Unified Report host surfaces) and EPIC-V13-01 (clean scoring data). Implementation complete (C1–C8, C10). Living Overview: `docs/master-plan/epics/EPIC-06-OVERVIEW.md`. Next: Final Review → Epic Close.

### Phase 4 — Production Readiness (after Phase 3 complete)

**EPIC-V13-07 (Production UX)** — **CLOSED** (2026-07-17)  
Depends on EPIC-V13-04 and EPIC-V13-05 being feature-complete.

**EPIC-V13-08 (Deployment & Operations)** — **CLOSED WITH OBSERVATIONS** (2026-07-20)  
Can begin environment configuration work in parallel with Phase 2; health endpoint and graceful shutdown require feature stability from Phase 3.

**EPIC-V13-09 (Performance & Scalability Baseline)** — **CLOSED** (2026-07-21)
Preliminary profiling can begin in Phase 2. Full load test and SLO validation require Phase 3 feature completeness. SLO-D (SessionHistory DB read) dispositioned N/A for V1.3 per Architecture Freeze. Baseline report published; P0-ABSENT under stub-LLM load.

### Phase 5 — Release Gate

**EPIC-V13-10 (Final Architecture Cleanup — full audit)** — **CLOSED WITH OBSERVATIONS** (2026-07-21)  
Final audit pass complete. Ownership Matrix, PAT/OP registry, dead-code purity, and AT-01…07 gates certified. Living Overview: `docs/master-plan/epics/EPIC-10-OVERVIEW.md`. Non-blocking carry-forward: `TD-EP10-001`, `TD-EP10-002`.

**V1.3 Release**

---

## 9. Success Metrics

The following indicators will be verified during the V1.3 Release Readiness Review. They are objective signals of platform quality and architectural integrity, not implementation tasks.

| Metric | Target |
|---|---|
| Architecture score | ≥ 9.5 |
| Maintainability score | ≥ 9.5 |
| Automated regression suite | 100% passing |
| Duplicated runtime computation | Zero instances |
| Parallel production paths | Zero instances |
| Replay determinism | Fully deterministic across all stored sessions |
| Explainability coverage | Every adaptive coaching decision has a surfaced evidence anchor |
| Report consolidation | Unified Report is the sole production report artifact; no secondary report path exists |
| Production deployment | Successfully validated in a production-equivalent environment |
| Documentation alignment | All documentation verified to be aligned with final implementation |

These metrics are evaluated as a whole at the release gate. A V1.3 release is not declared until all indicators are satisfied.

---

## 10. Definition of Done

V1.3 is officially complete and production-ready when all of the following are true simultaneously:

1. **Scoring pipeline is clean.** `InterviewEvaluation` is deleted. `Report` is the sole scoring artifact. All presentation consumers read from `Report`.

2. **Cross-session continuity is live.** `LongitudinalProfile` is persisted after every session. Progress tracking reflects behavioral trends, not only dimensional scores.

3. **Replay is fully operational.** `replay_node` is implemented and deterministic. The Replay UI navigates any stored session without LLM calls.

4. **The Unified Report is the primary deliverable.** Every session produces a single, cohesive report with scores, narrative, coaching, explainability anchors, a replay link, and a progress trend panel.

5. **Explainability is surface-level visible.** Every coaching assertion is traceable to its evidence source in the report UI.

6. **Production UX is complete.** No placeholder states. No internal error surfaces. Primary flows are keyboard-navigable. Report and replay meet WCAG 2.1 AA.

7. **The platform is deployable.** Environment-parameterised. Health endpoint active. Structured logging complete. Deployment runbook reviewed and tested.

8. **SLOs are met.** All defined performance SLOs verified under 50-session load test.

9. **Architecture is clean.** Zero deprecated artifacts without a deletion milestone. Zero `InterviewState` fields without declared ownership. All PATs registered and enforced. Zero known constitutional violations.

10. **Test suite is green.** Total passing tests ≥ 2,500. Zero P0/P1 issues. Full V1.2 regression passes. All V1.3 acceptance criteria satisfied.

11. **Release artifacts exist.** V1.3 release tag with changelog. Performance baseline report. All ADRs authored and merged.

---

*This document is the authoritative V1.3 roadmap. All V1.3 work is governed by it. Amendments require an explicit update to this document with a recorded rationale.*

---

### Amendment — 2026-07-16 (EPIC-05/06 dependency correction)

**Rationale:** Architecture Clarification for EPIC-V13-05 finding F-B-01 proved the EPIC-05 ↔ EPIC-06 circular dependency was a documentation inconsistency only — not an architectural blocker. ADR-033 freezes Unified Report without explainability. EPIC-01 Architecture Freeze deferred explainability UI to EPIC-V13-06 and stated it is not blocking V13-05.

**Correction:** Removed EPIC-V13-06 from EPIC-V13-05 Dependencies and Roadmap reverse edge. Retained EPIC-V13-06 → EPIC-V13-05. Clarified EPIC-V13-05 Scope/Non-Goals: stable report surfaces only; explainability owned by EPIC-V13-06. No architecture or product-scope change.
