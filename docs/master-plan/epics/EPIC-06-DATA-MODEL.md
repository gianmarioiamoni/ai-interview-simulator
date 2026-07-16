# EPIC-06 — Explainability: Data Model Specification

**Status:** DATA MODEL COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-06  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Data Model (Playbook §8.3)  
**Precondition:** `EPIC-06-DOMAIN-CONTRACTS.md` COMPLETE; EPIC-V13-05 CLOSED  
**Governing ADRs (reuse):** ADR-023, ADR-033; ADR-025 consulted for drift classification only; ADR-016 substrate only  
**Authority:** Persistence / serialization / presentation field tables; reconstruction completeness; schema versioning; failure model. No ADR. No Architecture Freeze. No implementation. No presentation-mechanism selection.

---

## Save Token (precondition)

| Check | Result |
|---|---|
| Working tree | Clean |
| HEAD | `7f43b1e3ad63bc5e9c7c4eeb2f2c738c46151b9d` (`7f43b1e` — docs(epic-06): define explainability domain contracts) |
| Stash | Not created |

---

## 1. Explainability Data Model

### 1.1 Plane and ownership

| Plane | Artifact | Role for explainability |
|---|---|---|
| Persistence / authority | `Report` (embedded `narrative`, `coaching_snapshot`) | Sole persisted source for explainability reconstruction |
| Domain evidence (read-only) | `NarrativeInsight`, `LearningObjective`, `CoachingAction` | Immutable evidence already on `Report` |
| Presentation | `FinalReportDTO` (+ nested DTOs) | Ephemeral projection via sole factory `from_report` |
| Forbidden | Observation store, SessionHistory dual-read, LLM at presentation | ARC-01 / ADR-033 / EC-V-01 |

**Invariant DM-E06-01:** Explainability never introduces a new Report writer, new domain producer schema, or parallel DTO factory.

**Invariant DM-E06-02:** Deterministic reconstruction of candidate-visible explainability uses only fields already persisted on `Report` (via Domain Contracts EC-N-01 / EC-C-01).

### 1.2 Required evidence field set (frozen)

| Concern | Required persisted fields | Domain owner | Present on implemented contracts? |
|---|---|---|---|
| Narrative insight evidence | `NarrativeInsight.source_feature_id` (`FeatureIdentity`), `NarrativeInsight.is_traceable` | ADR-023 | **YES** |
| FeatureIdentity serialization components | `feature_type_id`, `semantic_category` (`schema_version` optional qualifier, not identity) | ADR-020 / ADR-023 | **YES** |
| Coaching action linkage | `CoachingAction.objective_id` | Implemented coaching | **YES** |
| Coaching action origin | Parent `LearningObjective.feature_type`, `supporting_observation_types` (minimum); `description` allowed | Implemented coaching | **YES** |
| Snapshot integrity key | `LearningObjective.objective_id` match on same `coaching_snapshot` | Implemented coaching | **YES** |

**Not required for EPIC-06 reconstruction:** Observation payloads; `KnowledgeGap` entity; ADR-025 `source_gap_id` / `source_feature_id` on `CoachingAction`; ADR-025 `source_gap_ids` / `source_feature_ids` on `LearningObjective`.

### 1.3 Presentation DTO host set (EPIC-06 additive)

| DTO | EPIC-05 baseline | EPIC-06 additive responsibility |
|---|---|---|
| `NarrativeInsightDTO` | `insight_type`, `prose`, `confidence` | Project `source_feature_id` + `is_traceable` |
| `CoachingActionDTO` (**new presentation type**) | Absent | Project action identity + resolved origin fields |
| `CoachingObjectiveDTO` | `objective_id`, `description`, `priority`, `confidence`, `feature_type` | Optional origin enrichment: `supporting_observation_types` (OF-04) |
| `FinalReportDTO` | hosts lists above | Add `coaching_actions` list; extend insight mapping |

---

## 2. Narrative Evidence Serialization Model

### 2.1 Domain → persistence (already on Report)

Source path: `Report.narrative.insights[*]` (`NarrativeInsight`).

