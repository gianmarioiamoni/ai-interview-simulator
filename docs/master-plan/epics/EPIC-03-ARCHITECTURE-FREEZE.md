# EPIC-03 — Architecture Freeze Certificate

**Status:** FROZEN  
**Epic ID:** EPIC-V13-03  
**Date:** 2026-07-15  
**Declared by:** Architecture Review  
**Gate type:** Blocking — implementation cannot begin before this document is accepted  
**Precondition:** All EPIC-03 planning artifacts complete; all pre-freeze issues resolved.

---

## 1. Frozen Planning Set

The following documents are certified frozen as of this declaration. No implementation may begin against any artifact in this set until this certificate is accepted.

| Document | Status | HEAD Commit |
|---|---|---|
| `EPIC-03-REPLAY-ENGINE.md` | FROZEN | `db28db7` |
| `docs/decisions/adr-037-replay-engine-architecture.md` | ACCEPTED | `db28db7` |
| `EPIC-03-DOMAIN-CONTRACTS.md` | FROZEN | `db28db7` |
| `EPIC-03-DATA-MODEL.md` | FROZEN | `db28db7` |

Any post-freeze change to any document in this set requires a **Freeze Integrity Check** per V13-DEVELOPMENT-PLAYBOOK.md §9.

---

## 2. Authority Hierarchy — Verified

| Level | Authority Document | Status |
|---|---|---|
| Constitutional | ARC-01 (Architecture Constitution) | Active — all decisions verified against P-01 through P-08 |
| Epic Governance | EPIC-03-REPLAY-ENGINE.md | Frozen — no open architectural questions |
| Ownership Decisions | ADR-037 | Accepted — all 5 decisions frozen |
| Contract Specification | EPIC-03-DOMAIN-CONTRACTS.md | Frozen — all contracts complete |
| Data Model | EPIC-03-DATA-MODEL.md | Frozen — all field tables complete, all gaps resolved |

**Hierarchy is consistent.** No document contradicts a document above it. No circular authority references. No undeclared design decisions embedded in lower-level documents.

---

## 3. Review Findings

### 3.1 Authority Hierarchy — PASS

All decisions trace to a single authority source. ADR-037 is the final authority for all ownership, lifecycle, topology, invariant, and scope decisions. Domain Contracts reference ADR-037 decisions by section number. Data Model cross-validates against Domain Contracts and resolves only modelling questions. No authority conflicts.

### 3.2 Document Consistency

| Check | Finding | Classification |
|---|---|---|
| `ReplaySession.session_id` source: Domain Contracts §1.3 states `session_history.interview_metadata.session_id` | `InterviewMetadata` does not carry `session_id`. Data Model §2 (row 1) corrects source to `session_history.session_id`. | **WARNING — DC-01:** Source stated incorrectly in Domain Contracts; Data Model holds the authoritative correction. Implementer must use Data Model §2 as authoritative. No ADR change required. |
| `ReplaySession.candidate_identity_id` source: Domain Contracts §1.3 states `session_history.interview_metadata.candidate_identity_id` | `InterviewMetadata` does not carry `candidate_identity_id`. Data Model §2 (row 2) corrects source to `session_history.candidate_identity_id`. | **WARNING — DC-02:** Same class of error as DC-01. Data Model §2 is authoritative. No ADR change required. |
| `ReplayTimeline` declared in Domain Contracts §4; field `timeline` added to `ReplaySession` with note that it is permitted under ADR-037 Decision 3 §3.4 | ADR-037 Decision 3 §3.4 references EPIC-04 sufficiency; `timeline` is a derived sub-artifact, not a new knowledge source | **PASS — confirmed as Data Model extension within scope of ADR-037 D3.** |
| `company` field added to `ReplaySessionMetadata` in Data Model §3 without declaration in Domain Contracts §3.3 | `company` comes from persisted `InterviewMetadata.company`; it is additive metadata, not a new source | **PASS — additive Data Model clarification; no architectural impact.** |
| `ReplaySession` field count: Domain Contracts §1.3 has 17 rows; Data Model §2 has 18 rows (adds `timeline`) | `timeline` is a required field added by the Data Model layer; not present in the Domain Contracts field specification | **WARNING — DC-03:** `timeline` is not declared in Domain Contracts §1.3 field table. Domain Contracts §4 declares it as a separate section but does not add it to §1.3. Data Model §2 adds it to the `ReplaySession` field table. Implementer should treat Data Model §2 as the authoritative field table for `ReplaySession`. No architectural impact; no ADR amendment required. |
| RG-02 (`session_duration_seconds` aggregation): Data Model classifies this as a read-pass aggregation of persisted records | Sum of `Optional[float]` values — no recomputation of knowledge; no LLM call; fully deterministic when all values non-None | **PASS — within read-pass scope of ADR-037 D2.** |
| All invariants declared in ADR-037 Decision 5 traceable to Domain Contracts §9 and Data Model §11 | I-11, I-R01 through I-R09 all traced | **PASS** |

