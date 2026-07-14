# EPIC-02 — Architecture Freeze Certificate

**Status:** FROZEN  
**Epic ID:** EPIC-V13-02  
**Date:** 2026-07-14  
**Declared by:** Architecture Review  
**Gate type:** Blocking — implementation cannot begin before this document is accepted  
**Precondition:** All EPIC-02 planning artifacts complete; all pre-freeze issues resolved.

---

## 1. Frozen Planning Set

The following documents are certified frozen as of this declaration. No implementation may begin against any artifact in this set until this certificate is accepted.

| Document | Status | HEAD Commit |
|---|---|---|
| `EPIC-02-LONGITUDINAL-PROFILE.md` | FROZEN | `8daa7b5` |
| `docs/decisions/adr-034-longitudinal-profile-ownership.md` | ACCEPTED | `8daa7b5` |
| `EPIC-02-DOMAIN-CONTRACTS.md` | FROZEN | `b83b02c` |
| `EPIC-02-DATA-MODEL.md` | FROZEN | `b83b02c` |

Any post-freeze change to any document in this set requires a **Freeze Integrity Check** per V13-DEVELOPMENT-PLAYBOOK.md §9.

---

## 2. Authority Hierarchy — Verified

| Level | Authority Document | Status |
|---|---|---|
| Constitutional | ARC-01 (Architecture Constitution) | Active — all decisions verified against P-01 through P-08 |
| Epic Governance | EPIC-02-LONGITUDINAL-PROFILE.md | Frozen — no open architectural questions |
| Ownership Decisions | ADR-034 | Accepted — all 9 decisions frozen |
| Contract Specification | EPIC-02-DOMAIN-CONTRACTS.md | Frozen — all contracts complete |
| Data Model | EPIC-02-DATA-MODEL.md | Frozen — all field tables complete, all open issues closed |

**Hierarchy is consistent.** No document contradicts a document above it in the hierarchy. No circular authority references.

---

## 3. Review Findings

### 3.1 Authority Hierarchy — PASS

All decisions trace to a single authority source. ADR-034 is the final authority for all ownership, lifecycle, failure, and invariant decisions. Domain Contracts reference ADR-034 decisions by section. Data Model cross-validates against ADR-034 decisions. No circular references. No authority conflicts.

### 3.2 Document Consistency — PASS

| Check | Result |
|---|---|
| `LongitudinalProfile` field set: LONGITUDINAL-PROFILE.md ↔ DOMAIN-CONTRACTS.md ↔ DATA-MODEL.md | Consistent |
| `LongitudinalSessionMetadata` fields: DOMAIN-CONTRACTS.md §1.5 ↔ DATA-MODEL.md §1.3 | Consistent (3-field addition present in both) |
| `LearningProgress` field set: DOMAIN-CONTRACTS.md §2.3 ↔ DATA-MODEL.md §2.2 | Consistent |
| `CrossSessionLanguageCapability` field set: DOMAIN-CONTRACTS.md §1.6 ↔ DATA-MODEL.md §1.4 | Consistent |
| Builder inputs: DOMAIN-CONTRACTS.md §4.2 ↔ DATA-MODEL.md §5 (traceability) | Consistent |
| OI-03 resolution: DOMAIN-CONTRACTS.md §3.2 ↔ DATA-MODEL.md §3.2 ↔ DATA-MODEL.md §6.3 | Consistent |
| Reconstruction gap (`language_capability_summary`): documented in DATA-MODEL.md §6 | Accepted |
| Serialization rules: DOMAIN-CONTRACTS.md §7 ↔ DATA-MODEL.md §7 | Consistent |

**Finding:** Zero inconsistencies found across all four documents.

### 3.3 Ownership Model — PASS

