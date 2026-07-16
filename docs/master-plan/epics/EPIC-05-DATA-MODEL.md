# EPIC-05 — Unified Report: Data Model Specification

**Status:** DATA MODEL COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-05  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Data Model (Playbook §8.3)  
**Precondition:** EPIC-05-DOMAIN-CONTRACTS.md COMPLETE  
**Governing ADRs:** ADR-033, ADR-034, ADR-037, ADR-025, ADR-003  
**Authority:** Freezes presentation field tables, ownership verification, lifecycle, OI-DM-01. No ADR. No Architecture Freeze. No implementation.

---

## 1. Data Model Overview

### 1.1 Presentation model

The Unified Report presentation model has **three non-overlapping data planes**:

| Plane | Source of truth | Presentation carrier | UI surface |
|---|---|---|---|
| **A — Session report body** | `Report` | `FinalReportDTO` (sole factory `from_report`) | Report HTML sections + export |
| **B — Progress trend** | `LongitudinalProfile` → `LearningProgress` | `LearningProgress` (never on `FinalReportDTO`) | ProgressTrendPanel |
| **C — Replay handoff** | `Report.session_id` | `session_id: str` on DTO + chrome trigger | Gradio Replay control → EPIC-04 |

Planes do not share ownership. Plane A never reads Plane B sources. Plane B never embeds into Plane A. Plane C carries identity only.

### 1.2 Modelling resolutions closed by this document

| Open item | Resolution |
|---|---|
| OI-DM-01 — minimum session count for progress UI | **`>= 3`** (authoritative; §5) |
| AA-03 — new ADR required? | **No** — VERIFIED (§6) |
| AA-10 — insufficient-data rule | **VERIFIED** via OI-DM-01 |
| Study recommendations on DTO | Field table frozen (§2.5) |
| Replay `session_id` on DTO | Field table frozen (§2.4) |
| EPIC-06 extensibility | Additive DTO fields later; architecture unchanged (§7) |

---

## 2. Field Tables (Frozen)

### 2.1 Report — presentation-consumed fields (Plane A source)

Only fields consumed by Unified Report presentation are listed. Domain-only / unconsumed fields are intentional exclusions (§2.1.1).

| Field | Type | Presentation consumer | Mapped to FinalReportDTO |
|---|---|---|---|
| `session_id` | `str` | Replay handoff (Plane C) | `session_id` |
| `candidate_identity_id` | `str` | Progress load key (Plane B bind) | not on DTO body; used at bind |
| `scoring.overall_score` | `float` | Overall / performance | `overall_score` |
| `scoring.raw_score` | `Optional[float]` | Overall | `raw_score` |
| `scoring.adjusted_score` | `Optional[float]` | Overall | `adjusted_score` |
| `scoring.hiring_probability` | `float` | Overall / decision | `hiring_probability` |
| `scoring.hire_decision` | hire enum | Overall / decision | `hire_decision` (label) |
| `scoring.decision_explanation` | `Dict[str, List[str]]` | Decision | `decision_explanation` |
| `scoring.dimension_signals` | `Dict[str, float]` | Signals | `dimension_signals` |
| `scoring.percentile_rank` | `float` | Market | `percentile_rank` |
| `scoring.percentile_explanation` | `str` | Market | `percentile_explanation` |
| `scoring.gating_triggered` | `bool` | Decision | `gating_triggered` |
| `scoring.gating_reason` | `Optional[str]` | Decision | `gating_reason` |
| `scoring.weighted_breakdown` | `Dict[str, float]` | Dimensions | `weighted_breakdown` |
| `scoring.confidence` | `Confidence` | Overall | `confidence` |
| `scoring.scoring_dimensions` | dimensions | Performance / dimensions | `dimension_scores` (via mapper) |
| `scoring_narrative.executive_summary` | `str` | Executive | `executive_summary` |
| `scoring_narrative.went_well` | list | Went well | `went_well` |
| `scoring_narrative.held_you_back` | items | Held you back | `held_you_back` (`context_detail` dicts) |
| `scoring_narrative.knowledge_gaps` | items | Knowledge gaps | `knowledge_gaps` |
| `scoring_narrative.next_strategy` | items | Next strategy | `next_strategy` |
| `scoring_narrative.improvement_suggestions` | list | Roadmap | `improvement_suggestions` |
| `question_assessments` | tuple records | Questions | `question_assessments` |
| `narrative.insights` | insights | Narrative panel | `narrative_insights` |
| `coaching_snapshot.collection.objectives` | objectives | Coaching panel | `coaching_objectives` |
| `coaching_snapshot.collection.recommendations` | recommendations | Study panel | `study_recommendations` |
| `role` | `str` | Context | `role` |
| `seniority` | `str` | Context | `seniority_level` |
| `context_profile` | profile | Context | `context_profile` |
| `generation_metadata.total_tokens_used` | `int` | Metadata | `total_tokens_used` |