### 3.3 Ownership Model — PASS

| Artifact | Sole Producer | Sole Writer | Status |
|---|---|---|---|
| `ReplaySession` | `ReplaySessionBuilder` | `replay_node` | CONFIRMED — Domain Contracts §5.2; ADR-037 §1.3 |
| `ReplayManifest` | `replay_node` | `replay_node` | CONFIRMED — Domain Contracts §1.3 |
| `ReplayFeatureEngine` output | `ReplayFeatureEngine` | `replay_node` (passed to builder) | CONFIRMED — Domain Contracts §8 |
| `ReplayTimeline` | `ReplaySessionBuilder` | `replay_node` (via builder) | CONFIRMED — Domain Contracts §4.2 |
| `ReplaySessionMetadata` | `ReplaySessionBuilder` | `replay_node` (via builder) | CONFIRMED — Domain Contracts §3 |
| `ReplayQuestionRecord` | `ReplaySessionBuilder` | `replay_node` (via builder) | CONFIRMED — Domain Contracts §2 |

No artifact has more than one declared producer. No artifact has more than one declared writer. Single Ownership (P-02) satisfied.

### 3.4 Sole-Writer Invariants — PASS

- `replay_node` is the sole writer of `ReplaySession`. Declared in ADR-037 I-R01, Domain Contracts §5.2.
- `replay_node` has zero declared `InterviewState` write targets. Confirmed in ADR-037 §1.3 ("InterviewState field: None").
- `replay_node` has zero declared persistence write targets. Confirmed in ADR-037 I-R07 and Domain Contracts §9.1.
- No other node in the live session graph may write `ReplaySession`. Enforced by architectural test (I-R01).

### 3.5 Builder Ownership — PASS

- `ReplaySessionBuilder` is the sole construction path for `ReplaySession`. Direct constructor invocation prohibited in production code. Confirmed in Domain Contracts §5.2.
- `ReplaySessionBuilder.as_failed(...)` is the only alternate path; it produces a failed `ReplaySession`, not a partial one. Confirmed in Domain Contracts §5.5.
- No Builder contains computation logic. `ReplayFeatureEngine` reads; `ReplaySessionBuilder` assembles. P-05 satisfied.
- No wildcard copy (`**obj.dict()`, unscoped `model_copy`) is permitted. Confirmed in Domain Contracts §9.3 (PI-05).

### 3.6 Replay Reconstruction Completeness — PASS

- Data Model §5 (Traceability Matrix) maps all 18 `ReplaySession` fields to exactly one authoritative source.
- Data Model §6 (Reconstruction Completeness Matrix) confirms all fields are LLM-free and deterministic.
- Three reconstruction gaps (RG-01, RG-02, RG-03) were discovered and resolved within the Data Model layer without requiring ADR amendments.
- P-08 (Reconstruction Completeness) enforced by: Domain Contracts §9.2 (source invariants), Data Model §6, and ADR-037 I-R05 (architectural test mandate).

### 3.7 Determinism — PASS

- Data Model §13 defines the determinism verification model: 23 fields classified; all knowledge fields confirmed deterministic; manifest timestamps explicitly excluded from determinism assertion.
- Determinism test protocol specified: ≥ 20 fixtures, dual-invocation equality check on all knowledge fields. Confirmed in Data Model §13.2.
- Non-determinism failure classification defined: P0 / P1 / P2 with blocking thresholds. Data Model §13.3.

### 3.8 LLM-Free Guarantee (I-11) — PASS

- ADR-037 I-11: "Replay never invokes LLM calls." Declared as domain invariant.
- `ReplayFeatureEngine` explicitly prohibited from invoking any LLM-backed service. Confirmed in Domain Contracts §8.2, ADR-037 Decision 2.
- `ReplaySessionBuilder` contains no LLM calls by design (assembly component, P-05).
- Architectural test mandate: mock all LLM service interfaces; assert zero invocations during `replay_node` execution across all fixtures. ADR-037 I-11, Domain Contracts §9.3 PI-03.
- Data Model §6 reconstruction completeness matrix: LLM-Free = Yes for all 18 fields.

### 3.9 Replay / Longitudinal Isolation — PASS

- ADR-037 I-R06: bidirectional import prohibition between replay contracts and `LongitudinalProfile` contracts.
- Domain Contracts §9.3 PI-01 and PI-02 restate the prohibition at the contract specification level.
- Data Model §5 traceability matrix: no `ReplaySession` field sources from `LongitudinalProfile` or `LearningProgress`.
- Data Model §12 XCI-03 explicitly states isolation.
- No replay field requires longitudinal data. ADR-034 Decision 7 fully satisfied.

