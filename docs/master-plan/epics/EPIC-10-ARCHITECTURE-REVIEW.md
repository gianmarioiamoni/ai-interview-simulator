# EPIC-10 — Architecture Review

**Status:** COMPLETE  
**Verdict:** APPROVED WITH OBSERVATIONS  
**Date:** 2026-07-21  
**Epic ID:** EPIC-V13-10  
**Playbook Category:** Category B — Major Architectural Epic (**confirmed**)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-10; Product Goal P-10  
**Inputs:** `EPIC-10-ARCHITECTURE-DISCOVERY.md`; `EPIC-10-OVERVIEW.md`; ARC-01; Playbook v1.0; Master Plan  
**Authority:** Decision disposition for Category B cleanup epic. No production code. No proactive ADR. Does not authorize Implementation Plan until Architecture Freeze.

**Disambiguation:** Not PRD EPIC-10 (Progress Tracking).

---

## 1. Scope reviewed

| In scope | Out of scope |
|---|---|
| PAT / OP / P-08 registry model + Master Plan “five new PATs” wording | New product features |
| `InterviewState` ownership strategy + Contracts/Data Model necessity | CandidateProfile semantic redesign / rename campaign |
| Deprecated / dead / migration-scaffold disposition | Performance optimisation (EPIC-09 closed) |
| PAT-06 corollary enforcement strategy | Building SessionHistory durable store |
| Deploy-artifact purity (`TD-EP08-001`) | Horizontal scaling / Redis / CDN |
| Minimum architectural-test set | Expanding non-architectural test coverage |
| Category B confirmation + Freeze path | Implementation mechanisms (→ Implementation Plan) |

---

## 2. Discovery review

Discovery accepted as complete and accurate. Key accepted findings:

- Three parallel vocabularies (PAT-01…06, OP-01…06, P-08) — numeric IDs collide; INDEX lists PATs only.
- Master Plan “five new PATs” maps to OP-01…04 + P-08, not five new Pattern Freeze IDs.
- `InterviewState`: 45 fields; ~10 strong declarations; ~35 ownership gaps; thin arch-test coverage.
- Almost no `@deprecated` markers; dead stubs remain (`gradio_app.py`, `EvaluationBridgeDetector`).
- No confirmed live PAT-06 corollary violation; suspects need classification.
- Deploy: `COPY . .`, no `.dockerignore`; `TD-EP08-001` in scope.

---

## 3. Architectural decisions (AR / ARD disposition)

