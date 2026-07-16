# EPIC-06 — Explainability: Domain Contracts

**Status:** DOMAIN CONTRACTS COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-06  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Domain Contracts (Playbook §8.2)  
**Precondition:** `EPIC-06-EXPLAINABILITY.md` (Architecture Discovery) COMPLETE; EPIC-V13-05 CLOSED  
**Governing ADRs (reuse):** ADR-023, ADR-033, ADR-016 (substrate only); ADR-025 consulted for drift classification  
**Authority:** Ownership, presentation contracts, Traceability Matrix, evidence-contract resolutions. No Data Model field tables. No ADR. No Architecture Freeze. No implementation. No presentation-mechanism selection.

---

## 1. Contract Overview

### 1.1 Purpose

Define sole ownership and presentation contracts so EPIC-06 explainability is a Report-plane projection concern: candidate-visible evidence for narrative insights and coaching actions, without redesigning domain producers or inventing unrealized ADR-025 / KnowledgeGap entities.

### 1.2 Responsibilities (EPIC-06)

| Responsibility | In scope |
|---|---|
| Candidate-visible evidence for every `NarrativeInsight` on Unified Report | YES |
| Candidate-visible origin for every `CoachingAction` on Unified Report | YES |
| Project explainability fields via `FinalReportDTO.from_report` (additive) | YES |
| Pre-render / projection completeness validation for required evidence fields | YES |
| Preserve ADR-033 sole-source / dual-read ban / LLM-free projection | YES |
| Select concrete UI presentation mechanism | **NO** (Data Model / later planning) |
| Redesign `NarrativeInsight` / `CoachingAction` domain schemas | **NO** |
| Introduce `KnowledgeGap` domain type or ADR-025 unrealized FKs | **NO** |
| Embed Observation payloads on `Report` | **NO** |
| Change `report_node` / `ReportBuilder` writers | **NO** |
| NL “why” UI / AI meta-explanations / audit trails | **NO** (Master Plan non-goals) |

### 1.3 Ownership Summary (no shared ownership)

| Artifact / concern | Sole owner | Sole producer / writer | Sole presentation consumer API | Lifecycle |
|---|---|---|---|---|
| `NarrativeInsight` evidence identity (`source_feature_id`, `is_traceable`) | Domain narrative (ADR-023) | NarrativeGenerator → embedded on `Report.narrative` via `report_node` | `FinalReportDTO.from_report` → Narrative explainability surface | Immutable on `Report` |
| Narrative explainability presentation fields | EPIC-06 presentation | `FinalReportDTO.from_report` (sole factory) | Narrative section (C-20) / export parity | Ephemeral DTO |
| `CoachingAction` domain instance | Domain coaching | CoachingEngine → `Report.coaching_snapshot` | `FinalReportDTO.from_report` | Immutable on `Report` |
| Coaching action **origin** (contractual) | Domain coaching — parent `LearningObjective` | CoachingEngine (same snapshot) | `FinalReportDTO.from_report` → Coaching explainability surface | Immutable; linked by `objective_id` |
| Coaching explainability presentation | EPIC-06 presentation | `FinalReportDTO.from_report` | Coaching actions / objectives sections / export | Ephemeral DTO |
| Scoring-narrative `knowledge_gaps` (`ScoringNarrativeItem`) | Domain scoring narrative (EPIC-01/05) | Report scoring narrative assembly | Existing KnowledgeGapSection (C-11) | **Out of EPIC-06 explainability origin contract** |
| Observation payloads / Observation store | Domain observation (ADR-016) | Observation pipeline | **Not an EPIC-06 presentation source** | Unchanged |
| Documented `KnowledgeGap` entity / ADR-025 `source_gap_id` | N/A (unimplemented) | N/A | N/A | **Obsolete for EPIC-06 contract binding** (documentation drift) |
| Missing-required-evidence handling class | EPIC-06 contracts (this document) | Projection gate (`from_report` / pre-render validation) | Report render / export | Fail-fast class — §4.3 |

---

## 2. Evidence Contract Resolutions (OQ-01 / OQ-02 / OQ-03)

### 2.1 OQ-01 — Narrative evidence target