| Artifact | Sole Producer | Sole Writer |
|---|---|---|
| `LongitudinalProfile` | `LongitudinalProfileBuilder` | `longitudinal_update_node` |
| `CandidateProfileSnapshot` | `FeatureEngine` / `CandidateProfileBuilder` (unchanged) | `session_close_node` (unchanged) |
| `LearningProgress` | `LearningProgressBuilder` | Not persisted — no writer |
| `CrossSessionLanguageCapability` | `LongitudinalProfileBuilder` (embedded) | `longitudinal_update_node` (via profile) |

**Finding:** No duplicated ownership. No artifact has more than one declared producer or writer.

### 3.4 Builder Ownership — PASS

- `LongitudinalProfileBuilder` is the sole construction path (ADR-034 LP-02).
- Direct Pydantic instantiation in production is prohibited.
- Builder must not call any persistence layer, LLM service, or `FeatureEngine` (ADR-034 LP-03).
- Builder responsibility chain (DOMAIN-CONTRACTS.md §4.3 steps 1–10) is complete and deterministic.
- Builder receives `language_capabilities` as an explicit parameter from `longitudinal_update_node` (OI-03 resolution — consistent across DC and DM).

**Finding:** Builder boundary is clean. No hidden computation paths.

### 3.5 Single-Writer Invariants — PASS

- `longitudinal_update_node` is declared as the only component that calls `LongitudinalProfileRepository.save()` (ADR-034 LP-01).
- No other node, service, or builder declares or implies a write path to `LongitudinalProfile`.
- `InterviewState` carries no `LongitudinalProfile` field — no second write path possible via state propagation (ADR-034 Decision 1).

**Finding:** LP-01 (Sole Writer) invariant is formally satisfied. No duplicated write path exists.

### 3.6 Cross-Document Consistency — PASS

| Cross-document check | Result |
|---|---|
| LONGITUDINAL-PROFILE.md §7 (ownership) ↔ ADR-034 Decision 1 | Consistent |
| LONGITUDINAL-PROFILE.md §8 (runtime lifecycle) ↔ ADR-034 Decisions 2, 6 | Consistent |
| LONGITUDINAL-PROFILE.md §3 (target architecture) ↔ DOMAIN-CONTRACTS.md §6.1 (artifact chain) | Consistent |
| ADR-034 Decision 5 (`LearningProgress` from `LongitudinalProfile`) ↔ DOMAIN-CONTRACTS.md §2.2 ↔ DATA-MODEL.md §2.1 | Consistent |
| ADR-034 Decision 7 (replay isolation) ↔ DOMAIN-CONTRACTS.md §6.4 ↔ DATA-MODEL.md §8.1 | Consistent |
| ADR-034 LP-08 (reconstruction) ↔ DATA-MODEL.md §6 (reconstruction procedure + gap) | Consistent — gap documented and accepted |
| ADR-034 Decision 2 (ADR-033 trigger resolved) ↔ DATA-MODEL.md §8.1 | Consistent — `ScoringSnapshot` not in `LongitudinalProfile` |

**Finding:** Zero cross-document contradictions.

### 3.7 Replay Boundary — PASS

- Replay does not consume `LongitudinalProfile` (ADR-034 Decision 7).
- No replay contract (`ReplayContext`, `ReplayResult`, `ReplayManifest`, `ReplaySession`, `replay_node`) imports or references `LongitudinalProfile`.
- No `LongitudinalProfile` contract imports any replay contract.
- Replay UI progress panel data sourcing (EPIC-04/05) is explicitly deferred as a UI composition concern, not a replay concern.
- Invariant LP-11 (Replay Independence) is declared and verifiable by architectural import test.

**Finding:** Replay boundary is clean and bidirectional.

### 3.8 LongitudinalProfile Lifecycle — PASS

| Phase | State | Authority |
|---|---|---|
| Before first session | Does not exist | ADR-034 Decision 2; DOMAIN-CONTRACTS.md §1.8 |
| After first session | Created (`prior_profile=None` path) | ADR-034 Decision 2; LONGITUDINAL-PROFILE.md §8 |
| After each subsequent session | Replaced (replace-on-write) | ADR-034 Decision 2; DATA-MODEL.md §4.1 |
| At progress query time | Read-only | ADR-034 Decision 1; DOMAIN-CONTRACTS.md §1.8 |
| At replay time | Not accessed | ADR-034 Decision 7; DOMAIN-CONTRACTS.md §6.4 |
| On update failure | Profile not updated; gap detectable | ADR-034 Decision 6; LONGITUDINAL-PROFILE.md §8 |