| ID | Question | Disposition | Binding notes |
|---|---|---|---|
| **AR-01** (ARD-01) | Registry model for “register five new PATs” | **Accepted** | Keep **dual namespace**: PAT-01…06 = Engineering Pattern Registry; OP-01…06 = Official Patterns (ARC-01). **Do not** renumber OPs as PAT-07+. Satisfy Master Plan by amending `INDEX.md` with an **Official Patterns (ARC-01)** section listing OP-01…06, and a Master Plan wording note that “five new PATs” = OP-01…04 + P-08. |
| **AR-02** (ARD-02) | Reconstruction Completeness registry identity | **Accepted** | Remains **ARC-01 P-08** (constitutional principle). **Not** registered as a new PAT. INDEX cross-links P-08 under Official Patterns / principles. Master Plan “PAT” wording treated as historical synonym for P-08. |
| **AR-03** (ARD-03) | InterviewState ownership strategy | **Accepted** | Produce an **authoritative Ownership Matrix** (all 45 fields) as a Domain Contracts section. Strategy: **document authorized writers as they exist**, including explicit **authorized multi-writer sets** where fan-in is intentional (e.g. `results_by_question`). **No redesign** of navigation/UI control-plane ownership in this epic. UI-plane fields may list graph node + named UI handlers as the authorized set. Clear/reset by nav of presentation fields is documented privilege, not a second sole writer of semantic content. |
| **AR-04** (ARD-04) | Dead / deprecated / scaffold disposition | **Accepted** | **Delete in EPIC-10:** `gradio_app.py`; `EvaluationBridgeDetector` module + dedicated tests; InterviewState dead fields proven unused after Contracts verification (`progress`, `dimension_signals`, `current_reasoning_decision` — delete only if Contracts confirms zero production readers/writers beyond orphan writes). **Retire** obsolete MIG/TCP *scaffolding tests* that assert transitional dual-path behaviour no longer present. **Keep** live TCP nullable fields that are production state (`session_history`, `report`, etc.). **Docs:** correct stale Master Plan go-live `InterviewState.report_output` wording. |
| **AR-05** (ARD-05) | PAT-06 corollary classification | **Accepted** | **Not violations:** intra-capability type/area dispatch (`ExecutionEngine`, `AreaQuestionBuilder`); node-invoked single-facade sequencing (`InterviewEvaluationService`, KnowledgePipeline, SessionClosePipeline) that returns results without choosing graph next-step. **Violations:** service-to-service calls that select workflow branch, lifecycle transition, or retry-of-workflow-step. **`RecoveryReplanner`:** allowed if capability-internal and node decides graph continuation; escalate only if it encodes graph routing. **`start.py` bootstrap:** allowed pre-graph session init; must not implement interview workflow routing. Enforcement = arch-test allowlist + forbidden-pattern scan (AR-10). |
| **AR-06** (ARD-06) | Deploy-artifact purity (`TD-EP08-001`) | **Accepted** | **Primary:** delete confirmed dead production stubs from repo (ARC-01 deletion principle). **Defense-in-depth:** add `.dockerignore` excluding non-runtime paths (tests, docs tooling residue, local data) so image cannot ship deleted/non-runtime trees. Close `TD-EP08-001` when both delete set + ignore rules certified. |
| **AR-07** (ARD-07) | Domain Contracts / Data Model necessity | **Accepted** | **Domain Contracts: REQUIRED** — Ownership Matrix + deletion field specs + Traceability for Master Plan P-10 requirements. **Data Model: N/A** unless Contracts finds a deleted/changed field participates in `SessionHistory` / `Report` / `schema_version` durable shape; if so, **stop** and author Data Model before Freeze. Default path: no durable shape change. |
| **AR-08** (ARD-08) | `candidate_profile_v2` / `dimension_scores` | **Accepted (out of redesign)** | **In scope:** declare ownership for `candidate_profile_v2` only. **Out of scope:** rename field; remove `dimension_scores` dual-model; CandidateProfile V1.1 semantic migration. Register residual dual-model as TD if not already closed. |
| **AR-09** (ARD-09) | Projection-as-PAT-04 mislabels | **Accepted** | **Docs/code-comment hygiene only:** replace erroneous `PAT-04` (Projection Artifact) references with **OP-02**. No new ADR. |
| **AR-10** (ARD-10) | Minimum architectural-test set | **Accepted** | Mandatory gates (CAR): (1) Ownership Matrix coverage test — every `InterviewState` field appears with declared authorized writer set; (2) deleted stubs absent (`gradio_app`, EvaluationBridgeDetector); (3) PAT-06 corollary allowlist/scan; (4) registry presence — INDEX lists OP-01…06 + P-08 cross-ref; (5) no Projection-as-PAT-04 in `domain/contracts/report`; (6) existing P-08 reconstruction tests remain green; (7) deploy purity — deleted paths absent + `.dockerignore` present for agreed non-runtime globs. |
| **AR-11** | New formal ADR | **Rejected** | No constitutional exemption. Decisions reuse ARC-01, Pattern Freeze, OP registry. Field deletions + ownership documentation proceed via Domain Contracts + Freeze, not a new ADR. |
| **AR-12** | Multi-writer cluster redesign | **Rejected** | Out of scope; document authorized sets (AR-03). Redesign would be a separate epic/ADR. |
| **AR-13** | Category reclassification to A | **Rejected** | State-contract ownership + possible field deletion keep Category B. |
| **AR-14** | Implementation mechanisms | **Deferred** | Implementation Plan after Freeze. |

---

## 4. ARD-01…10 resolution summary

| ARD | Resolution | Freeze-blocking? |
|---|---|---|
| ARD-01 | Dual PAT/OP namespaces; INDEX Official Patterns section; no PAT renumber | **Yes** — registry doc plan in Freeze |
| ARD-02 | P-08 stays principle; not a PAT | **Yes** |
| ARD-03 | Ownership Matrix documents authorized writers (incl. multi-writer sets); no redesign | **Yes** — Contracts |
| ARD-04 | Delete stubs + proven-dead state fields; retire dead MIG scaffolding; keep live TCP fields | **Yes** — Contracts deletion table |
| ARD-05 | Corollary boundary + allowlist classification | **Yes** — Freeze + arch-test policy |
| ARD-06 | Delete + `.dockerignore` | **Yes** |
| ARD-07 | Contracts REQUIRED; Data Model N/A (default) | **Yes** — workflow path |
| ARD-08 | Ownership only; redesign out | **Yes** (scope freeze) |
| ARD-09 | Comment/doc fix OP-02 | No (non-blocking hygiene; include in Impl Plan) |
| ARD-10 | Seven mandatory arch-test gates | **Yes** |

---

## 5. Approved architecture (binding for Freeze)

1. **Registry:** PAT-01…06 and OP-01…06 remain distinct; INDEX gains Official Patterns + P-08 cross-link; Master Plan “five new PATs” = OP-01…04 + P-08.
2. **Ownership:** Category B Domain Contracts deliver full Ownership Matrix; authorized multi-writer sets allowed when documented; no ownership redesign.
3. **Cleanup:** Delete dead stubs/detectors; delete InterviewState fields only after Contracts proves unused; deploy purity = delete + `.dockerignore`.
4. **PAT-06 corollary:** Capability dispatch ≠ routing; workflow routing stays in LangGraph; enforce via allowlist arch tests.
5. **`candidate_profile_v2`:** Ownership declaration only.
6. **ADR:** None new (AR-11).
7. **Next gates:** Domain Contracts → (Data Model only if durable shape hit) → Architecture Freeze → Implementation Plan.