#### 2.1.1 Intentionally unconsumed on Report (EPIC-05)

| Field | Rationale |
|---|---|
| `profile_snapshot` | Not a Master Plan EPIC-05 report section; knowledge features not candidate-facing in Unified Report body |
| `narrative` five mandatory sections (overview/strengths/weaknesses/growth/recommendations) | Not Master Plan EPIC-05 requirements; insights list is the EPIC-05 narrative surface |
| `coaching_snapshot.collection.actions` | Not Master Plan EPIC-05 requirement |
| `report_id`, `interview_index`, `interview_type`, `question_count`, `knowledge_epoch`, `schema_version`, `created_at`, `metadata` | Provenance / internal; not required report sections |

---

### 2.2 FinalReportDTO — complete frozen field table

| Field | Type | Required | Source (`Report` path) | Owner |
|---|---|---|---|---|
| `overall_score` | `float` | Yes | `scoring.overall_score` | Report |
| `raw_score` | `float` | Yes | `scoring.raw_score` (0.0 if absent) | Report |
| `adjusted_score` | `float` | Yes | `scoring.adjusted_score` or overall | Report |
| `hiring_probability` | `float` | Yes | `scoring.hiring_probability` | Report |
| `hire_decision` | `str` | Yes | `scoring.hire_decision` (label) | Report |
| `decision_explanation` | `Dict[str, List[str]]` | Yes | `scoring.decision_explanation` | Report |
| `dimension_signals` | `Dict[str, float]` | Yes | `scoring.dimension_signals` | Report |
| `percentile_rank` | `float` | Yes | `scoring.percentile_rank` | Report |
| `percentile_explanation` | `str` | Yes | `scoring.percentile_explanation` | Report |
| `executive_summary` | `str` | Yes | `scoring_narrative.executive_summary` | Report |
| `gating_triggered` | `bool` | Yes | `scoring.gating_triggered` | Report |
| `gating_reason` | `Optional[str]` | Yes | `scoring.gating_reason` | Report |
| `weighted_breakdown` | `Dict[str, float]` | Yes | `scoring.weighted_breakdown` | Report |
| `dimension_scores` | `List[DimensionScoreDTO]` | Yes | `scoring.scoring_dimensions` | Report |
| `question_assessments` | `List[QuestionAssessmentDTO]` | Yes | `question_assessments` | Report |
| `improvement_suggestions` | `List[str]` | Yes | `scoring_narrative.improvement_suggestions` | Report |
| `went_well` | `List[str]` | Yes | `scoring_narrative.went_well` | Report |
| `held_you_back` | `List[Dict]` | Yes | `scoring_narrative.held_you_back` → dict | Report |
| `knowledge_gaps` | `List[Dict]` | Yes | `scoring_narrative.knowledge_gaps` → dict | Report |
| `next_strategy` | `List[Dict]` | Yes | `scoring_narrative.next_strategy` → dict | Report |
| `total_tokens_used` | `int` | Yes | `generation_metadata` or `0` | Report |
| `confidence` | `Confidence` | Yes | `scoring.confidence` | Report |
| `role` | `RoleType` | Yes | `role` | Report |
| `seniority_level` | `str` | Yes | `seniority` | Report |
| `context_profile` | `InterviewContextProfile` | Yes | `context_profile` | Report |
| `narrative_insights` | `List[NarrativeInsightDTO]` | Yes | `narrative.insights` | Report |
| `coaching_objectives` | `List[CoachingObjectiveDTO]` | Yes | `coaching_snapshot.collection.objectives` | Report |
| `study_recommendations` | `List[StudyRecommendationDTO]` | Yes | `coaching_snapshot.collection.recommendations` | Report |
| `session_id` | `str` | Yes | `session_id` | Report |