| Question | Resolution |
|---|---|
| Authoritative artifact | **`NarrativeInsight.source_feature_id: FeatureIdentity`** (ProfileFeature identity) plus **`is_traceable=True`**, per ADR-023 C-02 and implemented domain model |
| Obsolete / drift | Master Plan EPIC-06 wording “Observation anchor” as the **required** narrative evidence target is **documentation drift** relative to ADR-023 and I-15 (“Observation **or** ProfileFeature”) |
| Architectural gap? | **No** — for EPIC-06 narrative explainability. Observation payloads are not required on the Report plane for this contract |
| Candidate-visible meaning | Surfacing the ProfileFeature evidence identity already carried on each `NarrativeInsight` on `Report` |

**Contract invariant EC-N-01:** Every candidate-visible `NarrativeInsight` explainability surface SHALL project `source_feature_id` and `is_traceable` from `Report.narrative.insights` via `FinalReportDTO.from_report`. No Observation payload fetch. No SessionHistory dual-read.

**Contract invariant EC-N-02:** EPIC-06 SHALL NOT require a new Observation field on `NarrativeInsight` or Observation embedding on `Report`.

### 2.2 OQ-02 — Coaching origin model

| Question | Resolution |
|---|---|
| Authoritative artifact | **`CoachingAction` → parent `LearningObjective` via `objective_id`**, with origin fields already on `LearningObjective`: `feature_type`, `supporting_observation_types`, `description` (implemented evidence basis) |
| Obsolete / drift | Domain Freeze / ADR-025 **`KnowledgeGap` entity** and ADR-025 **`CoachingAction.source_gap_id` / `source_feature_id`** are **documentation drift** relative to the implemented coaching schema — **obsolete as EPIC-06 binding targets** (not deleted from ADR history; not implemented; not redesigned here) |
| Architectural gap? | **No redesign gap** for EPIC-06 if presentation binds to the implemented origin chain. Unrealized ADR-025 taxonomy is **out-of-band documentation debt**, not an EPIC-06 implementation redesign mandate |
| Master Plan phrase “KnowledgeGap origin” | Contractually interpreted as the **implemented coaching evidence origin** (parent `LearningObjective` evidence fields), not a non-existent `KnowledgeGap` type |

**Contract invariant EC-C-01:** Every candidate-visible `CoachingAction` SHALL present its origin by resolving `action.objective_id` to the matching `LearningObjective` on the **same** `Report.coaching_snapshot` and projecting that objective’s evidence fields (`feature_type`, `supporting_observation_types` at minimum).

**Contract invariant EC-C-02:** EPIC-06 SHALL NOT introduce `KnowledgeGap` domain types, SHALL NOT add ADR-025 unrealized FKs to `CoachingAction`, and SHALL NOT treat `ScoringNarrative.knowledge_gaps` as the coaching-action origin.

### 2.3 OQ-03 — Missing evidence handling class

| Question | Resolution |
|---|---|
| Architectural class | **Domain invariant violation / projection completeness failure — fail-fast** |
| Not chosen | Presentation degradation / silent omission of required anchors |

| Layer | Rule |
|---|---|
| Domain construction | `NarrativeInsight` without valid `source_feature_id` or with `is_traceable=False` remains a **domain invariant violation** (already enforced) |
| Snapshot integrity | `CoachingAction.objective_id` with no matching `LearningObjective` on the same `coaching_snapshot` is a **snapshot integrity violation** — fail-fast at projection |
| Presentation / pre-render | Required explainability fields MUST be present on the DTO for every insight/action included in the presentation set; absence after mapping from a present domain item is a **projection contract violation** — fail-fast. Silent suppression is **forbidden** |
| Empty collections | Zero insights or zero actions is valid (nothing to explain) — not a missing-anchor case |
| Master Plan “fail gracefully” | Subordinated for **required** explainability fields: graceful empty UI applies to empty sets only, not to missing required evidence on present items |

**Contract invariant EC-V-01:** EPIC-06 validation gate classifies missing required evidence as **fail-fast**, not presentation degradation.

### 2.4 Related Discovery WARNING resolutions (contractual)

| ID | Resolution |
|---|---|
| OQ-04 | Master Plan requires **action-level** surfacing. EPIC-06 contracts **require** `CoachingAction` on the presentation plane with origin. Objective-level surfaces remain (EPIC-05) and MAY expose the same origin fields; they do **not** replace action-level explainability |
| OQ-05 | Scoring-narrative `knowledge_gaps` are **distinct** from coaching-action origin. **Not a substitute.** Owner remains EPIC-05 scoring narrative / C-11 |
| OQ-06 | Closed for EPIC-06 contracts: Observation payload reachability **not required** (OQ-01). Provenance ID enrichment is out of contract scope |
| OQ-08 | Closed via OQ-01: ProfileFeature identity authoritative; Observation-only Master Plan wording = drift |
| OQ-09 | Closed for EPIC-06 binding: implement against **implemented** coaching schema; ADR-025 unrealized fields = documentation drift / debt — **no EPIC-06 redesign**. ADR amendment is optional later cleanup, not a Contracts blocker |