---

## 6. Assumption dispositions (AA-01…AA-10)

| ID | Status after Review |
|---|---|
| AA-01 | **VERIFIED** — AR-08/AR-12 keep feature redesign out |
| AA-02 | **VERIFIED** — Contracts REQUIRED; Data Model N/A by default (AR-07) |
| AA-03 | **VERIFIED** — AR-01/AR-02 reuse ARC-01 + Pattern Freeze |
| AA-04 | **VERIFIED** — scoring class gone; residue cleanup in AR-04 |
| AA-05 | **VERIFIED** — AR-06 closes `TD-EP08-001` path |
| AA-06 | **VERIFIED** — INDEX/OP registration + ownership still required |
| AA-07 | **VERIFIED** — P-08 remains; prior epic matrices reused (AR-02) |
| AA-08 | **VERIFIED** — AR-01 binding interpretation |
| AA-09 | **VERIFIED** — AR-05 classifications; no confirmed live violation |
| AA-10 | **VERIFIED** — gap closed by AR-03 Contracts Ownership Matrix |

---

## 7. Risk resolution

| ID | Addressed by |
|---|---|
| R-01 | AR-01 dual-namespace + INDEX Official Patterns |
| R-02 | AR-03 document authorized sets; AR-12 rejects silent redesign |
| R-03 | AR-04 Contracts verification before field delete |
| R-04 | AR-05 capability vs routing boundary |
| R-05 | AR-06 delete + `.dockerignore` |
| R-06 | AR-08 out of redesign |
| R-07 | AR-10 mandatory gates |
| R-08 | AR-04 docs correction |

---

## 8. Category decision

**Category B — confirmed.**

| Criterion | Decision |
|---|---|
| State contracts / ownership | **Yes** — Ownership Matrix + possible field deletion |
| Domain Contracts | **REQUIRED** (AR-07) |
| Data Model | **N/A (default)** — escalate only if durable shape affected |
| Formal ADR | **SKIP** (AR-11) |
| Architecture Freeze | **REQUIRED** before Implementation Plan |

**Authorized:** registry docs, ownership matrix, deletions proven unused, `.dockerignore`, PAT-06 corollary arch tests, comment hygiene (OP-02).

**Not authorized without re-Review:** CandidateProfile dual-model redesign; multi-writer cluster redesign; new PAT numbers for OPs; durable `schema_version` changes without Data Model.

---

## 9. ADR assessment

**New ADR required: NO**

| Existing authority | Covers |
|---|---|
| ARC-01 OP-01…06, P-04, P-08, deletion principle | Patterns, orchestrator, reconstruction, delete-not-deprecate |
| `V1.2-PATTERN-FREEZE.md` PAT-01…06 | Engineering Pattern Registry |
| EPIC-08 AR-16 | Deploy dead-code purity → EPIC-10 |
| This Review AR-01…AR-14 | Cleanup-specific dispositions |

If Contracts prove a durable stored-shape impact from field deletion, **stop** and either author Data Model (no new ADR if shape deletion only) or a new ADR if a constitutional boundary is crossed.

---

## 10. Decisions that must be frozen before implementation

| Must be in Architecture Freeze | Source |
|---|---|
| Dual PAT/OP registry + INDEX Official Patterns + P-08 cross-link | AR-01, AR-02 |
| Ownership Matrix complete (45 fields) via Domain Contracts | AR-03, AR-07 |
| Deletion table (stubs + verified dead fields + scaffolding) | AR-04 |
| PAT-06 corollary allowlist / violation classes | AR-05 |
| Deploy purity = delete + `.dockerignore` | AR-06 |
| Data Model N/A statement (or Data Model if escalated) | AR-07 |
| `candidate_profile_v2` ownership-only scope | AR-08 |
| Arch-test gate list AR-10 | AR-10 |
| ADR skipped rationale | AR-11 |

**Not freeze-blocking alone:** AR-09 comment hygiene (must still ship in Impl Plan).

---

## 11. Findings

### Observations (non-blocking)

- O-01: Master Plan / go-live text still says `InterviewState.report_output` — correct in docs pass (AR-04).
- O-02: Exact `.dockerignore` glob list → Implementation Plan / Freeze appendix.
- O-03: Ownership Matrix authorized multi-writer sets must be explicit in Contracts or CAR fails AR-10.1.
- O-04: Residual CandidateProfile `dimension_scores` dual-model → TD register if not already tracked (AR-08).
- O-05: PAT-06 corollary scan false-positive rate → tune allowlist in Impl Plan; do not weaken AR-05 classes.

### Blocking findings

- None for Review close. **Domain Contracts** remains the next hard gate before Freeze.

---

## 12. Review verdict

**APPROVED WITH OBSERVATIONS**

**Next:** Domain Contracts (`EPIC-10-DOMAIN-CONTRACTS.md`) — Ownership Matrix + deletion specs + Traceability → Architecture Freeze (Data Model only if escalated).

**Stop after Architecture Review.**