**Invariants:**
- DM-FR-01: Sole factory `from_report(Report)`.
- DM-FR-02: No `InterviewState` / `SessionHistory` reads in factory.
- DM-FR-03: `study_recommendations` and `session_id` are mandatory fields (may be empty list / non-empty string respectively).
- DM-FR-04: Progress fields **never** appear on `FinalReportDTO`.

---

### 2.3 Narrative fields (presentation)

#### NarrativeInsightDTO

| Field | Type | Required | Source | EPIC-05 |
|---|---|---|---|---|
| `insight_type` | `str` | Yes | `NarrativeInsight.insight_type` | YES |
| `prose` | `str` | Yes | `NarrativeInsight.prose` | YES |
| `confidence` | `float` | Yes | `NarrativeInsight.confidence` | YES |
| `source_feature_id` | — | — | domain only | **NO — EPIC-06** |
| `is_traceable` | — | — | domain only | **NO — EPIC-06** |

---

### 2.4 Coaching fields (presentation)

#### CoachingObjectiveDTO

| Field | Type | Required | Source | EPIC-05 |
|---|---|---|---|---|
| `objective_id` | `str` | Yes | `LearningObjective.objective_id` | YES |
| `description` | `str` | Yes | `LearningObjective.description` | YES |
| `priority` | `str` | Yes | `LearningObjective.priority` | YES |
| `confidence` | `float` | Yes | `LearningObjective.confidence` | YES |
| `feature_type` | `str` | Yes | `LearningObjective.feature_type` | YES |
| observation / KnowledgeGap origin fields | — | — | domain only | **NO — EPIC-06** |

#### StudyRecommendationDTO

| Field | Type | Required | Source |
|---|---|---|---|
| `recommendation_id` | `str` | Yes | `StudyRecommendation.recommendation_id` |
| `objective_id` | `str` | Yes | `StudyRecommendation.objective_id` |
| `resource_type` | `str` | Yes | `StudyRecommendation.resource_type` |
| `topic` | `str` | Yes | `StudyRecommendation.topic` |
| `rationale` | `str` | Yes | `StudyRecommendation.rationale` |
| `estimated_duration_hours` | `float` | Yes | `StudyRecommendation.estimated_duration_hours` |

**Invariant DM-SR-01:** Mapped only by `from_report`; production path must not use domain getattr fallback.

---

### 2.5 Replay entry fields (Plane C)

| Field | Type | Required | Source | Consumer |
|---|---|---|---|---|
| `FinalReportDTO.session_id` | `str` (non-empty) | Yes | `Report.session_id` | Report chrome replay resolver |
| Trigger payload `session_id` | `str` | Yes | **Must equal** `Report.session_id` when report present | `ReplayEntryPoint.enter` |

**Forbidden sources when `InterviewState.report is not None`:** `SessionHistory.session_id`, `InterviewState.interview_id`.

**Not on DTO:** `ReplaySession` payload, replay URLs, navigation state.

---

### 2.6 LearningProgress presentation fields (Plane B)

ProgressTrendPanel consumes the following from `LearningProgress`. No other progress source is permitted.

| Field | Type | UI use |
|---|---|---|
| `session_count` (property) | `int` | **Sole UI sufficiency gate** (§5): trend iff `>= 3` |
| `session_entries` | `tuple[SessionProgressEntry, ...]` | Optional session markers / sparkline inputs |
| `behavioral_trend` | `Optional[BehavioralTrend]` | Trend directions / feature trends when sufficiency true |
| `behavioral_trend.feature_trends[*].feature_type_id` | `str` | Trend row identity |
| `behavioral_trend.feature_trends[*].trend_direction` | `str` | improving / declining / stable / insufficient_data |
| `behavioral_trend.feature_trends[*].earliest_confidence` | `Optional[float]` | Display |
| `behavioral_trend.feature_trends[*].latest_confidence` | `Optional[float]` | Display |
| `behavioral_trend.feature_trends[*].sessions_observed` | `int` | Display |
| `candidate_identity_id` | `str` | Internal consistency; not required candidate-facing |
| `has_sufficient_data` | `bool` | **Not the UI gate** (see §5) |
| `language_capability_summary` | tuple | **Not consumed** by EPIC-05 ProgressTrendPanel |
| `schema_version`, `computed_at`, `knowledge_epoch`, `metadata` | various | Not rendered |

#### SessionProgressEntry (consumed subset)

| Field | UI use |
|---|---|
| `session_index` | Axis / ordering |
| `question_count` | Optional marker |
| Other entry fields | Not required for EPIC-05 trend panel minimum |