| Domain field | Type | Persisted | Serialization rule |
|---|---|---|---|
| `insight_type` | `NarrativeInsightType` | Yes | Enum `.value` → `str` |
| `prose` | `str` | Yes | As-is (LLM-variable; not explainability identity) |
| `confidence` | `float` | Yes | `[0.0, 1.0]` |
| `source_feature_id` | `FeatureIdentity` | Yes | Nested object — §2.2 |
| `is_traceable` | `bool` | Yes | Must be `true` at domain construction; project as `bool` |
| `schema_version` | `str` | Yes on domain | Not required on presentation DTO for explainability |

### 2.2 FeatureIdentity serialization (frozen shape)

| Field | Type | Required on DTO | Rule |
|---|---|---|---|
| `feature_type_id` | `str` | **Yes** | Stable identity key; never null/empty |
| `semantic_category` | `str` | **Yes** | Stable category label; never null/empty |
| `schema_version` | `str` | Optional | May be omitted on DTO; if present, copy from domain |

**Presentation type name:** `FeatureIdentityDTO` (nested frozen dataclass / equivalent) **or** inline dict with the same keys. Exact host language type is implementation-local; **keys and requiredness are frozen here**.

**Forbidden:** Serializing Observation ids; inventing feature labels not present on `source_feature_id`.

### 2.3 NarrativeInsightDTO (EPIC-06 complete table) — resolves OF-02 narrative half

| Field | Type | Required | Source | EPIC |
|---|---|---|---|---|
| `insight_type` | `str` | Yes | `NarrativeInsight.insight_type` | EPIC-05 |
| `prose` | `str` | Yes | `NarrativeInsight.prose` | EPIC-05 |
| `confidence` | `float` | Yes | `NarrativeInsight.confidence` | EPIC-05 |
| `source_feature_id` | `FeatureIdentityDTO` / `{feature_type_id, semantic_category[, schema_version]}` | **Yes** | `NarrativeInsight.source_feature_id` | **EPIC-06** |
| `is_traceable` | `bool` | **Yes** | `NarrativeInsight.is_traceable` | **EPIC-06** |

**Invariant DM-N-01:** Every insight included in `FinalReportDTO.narrative_insights` MUST carry both EPIC-06 fields. Absence → projection failure (EC-V-01).

---

## 3. Coaching Evidence Serialization Model

### 3.1 Domain → persistence (already on Report)

Source path: `Report.coaching_snapshot.collection.actions[*]` + `...objectives[*]`.

#### CoachingAction (domain)

| Domain field | Type | Role in explainability |
|---|---|---|
| `action_id` | `str` | Action identity |
| `objective_id` | `str` | Origin join key (EC-C-01) |
| `category` | `ActionCategory` | Presentation context (not origin) |
| `description` | `str` | Action text |
| `effort_estimate_hours` | `float` | Presentation context |
| `is_immediate` | `bool` | Presentation context |
| `tags` | `frozenset[str]` | Optional presentation; serialize as sorted `list[str]` if exposed |

**Absent on implemented domain (ADR-025 drift — not EPIC-06 fields):** `source_gap_id`, `source_feature_id`, `is_traceable` on action.

#### LearningObjective origin (domain)

| Domain field | Type | Origin role |
|---|---|---|
| `objective_id` | `str` | Join key |
| `feature_type` | `FeatureType` | **Required origin** |
| `supporting_observation_types` | `tuple[ObservationType, ...]` | **Required origin** (may be empty tuple) |
| `description` | `str` | Allowed origin prose |
| `priority`, `confidence`, … | various | Existing EPIC-05 objective surface |

### 3.2 Origin resolution rule (deterministic)

```
for each CoachingAction a in coaching_snapshot.collection.actions:
  objective = collection.objective_by_id(a.objective_id)
  if objective is None → FAIL (snapshot integrity)
  origin.feature_type = objective.feature_type
  origin.supporting_observation_types = objective.supporting_observation_types
  origin.objective_id = objective.objective_id
  origin.description = objective.description  # allowed enrichment
```

No Observation store fetch. No KnowledgeGap type. Same-snapshot only.

### 3.3 CoachingActionDTO (new — frozen table) — resolves OF-02 coaching half

