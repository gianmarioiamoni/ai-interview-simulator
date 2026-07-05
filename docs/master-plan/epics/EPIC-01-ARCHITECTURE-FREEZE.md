# EPIC-01 — Architecture Freeze

**Status:** ARCHITECTURE FROZEN  
**Date:** 2026-07-05  
**Reviewer:** Architecture  
**Precondition:** All four planning documents complete and read in full for cross-document verification.

**Documents reviewed:**
- `docs/master-plan/epics/EPIC-01-UNIFIED-REPORT.md` (planning, 474 lines)
- `docs/decisions/adr-033-unified-report-architecture.md` (accepted, 365 lines)
- `docs/master-plan/epics/EPIC-01-DOMAIN-CONTRACTS.md` (authoritative, 544 lines)
- `docs/master-plan/epics/EPIC-01-DATA-MODEL.md` (frozen, 522 lines)

---

## Authority Hierarchy

When documents conflict, the following precedence applies:

1. **ADR-033** — architectural decisions (Accepted; governs all other documents)
2. **EPIC-01-DATA-MODEL** — frozen data model; explicitly supersedes DOMAIN-CONTRACTS §1 (ScoringDimension) and resolves DOMAIN-CONTRACTS §10 open items
3. **EPIC-01-DOMAIN-CONTRACTS** — authoritative for field-level contracts except where DATA-MODEL supersedes
4. **EPIC-01-UNIFIED-REPORT** — planning document; **stale on four points** relative to ADR-033 (see below); the ADR governs where they conflict

This hierarchy is binding on all implementers. EPIC-01-UNIFIED-REPORT is not superseded in full — only in the four specific areas noted below.

---

## Verification Results

### 1. Architectural Contradictions

**Finding 1.1 — Scoring field shape on `Report`**

`EPIC-01-UNIFIED-REPORT` (written before ADR-033) describes scoring fields as flat fields on `Report`. ADR-033 Decision 1 and DOMAIN-CONTRACTS §1 introduce `ScoringSnapshot` as a nested artifact at `Report.scoring`.

**Classification: NOTE.** ADR-033 supersedes. `EPIC-01-UNIFIED-REPORT` is the stale document. No blocking ambiguity — ADR decision is unambiguous.

---

**Finding 1.2 — Coaching narrative ownership and assembler lifecycle**

`EPIC-01-UNIFIED-REPORT` describes `EvaluationNarrativeAssembler` as deleted and coaching narrative fields promoted to typed domain structures directly on `Report`. ADR-033 Decision 4 clarifies: `EvaluationNarrativeAssembler` is **refactored** (not deleted) to produce `ScoringNarrative`; the two coaching surfaces (`scoring_narrative` and `coaching_snapshot`) are kept separate and both embedded in `Report`.

**Classification: NOTE.** ADR-033 supersedes. Implementers must follow ADR-033 Decision 4: assembler is refactored, `EvaluationNarrativeAssembler` survives, `InterviewEvaluationService` survives in refactored form.

---

**Finding 1.3 — Coaching UI section count**

`EPIC-01-UNIFIED-REPORT` describes a single new `render_coaching` section. ADR-033 Decision 4 specifies two new sections: `render_coaching_objectives` and `render_study_recommendations` from `coaching_snapshot`, plus existing sections (`render_went_well`, `render_held_you_back`, etc.) re-sourced from `scoring_narrative`.

**Classification: NOTE.** ADR-033 supersedes. No blocking ambiguity.

---

**Finding 1.4 — `ScoringSnapshot` dimension representation**

DOMAIN-CONTRACTS §1 specifies `dict[str, float]` for dimension scores. DATA-MODEL §2 explicitly supersedes this with `scoring_dimensions: tuple[ScoringDimension, ...]` as the canonical structure, with three derived dict fields. DATA-MODEL §2 states "Supersedes the field set in EPIC-01-DOMAIN-CONTRACTS.md §1".

**Classification: NOTE.** DATA-MODEL §2 governs. `ScoringDimension` typed tuple is the canonical implementation target.

