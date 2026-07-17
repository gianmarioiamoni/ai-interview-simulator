# Database Migration Runbook — SQLite Schema Versioning Policy

**Epic:** EPIC-V13-08 (C15 / P6)  
**Freeze:** AR-14 (accepted); AR-15 (rejected for EPIC-08)  
**Authority extended:** V1.2 SQLite / knowledge persistence versioning (ADR-022 §G–H; related domain `schema_version` policies)  
**Complement:** `docs/ops/DEPLOYMENT-RUNBOOK.md` (C14) — deploy / readiness / SIGTERM only; do not duplicate here

---

## 1. Purpose

Operator and engineering policy for **SQLite schema versioning and migration** under the Hugging Face Spaces operational model.

This document **extends** the V1.2 versioning policy into an executable ops runbook. It does **not**:

- Change on-disk SQLite table shape
- Bump any stored `schema_version`
- Add migration code or runtime migration hooks in EPIC-08
- Alter Domain Contracts, Data Model, `InterviewState`, or LangGraph topology

EPIC-08 Category A boundary (AA-03): policy + documentation only.

---

## 2. Relationship to deployment and readiness (C14)

| Concern | Document |
|---|---|
| Local / staging / production deploy, image, secrets, SIGTERM drain | `DEPLOYMENT-RUNBOOK.md` |
| `GET /health/ready`, CI readiness gate | `DEPLOYMENT-RUNBOOK.md` |
| When / how DB schema may change; migration prerequisites, sequence, validation, rollback | **This document** |

**Ordering rule:** Deploy and confirm readiness **before** any authorized migration window. After migration (when one is authorized outside EPIC-08 scope), re-run readiness so the DB probe still reports success.

Readiness DB probe (side-effect-free): opens `Settings.sqlite_db_path` read-only and confirms the file is readable. It does **not** migrate, write, or rewrite schema.

---

## 3. Persistence surfaces in scope

| Surface | Path / access | Notes |
|---|---|---|
| Question bank SQLite | `Settings.sqlite_db_path` (default `data/questions.db`) | Infrastructure repository; readiness DB probe target |
| Domain artifact versions | Embedded `schema_version` (and related policy versions) on persisted knowledge artifacts | Governed by ADR-022 / domain ADRs — not rewritten by EPIC-08 |

SQL evaluation sandboxes use ephemeral in-memory SQLite and are **out of scope** for durable migration.

---

## 4. Extended versioning policy (V1.2 → ops)

### 4.1 Principles (inherited and binding)

| ID | Rule |
|---|---|
| VP-01 | Every persisted knowledge / history artifact carries its `schema_version` (and related policy versions) at write time |
| VP-02 | Readers adapt via version-branching; they do **not** silently rewrite stored rows |
| VP-03 | **Minor** (additive optional fields): existing records remain valid; absent fields → `None`; no migration required |
| VP-04 | **Major** (breaking): existing records remain readable under their stored version; upgrades produce **new** records alongside originals |
| VP-05 | **No silent migrations** — every mutation of stored knowledge is explicit, logged, auditable, operator-approved (ADR-022 MS-03) |
| VP-06 | Originals are never deleted by migration; retention is a separate policy decision (MS-05) |
| VP-07 | Replay prefers stored snapshots; recomputation is reserved for migration / recovery / explicit request (MS-01, MS-02) |

### 4.2 EPIC-08 freeze extension

| ID | Rule |
|---|---|
| VP-08 | EPIC-08 **does not** authorize on-disk schema changes or `schema_version` bumps (AR-14; rejects AR-15) |
| VP-09 | A future schema / stored-shape change requires Category B reclassification (or equivalent ADR / Data Model path) **before** implementation |
| VP-10 | Until a migration is authorized, the operator runbook “execution sequence” is a **no-op verify** path (§6.1) |

### 4.3 Triggering a version increment (future, post-authorization)

A stored-shape or major `schema_version` increment is triggered only when an accepted ADR / Data Model declares backward-incompatible persistence change. Additive optional fields with safe defaults do **not** require a version bump (aligned with ADR-034 / ADR-022 minor rules).

---