**Bind inputs (not FinalReportDTO fields):**
| Bind key | Source |
|---|---|
| `candidate_identity_id` | `Report.candidate_identity_id` |
| `LongitudinalProfile` | Persisted profile via repository / `ProgressTracker` |

---

## 3. Ownership Verification

| Field / group | Domain Contracts owner | Data Model verified owner | Dual ownership? |
|---|---|---|---|
| All §2.2 FinalReportDTO body fields except progress | Report → DTO | Report | No |
| `study_recommendations` | Report (`coaching_snapshot`) | Report | No |
| `session_id` | Report | Report | No |
| NarrativeInsightDTO EPIC-05 fields | Report.narrative | Report | No |
| CoachingObjectiveDTO EPIC-05 fields | Report.coaching | Report | No |
| ProgressTrendPanel fields §2.6 | LongitudinalProfile → LearningProgress | LongitudinalProfile | No |
| Replay UI after handoff | ReplaySession (EPIC-04) | ReplaySession | No |
| Explainability fields | EPIC-06 | EPIC-06 (not in tables) | No |

**Undefined ownership:** none.  
**Dual ownership:** none.

---

## 4. Lifecycle Verification

| Artifact | Created | Alive | Discarded | Mutability | Consistent with Domain Contracts? |
|---|---|---|---|---|---|
| `Report` | `report_node` | Session + persistence as applicable | N/A (immutable record) | Immutable | YES |
| `FinalReportDTO` | `from_report` per render/export | Request / UI response | After render/export | Immutable | YES |
| `LearningProgress` | On-demand at progress bind | Progress panel render | After render | Immutable; never persisted | YES |
| `LongitudinalProfile` | `longitudinal_update_node` (after report_node) | Persisted | Schema lifecycle elsewhere | Immutable instances | YES |
| Replay `session_id` trigger | User click on report chrome | Until `ReplayEntryPoint` accepts | After handoff | Scalar | YES |
| `ReplaySession` | EPIC-03/04 after handoff | Replay UI session | On replay exit | Immutable | YES (EPIC-04) |
| `UIResponse.report_output` | `_build_report` | UI cycle | Next response | String | YES |

**Lifecycle consistency check (F-W-05):** Progress bind **must not** assume longitudinal data exists at `report_node` completion. Progress loads persisted `LongitudinalProfile` at report UI bind time (after longitudinal update for the session, or on later view). **PASS.**

---

## 5. OI-DM-01 Resolution — Minimum Session Count

### 5.1 Decision

**Authoritative rule for Unified Report ProgressTrendPanel:**

```
show_trend := (LearningProgress.session_count >= 3)
```

- If `session_count < 3` → render **insufficient-data** state; **no trend extrapolation**.
- If `session_count >= 3` → render trend from `behavioral_trend` / allowed entry fields.

**Selected threshold: `>= 3`.**

### 5.2 Architectural rationale

1. **Master Plan product rule is explicit** (§7 Product Risks): show insufficient-data for fewer than **3** sessions; never extrapolate from sparse history.
2. **Two points are not a product trend.** Domain LP-LP-03 (`has_sufficient_data` when `session_count >= 2`) correctly marks computational readiness for pairwise delta; it does **not** authorize candidate-facing trend UX.
3. **Separation of concerns (no ADR required):**
   - LP-LP-03 remains the **domain computational** flag (`>= 2`).
   - ProgressTrendPanel uses **`session_count >= 3`** as the **sole presentation gate**.
   - UI **must not** treat `has_sufficient_data` alone as permission to show trends.
4. Amending LP-LP-03 to `>= 3` would change a frozen EPIC-02 domain invariant and would require ADR governance — **unnecessary** when presentation can gate on `session_count` without contradicting ADR-034 Decision 5.

### 5.3 Authoritative statement

| Layer | Rule | Status |
|---|---|---|
| Unified Report ProgressTrendPanel (EPIC-05) | `session_count >= 3` | **FROZEN — authoritative for this epic** |
| `LearningProgress.has_sufficient_data` (LP-LP-03) | `session_count >= 2` | Unchanged domain invariant; **not** the UI gate |

**OI-DM-01: CLOSED.**

---

## 6. Architecture Assumptions — Final Status