---

**Finding 1.5 — Renderer dict key format for `ScoringNarrativeItem`**

`EPIC-01-UNIFIED-REPORT` states "no renderer changes beyond field name alignment." DATA-MODEL §3 and DOMAIN-CONTRACTS §10 specify that `ScoringNarrativeItem.to_dict()` uses a unified `context_detail` key instead of section-specific keys (`impact`, `interview_impact`, `expected_improvement`). This is a breaking change to three renderer functions (`render_held_you_back`, `render_knowledge_gaps`, `render_next_strategy`).

**Classification: WARNING.** Implementers must update the three affected renderers in EPIC-V13-05. The change is specified and unambiguous. It is not a blocker because the exact new interface (`context_detail`) is frozen in DATA-MODEL.

---

**Finding 1.6 — `total_tokens_used` and `context_profile` marked TBD in DOMAIN-CONTRACTS**

DOMAIN-CONTRACTS §10 marks both `total_tokens_used` (source) and `context_profile` (source) as TBD. DATA-MODEL §1 resolves both explicitly: `total_tokens_used` comes from `report.generation_metadata.total_tokens_used` (R-17 forbids `TokenCalculator.calculate(state)`); `context_profile` comes from `report.context_profile`.

**Classification: NOTE.** Resolved by DATA-MODEL. No open TBD remains.

---

### 2. Ownership Ambiguity

**Finding 2.1 — `FinalReportDTO.from_report` timing**

DOMAIN-CONTRACTS R-05 states `from_components` is deleted after EPIC-V13-01 merge. ADR-033 evidence table assigns `final_report_dto.py` rebuild to EPIC-V13-05. These are not contradictory: EPIC-V13-01 deletes `from_components`; EPIC-V13-05 implements `from_report` with full field mapping. Both must ship atomically per ADR-033 invariant I-A — which means EPIC-V13-01 must introduce a minimal `from_report(report)` factory (even if some fields are not yet wired) and EPIC-V13-05 completes it.

**Resolution:** EPIC-V13-01 introduces `from_report` and deletes `from_components` in the same increment. EPIC-V13-05 extends `from_report` with narrative/coaching sections. No parallel factory at any point.

**Classification: NOTE.** No ambiguity remains after this resolution.

---

**Finding 2.2 — `GenerationMetadata` scope not in ADR-033**

DATA-MODEL §1 introduces `GenerationMetadata` (a new artifact with `total_tokens_used`, `total_cost_usd`, `cost_per_question_usd`) on both `SessionHistory` and `Report`. ADR-033 pipeline diagram (Decision 6) does not include `GenerationMetadata`. The DATA-MODEL document explicitly claims authority to "resolve open modelling decisions left by the Domain Contracts document."

**Resolution:** `GenerationMetadata` is in scope. DATA-MODEL authority is established by the Development Playbook §8: the Data Model Specification resolves all open modelling decisions not covered by ADRs. `GenerationMetadata` resolves the open issue "total_tokens_used source" from DOMAIN-CONTRACTS §10. No ADR amendment is required because this is a data modelling decision, not an architectural decision.

**Classification: NOTE.** No blocker.

---

**Finding 2.3 — `context_profile` not in ADR-033 Decision 6 pipeline diagram**

ADR-033 Decision 6 pipeline diagram does not list `context_profile` as a new field on `SessionHistory` or `Report`. DATA-MODEL §1a adds it as required. The ADR diagram is incomplete, not contradictory — it documents the scoring pipeline, not the complete field set.

**Resolution:** DATA-MODEL governs. `context_profile` is a required field. `SessionHistoryBuilder.build()` raises `ValueError` if not set (R-13). No ADR amendment needed.

**Classification: NOTE.** No blocker.

---

**Finding 2.4 — `ReportBuilder.with_question_assessments` vs assembly via `with_session_history`**

DOMAIN-CONTRACTS §7 lists `with_question_assessments` as an explicit setter. DOMAIN-CONTRACTS §7 also states `with_session_history` reads `history.question_results` and assembles the tuple. Two paths are described.