| Field | Type | Required | Source |
|---|---|---|---|
| `action_id` | `str` | Yes | `CoachingAction.action_id` |
| `objective_id` | `str` | Yes | `CoachingAction.objective_id` |
| `category` | `str` | Yes | `CoachingAction.category` → enum `.value` |
| `description` | `str` | Yes | `CoachingAction.description` |
| `effort_estimate_hours` | `float` | Yes | `CoachingAction.effort_estimate_hours` |
| `is_immediate` | `bool` | Yes | `CoachingAction.is_immediate` |
| `origin_feature_type` | `str` | **Yes** | Parent `LearningObjective.feature_type` → `.value` |
| `origin_supporting_observation_types` | `List[str]` | **Yes** | Parent types → each `.value`; empty list valid |
| `origin_objective_description` | `str` | Yes | Parent `LearningObjective.description` |

**Invariant DM-C-01:** Every action in `FinalReportDTO.coaching_actions` MUST include all three origin fields. Unresolved `objective_id` → fail-fast before DTO completion.

### 3.4 CoachingObjectiveDTO (optional enrichment — OF-04)

| Field | Type | Required | Source | EPIC |
|---|---|---|---|---|
| (existing EPIC-05 five fields) | … | Yes | unchanged | EPIC-05 |
| `supporting_observation_types` | `List[str]` | Optional for EPIC-06 go-live | `LearningObjective.supporting_observation_types` | EPIC-06 optional |

**Invariant DM-C-02:** Objective-level enrichment MUST NOT replace action-level explainability (EC-C-01 / OQ-04).

---

## 4. Report Persistence Mapping

| Persisted path | Explainability use | Writer | EPIC-06 change? |
|---|---|---|---|
| `Report.narrative.insights[*].source_feature_id` | Narrative evidence | NarrativeGenerator → report_node / ReportBuilder | **None** |
| `Report.narrative.insights[*].is_traceable` | Narrative evidence flag | Same | **None** |
| `Report.coaching_snapshot.collection.actions[*]` | Action set | CoachingEngine → same | **None** |
| `Report.coaching_snapshot.collection.objectives[*]` | Origin resolution set | CoachingEngine → same | **None** |
| `Report.schema_version` | Report envelope version | ReportBuilder | **None** |
| Observation store / SessionHistory | — | — | **Forbidden as explainability source** |

**Invariant DM-P-01:** EPIC-06 adds no columns to `Report`, `Narrative`, `CoachingSnapshot`, or domain coaching/narrative models.

---

## 5. FinalReportDTO Field Mapping

### 5.1 Additive / changed host fields

| Field | Type | Required | Source path | EPIC |
|---|---|---|---|---|
| `narrative_insights` | `List[NarrativeInsightDTO]` | Yes (may be empty) | `report.narrative.insights` | EPIC-05 + **EPIC-06 field extension** |
| `coaching_objectives` | `List[CoachingObjectiveDTO]` | Yes (may be empty) | `report.coaching_snapshot.collection.objectives` | EPIC-05 (+ optional OF-04) |
| `coaching_actions` | `List[CoachingActionDTO]` | **Yes (may be empty)** | `report.coaching_snapshot.collection.actions` + origin join | **EPIC-06** |
| `study_recommendations` | unchanged | Yes | unchanged | EPIC-05 |
| All other FinalReportDTO fields | unchanged | — | — | EPIC-05 |

**Invariant DM-FR-01:** Sole factory remains `FinalReportDTO.from_report(report)`.

**Invariant DM-FR-02:** Export path consumes the same factory output (parity).

### 5.2 Mapping algorithm (normative)

1. Map each `NarrativeInsight` → `NarrativeInsightDTO` including `source_feature_id` + `is_traceable`.
2. Build objective index by `objective_id` from `coaching_snapshot.collection.objectives`.
3. For each `CoachingAction`, resolve parent objective; on miss → raise projection error.
4. Map action + origin fields → `CoachingActionDTO`.
5. Map objectives as today; optionally attach `supporting_observation_types`.
6. Run projection completeness gate (PC-E05 / §11) before returning DTO.