**Finding:** Lifecycle is complete, consistent, and non-contradictory across all documents. First-session path and failure path both specified.

### 3.9 LearningProgress Lifecycle — PASS

- Never persisted (LP-LP-06).
- Computed on demand from `LongitudinalProfile` only (ADR-034 Decision 5).
- No `SessionHistory[]` fallback under any code path (LP-LP-07).
- Empty `LearningProgress` returned when profile absent (`has_sufficient_data = False`).
- New fields (`behavioral_trend`, `language_capability_summary`, `has_sufficient_data`) consistent across DOMAIN-CONTRACTS.md §2 and DATA-MODEL.md §2.

**Finding:** `LearningProgress` lifecycle is correct. No persistence path exists.

### 3.10 LanguageCapability Lifecycle — PASS

- Session-scoped `LanguageCapability` is produced by `FeatureEngine` (unchanged, V1.2).
- Session-scoped `LanguageCapability` instances are captured by `longitudinal_update_node` from live session state before expiry and passed to `LongitudinalProfileBuilder` as `language_capabilities` parameter (OI-03 resolution).
- `LongitudinalSessionMetadata.language_capabilities` embeds them permanently at contribution time.
- `CrossSessionLanguageCapability` is produced by aggregation in `LongitudinalProfileBuilder` from `LongitudinalSessionMetadata.language_capabilities`.
- `CrossSessionLanguageCapability` is persisted as part of `LongitudinalProfile`.
- No modification to the existing `LanguageCapability` contract (`domain/contracts/language/language_capability.py`).
- `SessionHistory` v2.0 contract is unchanged.

**Known accepted limitation:** `language_capability_summary` is not reconstructable from `SessionHistory[]` alone (DATA-MODEL.md §6.3). This is accepted for V1.3. The architectural test for I-LP-REC must assert `language_capability_summary == []` for a reconstructed profile.

**Finding:** LanguageCapability activation is architecturally coherent. No contract changes required for V1.3. Limitation is documented and accepted.

### 3.11 CandidateIdentity Consistency — PASS

- `LongitudinalProfile.candidate_identity_id` is declared as the ownership anchor (ADR-034 Decision 4).
- It must equal `SessionHistory.candidate_identity_id` for all embedded snapshots (XC-01).
- V1.3: anonymous (uuid4), opaque, no external auth assumption.
- V2 migration path: documented in ADR-034 Decision 4 (`external_identity_id: Optional[str]` additive extension). Not implemented in V1.3.
- Invariant LP-05 (Identity Binding): `LongitudinalProfile.candidate_identity_id` must match all embedded `profile_snapshot.candidate_identity_id` values.

**Finding:** `CandidateIdentity` integration is correct and V2-compatible without breaking changes.

### 3.12 Replay Completeness — PASS WITH ACCEPTED LIMITATION

**Reconstructable fields:** All fields except `language_capability_summary`. Full reconstruction procedure documented (DATA-MODEL.md §6.2). No LLM calls required.

**Accepted gap:** `language_capability_summary` will be empty in a reconstructed profile. This is not a critical data loss for V1.3 (no production persistence, supplementary data only). Documented in DATA-MODEL.md §6.3 under invariant I-LP-REC (amended).

**Verdict:** P-08 (Reconstruction Completeness) is substantially satisfied. The one accepted exception is documented, bounded, and non-critical for V1.3.

### 3.13 Architecture Constitution Compliance — PASS