| ID | Prior status | Final status | Verification |
|---|---|---|---|
| AA-01 | VERIFIED | **VERIFIED** | Discovery + Domain Contracts + this Data Model |
| AA-02 | VERIFIED | **VERIFIED** | Domain Contracts I-C25-01; §2.5 dual-read ban |
| AA-03 | CONDITIONALLY VERIFIED | **VERIFIED** | All modelling resolved under ADR-033/034/037/025; no unresolved architectural decision; no new ADR required |
| AA-04 | VERIFIED | **VERIFIED** | §2.6; ADR-034; no new persistent artifact |
| AA-05 | VERIFIED | **VERIFIED** | §2.5; chrome handoff |
| AA-06 | VERIFIED | **VERIFIED** | Master Plan amendment; §7 extensibility |
| AA-07 | VERIFIED | **VERIFIED** | §2.3–2.4; PC-05 tables |
| AA-08 | VERIFIED | **VERIFIED** | Gradio stack unchanged |
| AA-09 | VERIFIED | **VERIFIED** | DM-FR-02 |
| AA-10 | CONDITIONALLY VERIFIED | **VERIFIED** | OI-DM-01: presentation gate `session_count >= 3` |

**CONDITIONALLY VERIFIED remaining:** none.  
**UNVERIFIED remaining:** none.  
**INVALIDATED:** none.

---

## 7. Extensibility Review — EPIC-06 Explainability

| Concern | Supported without Unified Report architecture change? |
|---|---|
| Add evidence fields to `NarrativeInsightDTO` | YES — additive optional fields; `from_report` mapping extension |
| Add KnowledgeGap origin to coaching DTOs | YES — additive; same plane A pipeline |
| New evidence panel / tooltip UX | YES — new section or section enrichment; still reads via `FinalReportDTO` |
| Change sole factory / dual-read rules | **NOT REQUIRED** and **FORBIDDEN** |
| Embed explainability into `Report` ownership model | **NOT REQUIRED** — domain already carries `source_feature_id` / related fields |
| Progress / Replay planes | Unaffected |

**Conclusion:** EPIC-06 can extend presentation DTOs and sections additively. ADR-033 Unified Report pipeline remains intact. No structural change to Planes A/B/C required.

---

## 8. Presentation Completeness vs Traceability

| Traceability ID | Data Model coverage |
|---|---|
| R-01 Consolidate paths | §1 planes; §3 ownership |
| R-02 Sole FinalReportDTO API | §2.2 DM-FR-01 |
| R-03 Replay entry | §2.5 |
| R-04 Progress trend | §2.6; §5 |
| R-05 No SessionHistory dual read | §2.5 forbidden sources |
| R-06 Stable surfaces for EPIC-06 | §2.3–2.4 deferred columns; §7 |
| R-07 Traceable Report sections | §2.1–2.2 |
| R-08 Study recommendations | §2.4 StudyRecommendationDTO |
| R-09 Insufficient-data progress | §5 `>= 3` |

All rows covered. No unmet in-scope modelling gap.

---

## 9. Open Findings

### BLOCKER

None.

### WARNING

| ID | Finding | Notes |
|---|---|---|
| F-W-06 | Stale tooling still references `from_components` | Implementation cleanup; not a modelling gap |

### INFORMATION

| ID | Note |
|---|---|
| F-I-DM-01 | LP-LP-03 (`has_sufficient_data >= 2`) retained as domain computational flag; UI gate is independent (`>= 3`) |
| F-I-DM-02 | `profile_snapshot`, coaching actions, narrative five-sections intentionally unconsumed in EPIC-05 |
| F-I-DM-03 | `study_recommendations` and `session_id` are additive DTO fields relative to current code — Data Model freezes them as required |

---

## 10. Definition of Done — Data Model (§8.3)

| Criterion | Status |
|---|---|
| Open modelling questions from Domain Contracts resolved | YES — OI-DM-01 closed |
| Complete field tables frozen | YES — §2 |
| Replay / presentation completeness verified | YES — §8 |
| Extensibility for next epic evaluated | YES — §7 |
| All Architecture Assumptions VERIFIED or INVALIDATED | YES — §6 (all VERIFIED) |
| No ADR / Freeze / implementation | YES |

---

## 11. Next Step

**Architecture Review / ADR (conditional)** — evaluate whether any genuine unresolved architectural decision remains.

Per this Data Model: **no new ADR is indicated.** Proceed to record skip rationale in **Architecture Freeze**, then Implementation Plan.

---

*This document freezes the EPIC-V13-05 Unified Report presentation data model. It does not authorize implementation.*