**Resolution:** `ReportBuilder.with_session_history(history)` is the primary assembly path (consistent with the existing pattern). `with_question_assessments(...)` may exist as an explicit setter for test convenience only. In production, `with_session_history` is always the path that populates `question_assessments`. This is the sole-writer constraint: `report_node` calls `ReportBuilder.with_session_history(history)` and then `build()`.

**Classification: NOTE.** Implementer must follow the `with_session_history` primary path. Optional explicit setter is permitted for tests.

---

### 3. Multiple Producers / Multiple Writers

**Finding 3.1 — Sole writer verification**

| Artifact | Declared sole writer | Confirmed in all documents |
|----------|---------------------|---------------------------|
| `ScoringSnapshot` | `EvaluationAggregateNode` (to `InterviewState`) | ✅ |
| `ScoringNarrative` | `EvaluationAggregateNode` (to `InterviewState`) | ✅ |
| `SessionHistory` | `session_close_node` | ✅ |
| `Report` | `report_node` | ✅ |
| `QuestionResultRecord` | `session_close_node` | ✅ |
| `GenerationMetadata` | `session_close_node` | ✅ |
| `context_profile` (on SessionHistory) | `session_close_node` | ✅ |

No artifact has multiple writers. Sole-writer constraint is satisfied across all documents.

---

### 4. Domain Contract Internal Consistency

**Finding 4.1 — V-SH-01 and `Report` required fields**

DOMAIN-CONTRACTS V-SH-01: `SessionHistory` allows `scoring_snapshot` and `scoring_narrative` both `None` (for sessions without evaluation). DOMAIN-CONTRACTS §7 and ADR-033: `Report.scoring` and `Report.scoring_narrative` are **required** fields. This creates a gap: if a session has no evaluation, `ReportBuilder.build()` would raise `ValueError` for missing `scoring`.

**Resolution:** Sessions where `EvaluationAggregateNode` did not run (e.g. session ended without completion) do not produce a `Report`. The `report_node` is a non-fatal node (PAT Cascading Closure). If `session_history.scoring_snapshot is None`, `report_node` logs a warning and skips report construction — `InterviewState.report` remains `None`. The UI routes to a "no report available" state. This is consistent with `UIResponseBuilder._build_report` requiring `state.report is not None`.

This resolution must be stated explicitly in the implementation. It is an architectural decision that was implicit; it is frozen here.

**Classification: NOTE.** Resolution frozen. No blocker.

---

**Finding 4.2 — `NarrativeSectionType` rename**

DOMAIN-CONTRACTS §8 states that `NarrativeSectionType.EXECUTIVE_SUMMARY` rename to `NarrativeSectionType.OVERVIEW` is "an implementation choice left to EPIC-V13-01 implementer." The rename of the field `Narrative.executive_summary` → `Narrative.overview_section` is frozen (R-07); the enum value rename detail is deferred.

**Resolution:** The field rename is frozen. The enum value rename is a naming detail, not a structural decision. Implementer may keep `NarrativeSectionType.EXECUTIVE_SUMMARY` as the enum value and only rename the field. The validator must check `overview_section.section_type == NarrativeSectionType.EXECUTIVE_SUMMARY` (or the renamed enum). Both forms are valid.

**Classification: NOTE.** No blocker.

---

### 5. Data Model Compatibility with ADR-033

All DATA-MODEL decisions are compatible with ADR-033:

| ADR-033 Decision | DATA-MODEL compatibility |
|-----------------|--------------------------|
| D1: `ScoringSnapshot` in `Report.scoring` | DATA-MODEL §7 Report v2.0 table includes `scoring: ScoringSnapshot` (Required) ✅ |
| D2: `QuestionResultRecord` in `SessionHistory` | DATA-MODEL §7 SessionHistory v2.0 table includes `question_results` ✅ |
| D3: `ScoringNarrative` in `Report.scoring_narrative`; `Narrative.overview_section` rename | DATA-MODEL §7 Report v2.0 includes both ✅ |
| D4: Two coaching surfaces | DATA-MODEL §4 mapping table reflects both paths ✅ |
| D5: `scoring_snapshot` replaces `evaluation_result` | DATA-MODEL §7 SessionHistory v2.0 table: `evaluation_result` removed, `scoring_snapshot` added ✅ |
| D6: Target pipeline invariants I-A through I-G | DATA-MODEL confirms single factory (R-05), sole writers (§3), no parallel paths ✅ |