---

## 3. Presentation Contract Inventory

### PC-E01 — NarrativeInsight evidence (domain, read-only for EPIC-06)

| Attribute | Value |
|---|---|
| **Owner** | Domain narrative (ADR-023) |
| **Producer** | NarrativeGenerator → `Report.narrative` via `report_node` / `ReportBuilder` |
| **Consumer (EPIC-06)** | `FinalReportDTO.from_report` only |
| **Contract boundary** | EPIC-06 **reads** `source_feature_id`, `is_traceable` (and existing EPIC-05 insight fields). EPIC-06 **does not write** domain narrative |
| **Source of truth** | `Report.narrative.insights[*]` |

### PC-E02 — NarrativeInsightDTO explainability extension

| Attribute | Value |
|---|---|
| **Owner** | EPIC-06 presentation (extends EPIC-05 PC-03) |
| **Producer** | `FinalReportDTO.from_report` — **sole factory** |
| **Consumer** | Narrative section (C-20); export path (C-26) |
| **Contract boundary** | Additive fields on existing DTO host: MUST include projection of `source_feature_id` and `is_traceable`. Exact serialization shape → Data Model |
| **Forbidden** | Second factory; SessionHistory; Observation store; inventing anchors |

### PC-E03 — CoachingAction presentation

| Attribute | Value |
|---|---|
| **Owner** | EPIC-06 presentation |
| **Producer** | `FinalReportDTO.from_report` from `Report.coaching_snapshot.collection.actions` |
| **Consumer** | Coaching explainability / actions surface (existing coaching host sections / renderer composition — mechanism unresolved) |
| **Contract boundary** | Every action on the snapshot that is included in presentation MUST appear with origin fields resolved per EC-C-01. Exact DTO type name/fields → Data Model |
| **Forbidden** | Rendering actions without origin; reading SessionHistory / Observation store |

### PC-E04 — Coaching action origin (LearningObjective)

| Attribute | Value |
|---|---|
| **Owner** | Domain coaching — `LearningObjective` |
| **Producer** | CoachingEngine (already on snapshot) |
| **Consumer** | `FinalReportDTO.from_report` (origin projection for actions; optional enrichment of `CoachingObjectiveDTO`) |
| **Contract boundary** | Origin identity for an action is the parent objective’s evidence fields on the **same** Report snapshot. Minimum origin fields: `feature_type`, `supporting_observation_types` |
| **Not owner** | Scoring-narrative knowledge gaps; undocumented KnowledgeGap type |

### PC-E05 — Explainability projection validation gate

| Attribute | Value |
|---|---|
| **Owner** | EPIC-06 presentation / projection validation |
| **Producer** | Validation executed on `from_report` mapping and/or immediate pre-render of Report-owned explainability sections |
| **Consumer** | Report HTML path and export path (parity) |
| **Contract boundary** | Enforces EC-V-01 / EC-N-01 / EC-C-01. Fail-fast on required-field absence. No silent drop |
| **Forbidden** | UI-only soft-hide of missing required anchors; LLM calls; recomputation |

### PC-E06 — FinalReportDTO sole factory (inherited host)

| Attribute | Value |
|---|---|
| **Owner** | Application presentation (ADR-033 / EPIC-05 PC-02) |
| **Producer** | `FinalReportDTO.from_report` — unchanged sole factory |
| **Consumer** | All Report-owned sections including explainability |
| **Contract boundary** | EPIC-06 extends mapped fields only. Does not create a parallel DTO path |

---

## 4. Contract Boundaries by Layer

### 4.1 Report responsibilities

- Remain sole authoritative session report artifact (ADR-033).
- Continue to embed `narrative`, `coaching_snapshot`, `profile_snapshot` as today.
- **No new Report writer** for EPIC-06.
- **No** requirement to embed Observation payloads or KnowledgeGap entities.

### 4.2 DTO responsibilities

- Sole projection of Report → presentation via `from_report`.
- Add explainability fields for insights and actions + resolved origins.
- Enforce projection completeness (PC-E05) for required explainability fields.
- Export must use the same sole factory (parity).