### 3.10 Runtime Topology — PASS

- ADR-037 Decision 4: standalone single-node Replay Graph; `replay_node → END`.
- Domain Contracts §7 (`ReplayGraphState`): does not extend `InterviewState`; no live session data.
- Domain Contracts §7.3: `ReplayGraphState` must not reference `InterviewState`. Enforced by architectural test (I-R03).
- Domain Contracts §8.2: Replay Graph checkpointing must be disabled — `ReplaySession` must not be persisted as a LangGraph checkpoint.
- Live session graph and Replay Graph are topologically independent. No shared state. No shared nodes.

### 3.11 Artifact Lifecycle — PASS

- `ReplaySession` not persisted (ADR-037 D1 §1.4, Domain Contracts §9.1, Data Model §8.1).
- `ReplayGraphState` not persisted (Data Model §8.1).
- `ReplaySession` produced on demand; discarded after use. No caching in V1.3.
- `ReplayManifest` is a runtime audit record only; not independently persisted.
- All artifacts `frozen=True`, `extra=forbid` except `ReplayGraphState` (TypedDict by LangGraph convention — correct, documented in Domain Contracts §7.2).

### 3.12 Serialization Consistency — PASS

- Data Model §9 defines serialization rules for all types.
- No replay artifact is serialized to persistence (§9.1).
- API serialization rules defined for all types (§9.2).
- `candidate_answer` empty string serialization rule explicitly declared (§9.4).
- LangGraph checkpoint serialization explicitly prohibited (§8.2).
- Schema version: `ReplaySession.schema_version = "1.0"` constant; `ReplayManifest.replay_engine_version = "1.0"` set by node constant. Distinct concerns correctly separated.

### 3.13 Migration Completeness — PASS

Three migration phases with explicit deletion targets confirmed. All legacy artifacts have declared deletion triggers:

| Legacy Artifact | Deletion Trigger | Phase |
|---|---|---|
| `ReplaySession` (V1.2 orchestrator → `ReplayOrchestrator`) | When `ReplaySession` (V1.3) activated | Phase 3 |
| `ReplayResult` | Same increment as `ReplaySession` (V1.3) activation | Phase 3 |
| `ReplayOrchestrator` | Same as `ReplayResult` deletion | Phase 3 |
| `validate_result` method | Same as `ReplayResult` deletion | Phase 3 |
| `from_result` factory | Same as `ReplayResult` deletion | Phase 3 |

Each phase must leave the regression suite green before the next begins. No compatibility bridge survives Phase 3. Confirmed in Domain Contracts §13 and Data Model §12.

### 3.14 Document Duplication — PASS

- Domain Contracts §9.3 (prohibition invariants) and ADR-037 Decision 5 share invariant definitions — this is intentional restatement for implementer reference, not duplication of authority.
- Data Model §6 re-lists all `ReplaySession` fields with source verification — this is verification, not duplication of Domain Contracts.
- No information appears in two documents with different values except DC-01 and DC-02 (source field path errors in Domain Contracts §1.3, corrected in Data Model §2 — classified as WARNINGs above).

### 3.15 Hidden Implementation Decisions — PASS

No implementation decision was discovered hidden inside a planning document:
- `session_duration_seconds` aggregation (sum of `question_timeline[*].duration_seconds`) is a data assembly rule, not a computation — correctly kept in the Data Model.
- `candidate_answer` join by `question_id` (Data Model §4.1) is a read-pass assembly rule — correctly kept in the Data Model, not elevated to an ADR.
- All architectural choices trace to ADR-037.

### 3.16 Remaining Architectural Decisions — PASS

All open issues from EPIC-03-REPLAY-ENGINE.md (OI-01 through OI-04) and ADR-037 are resolved. Data Model §Open Issues confirms zero remaining open issues.

---

## 4. RG-03 Review — follow_up_question Classification

**Finding: RG-03 is an additive clarification. No ADR update is required.**

**Evidence:**

1. `follow_up_question` is a field already persisted in `QuestionResultRecord` (in `SessionHistory`). It was not introduced by EPIC-03 — it pre-exists in the closed persistence layer.

2. Omitting it from `ReplayQuestionRecord` was a Domain Contracts omission, not an architectural decision. No ADR governs the exclusion of `follow_up_question`.

3. Adding `follow_up_question: Optional[str]` to `ReplayQuestionRecord` does not:
   - Introduce a new data source not already present in `SessionHistory`.
   - Cross any constitutional boundary (Computation/Projection, Ownership, Replay, Longitudinal, or Presentation).
   - Introduce computation (it is a verbatim read of a persisted field).
   - Require a new builder, engine, or node.
   - Create a second ownership path for any artifact.