**DATA-MODEL additions not in ADR-033:** `GenerationMetadata` (new artifact), `context_profile` on `SessionHistory` and `Report` (new field), `ScoringDimension` typed structure (extends D1). All are additive, non-contradictory, and within DATA-MODEL's declared authority.

---

### 6. Replay Completeness

DATA-MODEL §5 provides a 24-row verification table. Every report section is confirmed reconstructible from `SessionHistory` v2.0 without LLM calls. The table is complete:

- All scoring fields: via `scoring_snapshot` ✅
- All narrative prose: via `scoring_narrative` ✅
- Per-question data: via `question_results` ✅
- AI hints: via `question_results[i].ai_hint_*` ✅
- Knowledge pipeline: via `knowledge_snapshot` ✅
- Session metadata: via `interview_metadata` ✅
- Context: via `context_profile` ✅
- Token metadata: via `generation_metadata` ✅

Domain invariant I-11 ("Replay never invokes LLM calls") is preserved.

---

### 7. No Remaining Implementation Decisions

Review of all four documents for "TBD", "deferred", "open issue", and "left to implementer":

| Item | Document | Classification | Resolution |
|------|----------|---------------|------------|
| `total_tokens_used` source | DOMAIN-CONTRACTS §10 TBD | Resolved | DATA-MODEL R-17 |
| `context_profile` source | DOMAIN-CONTRACTS §10 TBD | Resolved | DATA-MODEL §1a |
| `NarrativeSectionType` enum rename | DOMAIN-CONTRACTS §8 | NOTE | Implementer chooses enum name; field rename is frozen |
| Sessions without evaluation | DOMAIN-CONTRACTS V-SH-01 gap | NOTE | Resolved above (Finding 4.1): `report_node` skips if `scoring_snapshot is None` |
| `ScoringSnapshotBuilder` dict derivation | DATA-MODEL open issue 1 | NOTE | Implementer must derive dicts from `scoring_dimensions` at construction; R-12 is the constraint |
| `GenerationMetadata` + `scoring` co-presence | DATA-MODEL open issue 2 | NOTE | Warning-level invariant; no error |
| `context_profile` fixture updates | DATA-MODEL open issue 3 | NOTE | Test concern, not architecture |
| Explainability anchor UI affordance | EPIC Phase 4 | NOTE | Deferred by design to EPIC-V13-06; not blocking V13-01/V13-05 |
| `ReportBuilder` path choice | Finding 2.4 | NOTE | Resolved: `with_session_history` is primary |
| `FinalReportDTO.from_report` timing | Finding 2.1 | NOTE | Resolved: V13-01 introduces, V13-05 extends |

**No BLOCKER items remain.** All previously open items are either resolved, deferred by design (EPIC-V13-06 scope), or NOTE-level implementation details that do not require a new ADR.

---

### 8. Document Duplication Check

Each document covers its unique responsibility per the Development Playbook §8:

| Document pair | Overlap check |
|---------------|---------------|
| EPIC-01-UNIFIED-REPORT vs ADR-033 | EPIC-01 describes scope; ADR-033 decides. No content duplication. |
| ADR-033 vs DOMAIN-CONTRACTS | ADR records rationale; DOMAIN-CONTRACTS specifies fields. No duplication. |
| DOMAIN-CONTRACTS vs DATA-MODEL | DOMAIN-CONTRACTS specifies invariants; DATA-MODEL resolves open modelling questions and freezes field tables. Minor overlap on field tables is intentional (DATA-MODEL supersedes where explicitly stated). |
| EPIC-01-UNIFIED-REPORT vs DOMAIN-CONTRACTS | EPIC lists affected files; DOMAIN-CONTRACTS specifies fields. No duplication. |