## 5. Migration prerequisites (when a migration is authorized)

Do **not** run §6.2 unless all of the following hold:

1. **Authority:** Accepted ADR (or Category B Data Model) describing the schema delta, version numbers, and migration path  
2. **Artifact:** Versioned migration script / tool checked into the repo for that change (none shipped in EPIC-08)  
3. **Backup:** Copy of the SQLite file(s) under `Settings.sqlite_db_path` (and any other durable stores named by the authorizing ADR)  
4. **Environment:** Target environment identified (local / staging / production Space volume or bind mount)  
5. **Deploy baseline:** Target revision deployed per `DEPLOYMENT-RUNBOOK.md`; process idle or in maintenance window (drain complete if restarting)  
6. **Readiness pre-check:** `GET /health/ready` → HTTP 200, `"ready": true` (or documented intentional probe disables for the window)

---

## 6. Execution sequence

### 6.1 EPIC-08 current state (policy-only — default path)

No schema migration is authorized. Operator verification:

1. Confirm deploy revision and Settings (`SQLITE_DB_PATH` / secrets) per C14  
2. Confirm DB file exists at the configured path (or accept first-boot create behaviour of the app)  
3. `GET /health/ready` — DB probe `status` is `success` or intentionally `skipped`  
4. Record verification in the change log / Space release notes  
5. **Stop** — do not alter tables, `schema_version` values, or replace DB files except for restore from known-good backup

### 6.2 Future authorized migration (template — not executed in EPIC-08)

Only after §5 prerequisites:

1. **Quiesce** — SIGTERM drain / stop admit (process edge; see C14); no in-flight writers  
2. **Backup** — copy SQLite file(s) to a dated backup location outside the live path  
3. **Record** — note pre-migration image digest, git revision, Settings relevant to paths, and authorizing ADR id  
4. **Execute** — run the ADR-specified migration tool against a **copy** first (staging), then production  
5. **Validate** — §7  
6. **Resume** — restart / admit traffic per C14; confirm readiness  
7. **Retain** — keep originals and backups; do not delete pre-migration files as part of the migration itself

---

## 7. Validation

| Check | Pass criteria |
|---|---|
| File integrity | SQLite file opens; optional `PRAGMA integrity_check` → `ok` |
| Readiness | `GET /health/ready` → HTTP 200, `"ready": true` (DB probe success) |
| Version expectation | Stored `schema_version` values match the authorizing ADR (N/A under EPIC-08 no-op path) |
| Application smoke | Short UI / session smoke on staging before production |
| Audit | Migration log lists operator, reason, ADR id, before/after versions (N/A under no-op path) |

Under EPIC-08, “tested” means: doc review checklist (§9) + full regression green with **unchanged** on-disk shape tests.

---

## 8. Rollback guidance

| Scenario | Action |
|---|---|
| EPIC-08 / no migration applied | No DB rollback; redeploy prior app revision per C14 if app regression |
| Authorized migration fails validation | Stop admit; restore SQLite file(s) from §6.2 backup; redeploy prior image if required; re-check readiness |
| Partial dual-write (new alongside old) | Prefer serving pre-migration originals; quarantine upgraded copies; follow authorizing ADR |

Rollback restores **data files + image/Settings** as needed. Do not “reverse-migrate” in place unless the authorizing ADR defines an explicit reverse tool.

---

## 9. Doc review checklist (C15 acceptance)

- [x] V1.2 versioning policy extended (VP-01–VP-07) and EPIC-08 freeze rules (VP-08–VP-10) present  
- [x] Prerequisites, execution sequence, validation, rollback documented  
- [x] Relationship to C14 deploy/readiness stated; deploy steps not duplicated  
- [x] Explicit: no on-disk shape / `schema_version` code change in EPIC-08 (AR-14; rejects AR-15)  
- [x] No Domain Contracts / Data Model / `InterviewState` / LangGraph guidance that implies runtime schema rewrite  
- [x] Category A preserved  

**Review result:** PASS  **Date:** 2026-07-18  **Reviewer:** Architecture Checkpoint C

---

*End of DB Migration Runbook (EPIC-08 C15).*