---

## 6. DTO Serialization Rules

| Rule ID | Rule |
|---|---|
| SR-01 | Enums → string via `.value` (or `str` equivalent); never opaque enum objects across UI boundary |
| SR-02 | `FeatureIdentity` → nested DTO/dict with required `feature_type_id` + `semantic_category` |
| SR-03 | `ObservationType` tuples → `List[str]` of `.value`; preserve order; empty list allowed |
| SR-04 | `frozenset[str]` (tags), if exposed → sorted `list[str]` for deterministic serialization |
| SR-05 | Booleans and floats copied without coercion beyond type |
| SR-06 | No defaulting of missing required explainability fields to empty/placeholder values |
| SR-07 | No LLM calls; no recomputation of feature/gap identity |
| SR-08 | Extra domain fields not listed in §2–§3 MAY be omitted from DTO; required explainability fields MUST NOT |

---

## 7. Traceability Matrix (Persisted Source → Presentation Field)

| # | Persisted source | Presentation field | Consumer | Contract |
|---|---|---|---|---|
| T-01 | `Report.narrative.insights[*].source_feature_id` | `NarrativeInsightDTO.source_feature_id` | C-20 / C-26 | EC-N-01, PC-E02 |
| T-02 | `Report.narrative.insights[*].is_traceable` | `NarrativeInsightDTO.is_traceable` | C-20 / C-26 | EC-N-01, PC-E02 |
| T-03 | `Report.coaching_snapshot.collection.actions[*]` | `FinalReportDTO.coaching_actions[*]` (identity fields) | Coaching surface / C-26 | PC-E03 |
| T-04 | Parent `LearningObjective.feature_type` (same snapshot) | `CoachingActionDTO.origin_feature_type` | Coaching surface / C-26 | EC-C-01, PC-E04 |
| T-05 | Parent `LearningObjective.supporting_observation_types` | `CoachingActionDTO.origin_supporting_observation_types` | Coaching surface / C-26 | EC-C-01, PC-E04 |
| T-06 | Parent `LearningObjective.description` | `CoachingActionDTO.origin_objective_description` | Coaching surface / C-26 | PC-E04 |
| T-07 | Parent `LearningObjective.objective_id` | `CoachingActionDTO.objective_id` (join echo) | Coaching surface | EC-C-01 |
| T-08 | (optional) `LearningObjective.supporting_observation_types` | `CoachingObjectiveDTO.supporting_observation_types` | C-21 | OF-04 / PC-E04 |

**Status:** 8/8 presentation mappings owned once. No dual-source rows.

---

## 8. Reconstruction Completeness Verification (AA-05 / domain plane)

### 8.1 Question

Do implemented domain contracts contain every **persisted** field required for deterministic Explainability reconstruction on the Report plane?

### 8.2 Verdict

**YES — complete on the Report / domain plane.**

| Required field | Location | Classification if missing |
|---|---|---|
| `NarrativeInsight.source_feature_id` | Implemented | — |
| `NarrativeInsight.is_traceable` | Implemented | — |
| `FeatureIdentity.feature_type_id` / `semantic_category` | Implemented | — |
| `CoachingAction.objective_id` | Implemented | — |
| `LearningObjective.feature_type` | Implemented | — |
| `LearningObjective.supporting_observation_types` | Implemented | — |
| `LearningObjective.objective_id` | Implemented | — |

### 8.3 Gaps vs presentation (not domain persistence gaps)

| Gap | Classification |
|---|---|
| `NarrativeInsightDTO` lacks `source_feature_id` / `is_traceable` today | **Data Model extension** (this document freezes the table; implementation later) |
| No `CoachingActionDTO` / `coaching_actions` on `FinalReportDTO` today | **Data Model extension** |
| Optional objective `supporting_observation_types` on DTO | **Data Model extension** (OF-04) |
| ADR-025 `source_gap_id` / action `source_feature_id` absent in domain | **Documentation drift** (OF-03) — **not** required for reconstruction under EC-C-01 |
| Master Plan “Observation anchor” / “KnowledgeGap origin” wording | **Documentation drift** (Domain Contracts §2) — not Architecture issue for EPIC-06 binding |