No structural duplication detected.

---

## Summary of Findings

| # | Finding | Classification |
|---|---------|---------------|
| 1.1 | EPIC-01-UNIFIED-REPORT stale on scoring shape | NOTE |
| 1.2 | EPIC-01-UNIFIED-REPORT stale on assembler lifecycle | NOTE |
| 1.3 | EPIC-01-UNIFIED-REPORT stale on coaching section count | NOTE |
| 1.4 | DOMAIN-CONTRACTS §1 superseded by DATA-MODEL §2 on ScoringDimension | NOTE |
| 1.5 | Renderer dict key change is a breaking change not noted in EPIC | WARNING |
| 1.6 | DOMAIN-CONTRACTS TBD items resolved by DATA-MODEL | NOTE |
| 2.1 | `FinalReportDTO.from_report` timing resolved | NOTE |
| 2.2 | `GenerationMetadata` scope authority resolved | NOTE |
| 2.3 | `context_profile` not in ADR pipeline diagram — DATA-MODEL governs | NOTE |
| 2.4 | `ReportBuilder` path resolved: `with_session_history` primary | NOTE |
| 3.1 | Sole writer constraint verified for all artifacts | NOTE |
| 4.1 | Sessions without evaluation — `report_node` skips; resolution frozen | NOTE |
| 4.2 | `NarrativeSectionType` rename is naming detail, not structural | NOTE |
| 5.x | DATA-MODEL fully compatible with ADR-033 | NOTE |
| 6.x | Replay completeness verified (24 sections) | NOTE |
| 7.x | No remaining TBD or open blocking decisions | NOTE |
| 8.x | No document duplication | NOTE |

**BLOCKER count: 0**  
**WARNING count: 1** (Finding 1.5 — renderer key change; specified and unambiguous)  
**NOTE count: 16**

---

## Implementation Prerequisites Confirmed

Before any implementation begins, the following are confirmed as satisfied:

- [x] ADR-033 accepted and frozen
- [x] Domain contract field sets, types, validation invariants, and ownership rules specified in EPIC-01-DOMAIN-CONTRACTS.md
- [x] Data model decisions frozen in EPIC-01-DATA-MODEL.md
- [x] All open issues from DOMAIN-CONTRACTS resolved in DATA-MODEL
- [x] Every new artifact has a declared sole writer, declared readers, and a declared lifecycle
- [x] `FinalReportDTO.from_report(report)` field mapping complete and every field traceable
- [x] Replay completeness verified: every report section reconstructible from `SessionHistory` without LLM calls
- [x] No open architectural questions remain that require a new ADR before implementation

---

## Architecture Freeze Verdict

**ARCHITECTURE FROZEN**

EPIC-V13-01 implementation may begin. All architectural decisions are frozen. All domain contracts are specified. All data model decisions are resolved. No open architectural questions remain.

The single WARNING (Finding 1.5 — renderer key format change) is a known, specified breaking change to three renderer functions. It does not require a new ADR because the new interface (`context_detail`) is frozen in DATA-MODEL §2 and DOMAIN-CONTRACTS §10. The EPIC-V13-05 implementer must update `render_held_you_back`, `render_knowledge_gaps`, and `render_next_strategy` to read `context_detail` instead of their current section-specific dict keys.

The staleness of EPIC-01-UNIFIED-REPORT on four points (Findings 1.1–1.3, 1.5) does not prevent implementation because the ADR governs over the planning document in all four cases. EPIC-01-UNIFIED-REPORT remains useful as a high-level scope reference; implementers must use ADR-033 + DOMAIN-CONTRACTS + DATA-MODEL as the authoritative implementation specification.

---

*This document is the Architecture Freeze record for EPIC-V13-01. It may not be amended after the freeze date. If implementation reveals an unresolved architectural question, the Stopping Rule (Development Playbook §8) applies: stop, return to ADR, freeze, resume.*