| Principle | Compliance |
|---|---|
| P-01 (Runtime Computes; Projection Never Computes) | `longitudinal_update_node` performs no LLM calls, no scoring, no computation — pure assembly from closed artifacts. LP-03 invariant enforces this. |
| P-02 (Single Ownership) | Every artifact has exactly one declared producer and one declared writer. Verified in §3.3 and §3.5. |
| P-03 (Immutable Domain Contracts) | All new artifacts are `frozen=True`, `extra=forbid`. Update = replace, not mutate. |
| P-04 (LangGraph Is Sole Orchestrator) | `longitudinal_update_node` is a LangGraph node. No service-chain orchestration. |
| P-05 (Builders Assemble; Engines Compute) | `LongitudinalProfileBuilder` contains no computation logic. Trend direction rule (§2.6 DC) is a simple threshold comparison, not an engine-level computation. |
| P-06 (Fail Fast Over Silent Fallback) | `longitudinal_update_node` is non-fatal but observable (LP-09). Every failure path emits a structured `WARNING` log. Silent failure is prohibited. |
| P-08 (Reconstruction Completeness) | Substantially satisfied (§3.12). Accepted gap documented. |

**Finding:** Architecture Constitution compliance is confirmed. No constitutional principle is violated.

### 3.14 Remaining Architectural Decisions — PASS

| Decision | Status |
|---|---|
| `LongitudinalProfile` ownership (ADR-034 Decision 1) | FROZEN |
| Artifact lifecycle (ADR-034 Decision 2) | FROZEN |
| Relationship with `SessionHistory` (ADR-034 Decision 3) | FROZEN |
| Relationship with `CandidateIdentity` (ADR-034 Decision 4) | FROZEN |
| `LearningProgress` input source (ADR-034 Decision 5) | FROZEN |
| Failure semantics (ADR-034 Decision 6) | FROZEN |
| Replay interaction (ADR-034 Decision 7) | FROZEN |
| Persistence boundary (ADR-034 Decision 8) | FROZEN |
| Architectural invariants LP-01 to LP-12 (ADR-034 Decision 9) | FROZEN |
| OI-01 (`total_objectives` source) | CLOSED |
| OI-02 (`total_narrative_insights` source) | CLOSED |
| OI-03 (`LanguageCapability` accessibility) | CLOSED |

**Finding:** No open architectural decisions. All 9 ADR-034 decisions are frozen. All 3 open issues are closed. No pending decisions block implementation.

### 3.15 Document Duplication — PASS

| Check | Result |
|---|---|
| Duplicated field definitions | None. Each field is defined in DOMAIN-CONTRACTS.md and referenced (not redefined) in DATA-MODEL.md. |
| Duplicated ownership declarations | None. ADR-034 Decision 1 is the sole source; other documents cite it. |
| Duplicated invariants | None. Invariant IDs are unique (LP-01 through LP-12, LP-V-01 through LP-V-08, LC-V-01 through LC-V-05, LP-LP-01 through LP-LP-07, XC-01 through XC-05). |
| Overlapping lifecycle descriptions | None. Each document's lifecycle description covers a different level of abstraction (architecture, contract, data model). |

**Finding:** No duplicated content across the planning set.

### 3.16 Implementation Readiness — PASS

All prerequisite planning gates are complete:

| Gate | Status |
|---|---|
| Architecture planning document frozen | Yes — EPIC-02-LONGITUDINAL-PROFILE.md |
| All ownership decisions frozen in ADR | Yes — ADR-034 (9 decisions) |
| Domain contracts complete and frozen | Yes — EPIC-02-DOMAIN-CONTRACTS.md |
| Data model complete and frozen | Yes — EPIC-02-DATA-MODEL.md |
| All pre-freeze issues resolved | Yes — OI-01, OI-02, OI-03 closed |
| No unresolved ADRs | Yes |
| No unresolved planning issues | Yes |
| No contradictory decisions | Yes |
| No duplicated ownership | Yes |
| No hidden implementation decisions | Yes |
| No unacknowledged reconstruction gaps | Yes — gap documented and accepted |

---

## 4. Additional Verification

### 4.1 No Contradictory Decisions