### 4.3 Presentation responsibilities

- Render candidate-visible evidence for insights and action origins from DTO only.
- Must not dual-read SessionHistory / Observation store / domain `Report` bypass of DTO on production path.
- Presentation **mechanism** (layout/interaction) is **out of this document**.
- Must not silently omit required explainability fields.

### 4.4 Narrative responsibilities

- Domain remains sole writer of `NarrativeInsight` evidence identity (ADR-023).
- EPIC-06 does not change NarrativeGenerator.
- EPIC-06 surfaces existing `source_feature_id` / `is_traceable`.

### 4.5 Coaching responsibilities

- Domain remains sole writer of `LearningObjective` / `CoachingAction` on `CoachingSnapshot`.
- EPIC-06 does not change CoachingEngine schema.
- EPIC-06 projects actions + parent-objective origin fields already present.
- ADR-025 unrealized FKs are **not** EPIC-06 coaching responsibilities.

---

## 5. Traceability Matrix

Every Master Plan EPIC-V13-06 / P-06 requirement maps **exactly once**. Exactly one owner per row.

| # | Master Plan Requirement | Domain / Presentation Contract | Sole Owner | Consuming Component | Verification Artifact |
|---|---|---|---|---|---|
| R-01 | Every `NarrativeInsight` surfaces its evidence anchor (I-15 candidate-visible) | PC-E01, PC-E02; EC-N-01 | EPIC-06 presentation (maps domain ADR-023 fields) | C-20 NarrativeSection (+ export C-26) | Contract/unit test: each insight DTO carries `source_feature_id` + `is_traceable`; UI/export consume them |
| R-02 | Every `CoachingAction` surfaces its origin (“KnowledgeGap origin” Master Plan phrase) | PC-E03, PC-E04; EC-C-01 | EPIC-06 presentation (origin = parent `LearningObjective`) | Coaching explainability surface / renderer composition | Contract/unit test: each action DTO resolves parent objective evidence fields from same snapshot |
| R-03 | Validate evidence references before report is rendered | PC-E05; EC-V-01 | EPIC-06 projection validation gate | C-01 / C-02 / C-06 / C-26 paths | Test: missing required explainability field → fail-fast; no silent omit |
| R-04 | Missing-anchor handling (Master Plan graceful language) | §2.3; EC-V-01 | EPIC-06 contracts (fail-fast class) | Projection gate | Architectural test: forbidden silent suppression of required anchors |
| R-05 | Explainability is a report section concern on Unified Report host | PC-E06; EPIC-05 host | EPIC-06 on ADR-033 / EPIC-05 surfaces | C-02, C-04–C-06, C-20, coaching hosts | Traceability: no standalone explainability pipeline; sole `from_report` |
| R-06 | No dual-read / LLM-free projection preserved | §4; AA-04 | EPIC-06 presentation (inherits ADR-033) | All report presentation components | Architectural test: no SessionHistory / Observation-store reads on explainability path; no LLM |
| R-07 | Platform explainable by design (P-06 / go-live checklist) | R-01 + R-02 + R-03 aggregate | EPIC-06 (not EPIC-05) | Report UI | Epic acceptance: every insight/action in fixtures surfaces required origin fields |

**Excluded / non-rows:** Observation payload embedding; KnowledgeGap type introduction; presentation mechanism UX; ADR-025 schema redesign.

**Status:** 7/7 in-scope requirements mapped exactly once. No duplicate ownership. No unmet in-scope requirement under contractual interpretations §2.1–§2.3.

---

## 6. Architecture Assumptions Register