**No Domain Contracts extension required** for missing persisted explainability fields.  
**No Architecture issue** (ownership / sole-writer remains ADR-023 + ADR-033 + implemented coaching binding).

### 8.4 AA-05 register update

| Aspect | Status |
|---|---|
| Persisted-field completeness for deterministic reconstruction | **VERIFIED** |
| Concrete UI presentation mechanism (layout/interaction) | **UNVERIFIED** — remains OF-01; out of Data Model selection authority |

AA-05 overall register status: **PARTIALLY VERIFIED** — reconstruction data plane verified; mechanism deferred.

---

## 9. Schema Versioning Strategy

| Layer | Version field | EPIC-06 policy |
|---|---|---|
| `Report.schema_version` | Currently `"2.0"` | **No bump required** for explainability (no Report schema change) |
| `NarrativeInsight.schema_version` | Domain default `"1.0"` | Unchanged; not a presentation gate |
| Coaching domain objects | No separate action schema bump for explainability | Unchanged |
| `FinalReportDTO` | Presentation-only | Additive fields; treat as **compatible additive projection version** — no domain schema version increment |
| FeatureIdentity.schema_version | Qualifier only | Must not be used as join key; identity remains `(feature_type_id, semantic_category)` |

**Invariant DM-V-01:** Additive DTO fields MUST NOT require Report `schema_version` change.  
**Invariant DM-V-02:** Future removal/rename of required explainability DTO fields requires a documented presentation version policy (out of EPIC-06 scope unless encountered at Freeze).

---

## 10. Cross-Contract Validation

| Check | Rule | Fail class |
|---|---|---|
| X-01 | Every presented insight has non-null `source_feature_id.feature_type_id` and `semantic_category` | Projection contract violation |
| X-02 | Every presented insight has `is_traceable is True` | Domain invariant / projection failure |
| X-03 | Every presented action’s `objective_id` resolves on same `coaching_snapshot` | Snapshot integrity violation |
| X-04 | Resolved origin includes `origin_feature_type` and `origin_supporting_observation_types` (list, possibly empty) | Projection contract violation |
| X-05 | No explainability mapping reads SessionHistory / Observation store | Architectural violation (ADR-033) |
| X-06 | Scoring-narrative `knowledge_gaps` never used as coaching-action origin | Contract violation (EC-C-02) |
| X-07 | Empty `narrative_insights` / empty `coaching_actions` allowed | Valid — not a failure |
| X-08 | HTML render and export use identical DTO instance / factory path | Parity violation if diverged |

Validation executes at `from_report` and/or immediate pre-render (PC-E05). Class: fail-fast (EC-V-01).

---

## 11. Explainability Failure Model

| Case | Class | Behavior |
|---|---|---|
| Insight present, missing `source_feature_id` components after map | Projection contract violation | **Fail-fast** — no DTO / no render |
| Insight present, `is_traceable=False` | Domain invariant violation | **Fail-fast** (domain should already reject; presentation must not soften) |
| Action present, parent objective missing | Snapshot integrity violation | **Fail-fast** |
| Action present, origin fields dropped in map | Projection contract violation | **Fail-fast** |
| Zero insights / zero actions | Empty set | **Success** — nothing to explain |
| LLM unavailable at presentation | N/A | Presentation is LLM-independent — not a failure mode |
| Observation payload unreachable | N/A | Not required — not a failure mode |

**Forbidden:** Silent omission, placeholder anchors, soft-hide of required fields, degradation to “no evidence” copy when evidence was required for a present item.

---

## 12. Documentation Drift Verification

| ID | Drift | Classification | EPIC-06 action |
|---|---|---|---|
| D-01 | Master Plan “Observation anchor” vs ADR-023 ProfileFeature identity | Documentation drift | Already contracted (EC-N-01); no implementation redesign |
| D-02 | Master Plan / ADR-025 “KnowledgeGap origin” / `source_gap_id` vs implemented `LearningObjective` origin | Documentation drift | Already contracted (EC-C-01); no EPIC-06 domain redesign |
| D-03 | ADR-025 LearningObjective / CoachingAction taxonomy fields unrealized in code | Documentation drift | **OF-03** — documentation alignment only |
| D-04 | EPIC-05 Data Model deferred columns now specified here | Resolved by this document | Implementation later under Freeze |