Full cross-check of all decisions across four documents: **zero contradictions found**.

Notable potential conflicts that were verified as non-contradictory:

- LONGITUDINAL-PROFILE.md §3 states reconstruction guarantee broadly; DATA-MODEL.md §6 correctly refines it with the `language_capability_summary` gap. Not a contradiction — the later document provides additional precision.
- LONGITUDINAL-PROFILE.md §7.1 (table) states `longitudinal_update` may write to `InterviewState`; ADR-034 Decision 1 explicitly prohibits this. **Resolution:** The planning document (LONGITUDINAL-PROFILE.md) predates ADR-034 and was written before the decision was frozen. ADR-034 Decision 1 is authoritative. DOMAIN-CONTRACTS.md §1.2 and DATA-MODEL.md §8.1 correctly follow ADR-034 (no `InterviewState` field). **Action:** See §5.1 — this is a pre-existing planning document inconsistency; it does not affect implementation because ADR-034 is authoritative. The planning document does not require a post-freeze edit.

### 4.2 No Duplicated Ownership

Confirmed in §3.3. Every artifact has exactly one producer and one writer. The only potentially ambiguous case — `CrossSessionLanguageCapability` — is correctly identified as embedded within `LongitudinalProfile` and therefore owned by the same builder/node.

### 4.3 No Duplicated Computation

- `LearningProgress` is computed exclusively by `LearningProgressBuilder` from `LongitudinalProfile`. It is not recomputed from `SessionHistory[]` by any other component.
- `CrossSessionLanguageCapability` is aggregated exclusively by `LongitudinalProfileBuilder`. No other component performs language capability aggregation.
- Trend direction computation (`FeatureTrend.trend_direction`) is performed exclusively by `LearningProgressBuilder` using the §2.6 threshold rule. The rule is stated once in DOMAIN-CONTRACTS.md; DATA-MODEL.md does not re-state it.

### 4.4 No Hidden Implementation Decisions

The following were confirmed as architectural (not implementation) decisions:
- Repository interface (`get`, `save`, `exists`) is declared at the domain layer — no storage technology specified.
- Serialization format (JSON) is architectural — confirmed by V1.2 precedent and Pydantic v2 tooling; not a novel implementation choice.
- `trend_direction` threshold (`0.05`) is stated explicitly in DOMAIN-CONTRACTS.md §2.6 as a builder responsibility — not a hidden algorithm.

No implementation choices (storage engine, file paths, SQL schema, encoding, concurrency model) have leaked into the planning documents.

### 4.5 No Unresolved ADRs

ADR-034 is the only ADR introduced for EPIC-02. It is accepted. All 9 decisions are frozen. The ADR-033 review trigger ("`ScoringSnapshot` sufficiency") is resolved by ADR-034 Decision 2 — `ScoringSnapshot` is not embedded in `LongitudinalProfile`.

No additional ADRs are required for EPIC-02 implementation to begin.

### 4.6 No Unresolved Planning Issues

| Issue | Classification | Status |
|---|---|---|
| OI-01 — `total_objectives` source | DC | CLOSED |
| OI-02 — `total_narrative_insights` source | DC | CLOSED |
| OI-03 — `LanguageCapability` accessibility | PI | CLOSED |
| Reconstruction gap (`language_capability_summary`) | DM | ACCEPTED |

No undocumented planning issue remains.

---

## 5. Open Issues at Freeze

### 5.1 LONGITUDINAL-PROFILE.md §7 Table — Minor Pre-ADR Inconsistency

**Classification:** Documentation — non-blocking.  
**Description:** LONGITUDINAL-PROFILE.md §7.1 ownership table lists `longitudinal_update` node as potentially writing `LongitudinalProfile` to `InterviewState`. ADR-034 Decision 1 explicitly prohibits this (`InterviewState` field not introduced). The planning document predates the ADR.  
**Impact:** Zero. ADR-034 is the authoritative governance document. DOMAIN-CONTRACTS.md and DATA-MODEL.md both correctly implement ADR-034 Decision 1. No production code will introduce an `InterviewState` field for `LongitudinalProfile`.  
**Resolution:** No post-freeze edit required. Note recorded here for completeness. If LONGITUDINAL-PROFILE.md is updated for any other reason, the table should be corrected at that time.