| ID | Status | Justification ( Domains Contracts) |
|---|---|---|
| AA-01 | **VERIFIED** | Unchanged — EPIC-05 host + PC-E06 additive extension |
| AA-02 | **INVALIDATED** | Remains invalidated as originally worded (“sufficient for Observation anchoring”). **Superseding contract:** ProfileFeature identity is authoritative (OQ-01 / EC-N-01) |
| AA-03 | **INVALIDATED** | Remains invalidated (`source_gap_id` absent). **Superseding contract:** LearningObjective origin chain (OQ-02 / EC-C-01) |
| AA-04 | **VERIFIED** | Constraint + **feasibility**: required evidence fields already on `Report` narrative/coaching snapshot; no new persistence writers; no Observation/KnowledgeGap payload requirement |
| AA-05 | **UNVERIFIED** | Presentation mechanism still unresolved — Data Model / later planning |
| AA-06 | **VERIFIED** | OQ-03 resolved: fail-fast domain/projection class; not presentation degradation (EC-V-01) |
| AA-07 | **VERIFIED** (for Contracts gate) | Ownership resolved by ADR-023 + ADR-033 + implemented coaching binding; **ADR step likely not required**. Reconfirm at Architecture Review after Data Model |
| AA-08 | **INVALIDATED** | Remains invalidated for Master Plan-named Observation/KnowledgeGap **payloads**. **Superseding contract:** those payloads are **not** EPIC-06 required inputs; Report-plane ProfileFeature identity + LearningObjective fields are |
| AA-09 | **VERIFIED** | Discovery inventory stands; Contracts consume existing hosts |
| AA-10 | **VERIFIED** | Unchanged |

**VERIFIED:** AA-01, AA-04, AA-06, AA-07, AA-09, AA-10. **INVALIDATED:** AA-02, AA-03, AA-08. **UNVERIFIED:** AA-05.

---

## 7. Open Findings

| ID | Finding | Class |
|---|---|---|
| OF-01 | Concrete presentation mechanism (layout/interaction) unresolved | **INFORMATION** (not ownership) |
| OF-02 | Exact DTO field tables / `FeatureIdentity` serialization / action DTO shape | **WARNING** — reserved for **Data Model** |
| OF-03 | ADR-025 / Domain Freeze KnowledgeGap documentation drift remains historical debt outside EPIC-06 redesign | **INFORMATION** — optional later ADR/docs cleanup; not a Contracts blocker |
| OF-04 | Whether objective-level DTO also duplicates origin fields (in addition to action-level) for UX clarity | **INFORMATION** — Data Model / mechanism; ownership already allows optional enrichment under PC-E04 |

**BLOCKER:** none remaining for Domain Contracts ownership.

---

## 8. Candidate ADR Evaluation

| Item | Result |
|---|---|
| ADR-023 | **Sufficient** — narrative evidence ownership |
| ADR-033 | **Sufficient** — Unified Report projection plane |
| ADR-016 | **Sufficient** as Observation substrate; **not** an EPIC-06 presentation source |
| ADR-025 | **Not used as binding schema** for EPIC-06; unrealized fields classified as documentation drift. **No new ADR required** to freeze that classification for ownership |
| New ADR | **Likely not required** after Domain Contracts. Re-evaluate only if Data Model introduces a new sole-writer, persistence shape, or ownership conflict |

**ADR step prediction:** **SKIP likely** at Architecture Review, pending Data Model confirmation that no new ownership decision appears.

---

## 9. Forbidden Scope (contractual)

| Forbidden | Reason |
|---|---|
| New `KnowledgeGap` domain type in EPIC-06 | Documentation drift; redesign out of scope |
| Adding `source_gap_id` to `CoachingAction` in EPIC-06 | ADR-025 unrealized; redesign out of scope |
| Observation store / SessionHistory reads from report explainability UI | Dual-read / AA-04 |
| Silent omission of required explainability fields | EC-V-01 |
| Parallel presentation factory | ADR-033 |
| LLM / reasoner recomputation for explainability | ARC-01 P-01 |
| Using scoring-narrative knowledge gaps as coaching-action origin | OQ-05 / EC-C-02 |

---

## 10. Recommendation

**Next engineering task (exactly one):**  
**Produce the Data Model Specification for EPIC-V13-06** — freeze field tables for narrative explainability DTO fields, coaching action + origin projection, and projection-validation rules under EC-N-01 / EC-C-01 / EC-V-01. Do not author an ADR unless Data Model surfaces a new ownership conflict. Do not select presentation mechanism beyond data required for surfaces.

---

## 11. Playbook §8.2 Definition of Done Checklist

| Criterion | Status |
|---|---|
| Every new/changed artifact has ownership, producer, consumers, lifecycle | YES (§1.3, §3) |
| Sole writer / sole presentation API declared | YES |
| Traceability Matrix complete; each requirement once | YES (§5) |
| No untraced field mandate without consumer | YES (field shapes deferred to Data Model deliberately) |
| No unmet Master Plan requirement under contractual interpretation | YES (§2, §5) |
| No alternatives evaluation (ADR job) | YES |
| No Data Model / ADR / implementation | YES |

---

*Domain Contracts complete. Ownership and evidence contracts frozen at contract level. Data Model next.*