### 12.1 OF-03 / ADR-025 — alignment vs divergence

| Question | Verdict |
|---|---|
| Does ADR-025 require **only documentation alignment** for EPIC-06? | **YES** |
| Does any **implemented** contract diverge from EPIC-06 binding contracts? | **NO** — implementation matches EC-C-01 binding |
| Does implemented coaching diverge from ADR-025 text? | **YES** — historical documentation drift (unrealized FKs / KnowledgeGap entity) |
| Architecture issue? | **NO** for EPIC-06 ownership |
| Domain Contracts extension required? | **NO** |

---

## 13. Architecture Assumptions Register (Data Model)

| ID | Status | Justification |
|---|---|---|
| AA-01 | **VERIFIED** | Unchanged — additive DTO on EPIC-05 host |
| AA-02 | **INVALIDATED** | Unchanged — ProfileFeature identity supersedes Observation-anchor wording |
| AA-03 | **INVALIDATED** | Unchanged — LearningObjective origin supersedes `source_gap_id` |
| AA-04 | **VERIFIED** | Confirmed: all required evidence fields already on Report; no new persistence |
| AA-05 | **PARTIALLY VERIFIED** | Reconstruction field completeness **VERIFIED** (§8); UI presentation mechanism still **UNVERIFIED** (OF-01) |
| AA-06 | **VERIFIED** | Failure model §11 = fail-fast (EC-V-01) |
| AA-07 | **VERIFIED** | No new sole-writer / persistence ownership; ADR step still likely skip |
| AA-08 | **INVALIDATED** | Unchanged — named Observation/KnowledgeGap payloads not required |
| AA-09 | **VERIFIED** | Unchanged |
| AA-10 | **VERIFIED** | Unchanged |

**VERIFIED:** AA-01, AA-04, AA-06, AA-07, AA-09, AA-10. **PARTIALLY VERIFIED:** AA-05. **INVALIDATED:** AA-02, AA-03, AA-08.

---

## 14. Open Findings

| ID | Finding | Class | Status after Data Model |
|---|---|---|---|
| OF-01 | Concrete presentation mechanism unresolved | INFORMATION | **Open** — mechanism later / Freeze UX, not ownership |
| OF-02 | Exact DTO field tables / FeatureIdentity serialization / action DTO shape | WARNING | **Resolved** — §2–§5 |
| OF-03 | ADR-025 / KnowledgeGap documentation drift | INFORMATION | **Confirmed documentation-alignment-only** — §12 |
| OF-04 | Optional objective-level origin duplication | INFORMATION | **Resolved as optional** — §3.4; not required for R-02 |

**BLOCKER:** none for Data Model gate.

---

## 15. Candidate ADR Evaluation

| Item | Result |
|---|---|
| New sole-writer? | No |
| New persistence shape on Report? | No |
| New ownership conflict? | No |
| New ADR required? | **No** — reconfirm at Architecture Review (expected SKIP) |

---

## 16. Playbook §8.3 Definition of Done Checklist

| Criterion | Status |
|---|---|
| Field tables frozen for narrative + coaching explainability | YES (§2–§3, §5) |
| Persistence mapping explicit; no new Report writers | YES (§4) |
| Serialization rules explicit | YES (§6) |
| Traceability persisted → presentation | YES (§7) |
| Reconstruction completeness verified | YES (§8) |
| Schema versioning strategy | YES (§9) |
| Cross-contract validation + failure model | YES (§10–§11) |
| Documentation drift classified | YES (§12) |
| No ADR / Freeze / implementation | YES |

---

## 17. Recommendation

**Next engineering task (exactly one):**  
Proceed to Architecture Review (expect ADR skip) then Architecture Freeze for EPIC-V13-06. Do not implement until Freeze. Presentation mechanism remains OF-01.

---

*Data Model complete. Persistence and presentation field tables frozen. Reconstruction plane verified. No production code modified.*