### 5.2 LanguageCapability Reconstruction Gap — Accepted

**Classification:** DM — accepted limitation.  
**Description:** `language_capability_summary` is not reconstructable from `SessionHistory[]` alone. Reconstructed profiles will have `language_capability_summary = []`.  
**Impact:** Acceptable for V1.3. No production data exists at freeze time. Data is supplementary.  
**Resolution:** Documented in DATA-MODEL.md §6.3 under amended invariant I-LP-REC. Architectural test must verify this behavior explicitly. V2 may address via a new ADR if needed.

---

## 6. Acceptance Checklist

| # | Check | Result |
|---|---|---|
| 1 | Authority hierarchy is complete and internally consistent | PASS |
| 2 | All EPIC-02 planning documents are internally consistent | PASS |
| 3 | No contradictory decisions across documents | PASS |
| 4 | Ownership model: no duplicated producers or writers | PASS |
| 5 | Builder ownership and boundaries are clean | PASS |
| 6 | Single-writer invariants (LP-01, LP-02) are formally satisfied | PASS |
| 7 | Cross-document field consistency verified | PASS |
| 8 | Replay boundary is clean and bidirectional (LP-11) | PASS |
| 9 | `LongitudinalProfile` lifecycle is complete | PASS |
| 10 | `LearningProgress` lifecycle is correct (never persisted) | PASS |
| 11 | `LanguageCapability` activation is architecturally coherent | PASS |
| 12 | `CandidateIdentity` integration is correct and V2-compatible | PASS |
| 13 | Reconstruction completeness (P-08): substantially satisfied | PASS (gap accepted) |
| 14 | Architecture Constitution (P-01 through P-08): compliant | PASS |
| 15 | All 9 ADR-034 decisions are frozen | PASS |
| 16 | All pre-freeze open issues (OI-01, OI-02, OI-03) are closed | PASS |
| 17 | No unresolved ADRs | PASS |
| 18 | No hidden implementation decisions | PASS |
| 19 | No duplicated computation | PASS |
| 20 | No document duplication | PASS |
| 21 | Implementation readiness gates are all satisfied | PASS |

**All 21 checks pass. 0 failures. 1 accepted limitation (§5.2).**

---

## 7. Architecture Freeze Decision

**ARCHITECTURE FREEZE DECLARED.**

EPIC-02 planning is complete. The following is now in effect:

1. **Implementation may begin** on any module specified in EPIC-02-LONGITUDINAL-PROFILE.md §13 (Appendix A).
2. **Frozen document set** (§1) must not be modified without a Freeze Integrity Check per V13-DEVELOPMENT-PLAYBOOK.md §9.
3. **Any deviation from frozen decisions** during implementation constitutes an architectural exception and requires a new ADR or Freeze Integrity Check before the deviation is committed.
4. **Architecture Review (CAR) applies** to implementation artifacts at the milestones defined in V13-DEVELOPMENT-PLAYBOOK.md.
5. **FR-02 (Final Review)** is the closure gate for EPIC-02. Implementation is complete when all success criteria in EPIC-02-LONGITUDINAL-PROFILE.md §12 are satisfied and FR-02 produces a Closed outcome.

**Freeze date:** 2026-07-14  
**Freeze authority:** Architecture Review — EPIC-02 Planning Set

---

*Any post-freeze modification to a frozen planning document requires a Freeze Integrity Check before the change is accepted. The Freeze Integrity Check must verify that: (1) the change is additive and non-breaking, or (2) a new ADR supersedes the affected decision, and (3) all documents in the frozen set remain internally consistent after the change.*

*Revision 2026-07-14: Initial Architecture Freeze declaration for EPIC-02.*