4. ADR-037 Decision 3 §3.4 explicitly states: "EPIC-04 may choose not to render certain optional fields — that is a UI rendering decision, not a replay contract change." The converse is also true: adding an optional persisted field to the replay projection is a projection decision, not an architectural change.

5. The field is `Optional[str]` with default `None` — additive, backward-compatible, no version increment required.

**Conclusion: Domain Contracts §2.3 is extended by Data Model §4 (RG-03 resolution). This is within the Data Model document's authority. No ADR amendment is required. No Freeze Integrity Check is triggered beyond the normal review of this Data Model.**

---

## 5. Architecture Freeze Decision

### 5.1 Finding Summary

| ID | Finding | Classification |
|---|---|---|
| DC-01 | `session_id` source path incorrect in Domain Contracts §1.3; correct in Data Model §2 | WARNING |
| DC-02 | `candidate_identity_id` source path incorrect in Domain Contracts §1.3; correct in Data Model §2 | WARNING |
| DC-03 | `timeline` field present in Data Model §2 but not in Domain Contracts §1.3 field table | WARNING |
| RG-01 | `session_date` → `SessionHistory.created_at` | RESOLVED (Data Model §1.2) |
| RG-02 | `session_duration_seconds` → aggregation of `question_timeline` | RESOLVED (Data Model §1.2) |
| RG-03 | `follow_up_question` omitted from Domain Contracts | RESOLVED — additive clarification; no ADR required |
| All 16 review checks | Authority hierarchy, ownership, builders, determinism, LLM-free, isolation, topology, lifecycle, serialization, migration | PASS |

**BLOCKER findings: 0**  
**WARNING findings: 3** (DC-01, DC-02, DC-03 — all source path corrections; Data Model is authoritative; no implementation risk)  
**PASS: 16 of 16 checks**

### 5.2 Architecture Freeze: DECLARED

**Architecture Freeze is DECLARED for EPIC-03 — Replay Engine.**

All decisions required for implementation are frozen, unambiguous, and consistent. Three WARNINGs are recorded; all are source-path clarifications with Data Model §2 as the authoritative resolution. No WARNING affects the implementation — implementers must use Data Model §2 as the field table, not Domain Contracts §1.3, for the three affected fields.

**Implementation may begin.**

The Implementation Plan (EPIC-03-IMPLEMENTATION-PLAN.md) is the next mandatory document before coding begins.

---

## 6. Remaining Implementation Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| `ReplayOrchestrator` rename breaks imports not identified during planning audit | Low | Phase 1 regression suite must pass before Phase 2 begins; any import error surfaces immediately |
| `candidate_answer` join by `question_id` fails for sessions where `TranscriptEntry.question_id` is absent or inconsistent | Low | `ReplaySessionBuilder` must handle missing join with `candidate_answer = ""` (defined in Data Model §4.1); test with fixture where join fails |
| `session_duration_seconds` aggregation returns `None` unexpectedly for most sessions (if `question_timeline` entries commonly lack `duration_seconds`) | Medium | Profile a representative fixture set before Phase 2; if most sessions produce `None`, the field is informational only and EPIC-04 must render "Not available" gracefully |
| `scoring_snapshot` and `scoring_narrative` pairing invariant (V-SH-01) produces validation errors for sessions from before EPIC-01 | Low | EPIC-01 is CLOSED; all sessions in the live system use `SessionHistory` v2.0; pre-v2.0 sessions do not exist in production |
| `ReplayLevel.REASONING` guard not enforced uniformly across entry points | Low | Architectural test must validate all entry points to `replay_node` reject `REASONING` level; `ReplayRequest` validator enforces it at input |
| LangGraph checkpointing inadvertently persists `ReplayGraphState` | Low | Replay Graph must be instantiated with checkpointing disabled; verified by test that asserts no checkpoint writes occur during `replay_node` execution |

---

## 7. Open Issues

None. All pre-freeze issues are resolved.

Three WARNINGs (DC-01, DC-02, DC-03) are recorded in the finding summary. These are source-path documentation errors in Domain Contracts §1.3, authoritatively corrected by Data Model §2. They do not block implementation. They do not require ADR amendments. The Domain Contracts document is not retroactively modified — the Data Model is the authoritative override for these three fields per the document responsibility hierarchy.

---

*This certificate declares EPIC-03 Architecture Freeze. Implementation of EPIC-03 production code may begin only after this certificate is accepted. Any modification to a frozen planning document after this declaration requires a Freeze Integrity Check per V13-DEVELOPMENT-PLAYBOOK.md §9.*
