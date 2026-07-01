# ADR-016A — CandidateIdentity & Session Ownership

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)  
**Date:** 2026-07-01  
**Owner:** Domain  
**Preconditions:** ADR-016 (Observation Intelligence Architecture), K0/K1/K2 frozen  
**Supersedes:** Nothing  
**Superseded by:** Nothing  
**Related:** ADR-017, ADR-018, ADR-022

---

## Context

ADR-016 established the Observation Intelligence Architecture — the flow from EvidenceSignal to Observation to ProfileFeature. It defined ObservationStore as an independent Aggregate Root and SessionHistory as a write-once persistence aggregate.

Neither ADR-016 nor any prior V1.1 ADR answered a foundational question: **who owns the session?**

V1.1 was a stateless, single-session platform. There was no need for an owner concept — each session was ephemeral. V1.2 introduces durable `SessionHistory`, cross-session `LearningProgress`, and eventually `CandidateProfileSnapshot` comparison. Without a `CandidateIdentity` concept, there is no answer to:

- Which sessions belong together in a progress view?
- Who is the subject of a `CandidateProfileSnapshot`?
- What is the unit of replay access?
- How does V2 authentication map to platform data without a domain redesign?

This ADR introduces `CandidateIdentity` as a first-class domain concept and freezes its responsibilities, aggregate boundaries, and relationships to all downstream aggregates.

---

## Decision

**`CandidateIdentity` is a first-class domain concept representing the owner of all interview knowledge produced by the platform on behalf of one candidate.**

It is:
- An Aggregate Root
- Not an authenticated user
- Not dependent on any authentication system
- The root of the ownership hierarchy for `SessionHistory`, `CandidateProfileSnapshot`, and `LearningProgress`

---

## SECTION A — Purpose & Distinction

### Why V1.2 Requires CandidateIdentity

Three V1.2 features are impossible without a stable ownership anchor:

| Feature | Without CandidateIdentity | With CandidateIdentity |
|---|---|---|
| Session Replay | Sessions are isolated records with no owner | Sessions belong to one identity; replay is identity-scoped |
| Progress Tracking | Cross-session aggregation has no grouping key | Progress is computed for one CandidateIdentity |
| CandidateProfileSnapshot comparison | No way to compare two snapshots for the same candidate | Both snapshots carry the same `candidate_identity_id` |

### Frozen Distinctions

| Concept | Responsibility | Owns? |
|---|---|---|
| `CandidateIdentity` | The domain concept representing the owner of interview knowledge | `SessionHistory[]`, `CandidateProfileSnapshot[]`, `LearningProgress` |
| `User` | An infrastructure/UI concept representing someone interacting with the system | Nothing in the domain model |
| `Authentication` | An infrastructure concern — verifying who is making a request | Nothing in the domain model |
| `Authorization` | An infrastructure concern — what an authenticated user may access | Nothing in the domain model |
| `Recruiter` | A V2 concept — an actor who views aggregate analytics | Nothing in V1.2 domain model |
| `Organization` | A V2 concept — a tenant in a multi-tenant deployment | Nothing in V1.2 domain model |

### Core Principle

> **`CandidateIdentity` represents the owner of interview knowledge. It is not an authenticated user.**

In V1.2 (local deployment, no auth), `CandidateIdentity` is a platform-generated stable identifier. The candidate does not log in. The identity is assigned at first session and persists in local storage. In V2, the same domain concept is linked to an authenticated account without any change to the domain model.

---

## SECTION B — Domain Concept Definition

### Purpose

`CandidateIdentity` is the stable, immutable anchor for all platform knowledge produced on behalf of one candidate. It provides the ownership root for `SessionHistory`, progress data, and profile snapshots. It carries no personally identifiable information — it is an opaque identifier with optional display metadata.

### Ownership

`CandidateIdentity` is an **Aggregate Root**. It does not contain other aggregates; it is referenced by them. `SessionHistory`, `CandidateProfileSnapshot`, and `LearningProgress` each carry a `candidate_identity_id` foreign reference. CandidateIdentity itself owns only its metadata.

### Lifecycle

```
Created:   Once, at first session start (or at first explicit platform registration in V2)
Persisted: Immediately; written to durable storage on creation
Mutated:   Display name only (optional; candidate preference)
Deleted:   Never in V1.2 (deletion is a V2 data-governance concern)
Referenced: By every SessionHistory, CandidateProfileSnapshot, LearningProgress record
```

### Identity Fields (Conceptual)

| Field | Type | Notes |
|---|---|---|
| `candidate_identity_id` | opaque stable ID (uuid4) | Assigned at creation; never regenerated |
| `created_at` | timestamp | Creation time; immutable |
| `schema_version` | string | Forward-compatible versioning |
| `display_name` | string (nullable) | Candidate-supplied optional name; only mutable field |

### Immutability After Creation

All fields except `display_name` are immutable after creation. Rationale:

- `candidate_identity_id` is referenced by every downstream record. Regenerating it would orphan all historical data.
- `created_at` is an audit fact; mutation would destroy the creation timeline.
- `schema_version` evolves only through migration, not field reassignment.

`display_name` is mutable because it is cosmetic and carries no semantic meaning in the domain model. Changing it has no downstream effect on any aggregate.

### Persistence

`CandidateIdentity` is persisted to SQLite alongside `SessionHistory`. It is the only aggregate that is created before a session begins. All other aggregates are created during or after a session.

### Consumers

| Consumer | How it uses CandidateIdentity |
|---|---|
| `SessionHistory` | Carries `candidate_identity_id`; used to retrieve all sessions for a candidate |
| `CandidateProfileSnapshot` | Carries `candidate_identity_id`; enables cross-session profile comparison |
| `LearningProgress` | Queries all `SessionHistory` records for one `candidate_identity_id` |
| `Replay UI` | Presents sessions owned by one `candidate_identity_id` |
| `V2 Auth layer` | Links an authenticated user account to an existing `candidate_identity_id` |

### Producers

`CandidateIdentity` is created by the session initialisation pipeline (before session start). In V2, it may also be created by the registration flow. The **session initialisation pipeline is the sole producer** in V1.2.

---

## SECTION C — Domain Relationships

```
CandidateIdentity  (Aggregate Root — the ownership anchor)
    │
    │  (one-to-many; each session belongs to one CandidateIdentity)
    ▼
SessionHistory[]  (write-once; one per completed session)
    │
    ├── ObservationStore snapshot  (ordered, immutable)
    ├── EvidenceStore snapshot     (ordered, immutable)
    ├── CandidateProfileSnapshot   (point-in-time profile view)
    │       └── ProfileFeatures[]  (derived from ObservationStore at close)
    ├── Narrative                  (NarrativeSections + NarrativeInsights)
    ├── CoachingPlan               (LearningObjectives + CoachingActions)
    ├── EvaluationResults[]        (per-question scores)
    ├── LanguageProfile            (session language configuration)
    └── metadata                   (date, role, seniority, business context, score)

CandidateIdentity
    │
    │  (derived read-only; computed from SessionHistory[])
    ▼
LearningProgress    (cross-session dimensional trend view)
    │
    ▼
Replay UI           (session list + per-session replay; read-only)
```

### Ownership Rules

- `CandidateIdentity` does not contain any other aggregate in memory. It references them by ID.
- `SessionHistory` is the container of all session-level aggregates. It carries `candidate_identity_id`.
- `LearningProgress` is a derived, read-only view. It has no independent persistence.
- No aggregate navigates upward to `CandidateIdentity` at runtime; they carry its ID as a reference only.

---

## SECTION D — Aggregate Boundaries

### CandidateIdentity as Aggregate Root

| Attribute | Value |
|---|---|
| Is Aggregate Root | Yes |
| Owns | Its own metadata fields only |
| References | `SessionHistory[]` by `candidate_identity_id` (not in-memory containment) |
| Allowed mutations | `display_name` only |
| Persistence strategy | SQLite; one row per candidate; created before first session; never deleted in V1.2 |
| Lifetime | Platform lifetime (indefinite in V1.2) |
| Sole writer | Session initialisation pipeline (V1.2); registration flow (V2) |

### Boundary Constraints

- `CandidateIdentity` may not contain a live `CandidateProfile`. The profile is session-scoped. The snapshot is stored in `SessionHistory`.
- `CandidateIdentity` may not contain `LearningProgress`. Progress is derived on demand from `SessionHistory[]`.
- `CandidateIdentity` may not contain `ObservationStore`. Observations are session-scoped; their snapshot lives in `SessionHistory`.

---

## SECTION E — Runtime Ownership

```
Platform setup / first launch
    │
    ▼  [writer: session initialisation pipeline — SOLE PRODUCER in V1.2]
CandidateIdentity  (created once; persisted immediately)
    │
    ▼  [session start: CandidateIdentity.id passed into session config]
Interview Session  (ephemeral runtime state; carries candidate_identity_id)
    │
    ▼  [answer submitted → evaluation → signals → observations → features]
SessionHistory  (written once at session close; carries candidate_identity_id)
    │
    ├─► ObservationStore snapshot  (frozen at close; owned by SessionHistory)
    ├─► CandidateProfileSnapshot   (frozen at close; owned by SessionHistory)
    ├─► Narrative                  (frozen at close; owned by SessionHistory)
    └─► CoachingPlan               (frozen at close; owned by SessionHistory)
    │
    ▼  [on-demand; read-only; groups by candidate_identity_id]
LearningProgress  (derived; not persisted independently)
    │
    ▼  [on-demand; read-only]
Replay UI / Progress UI
```

### Ownership Validation

| Property | Status |
|---|---|
| Single writer for CandidateIdentity | ✓ Session initialisation pipeline only |
| CandidateIdentity created before session | ✓ Always present before session state is initialised |
| SessionHistory carries identity reference | ✓ `candidate_identity_id` is non-nullable in SessionHistory |
| No session runs without a CandidateIdentity | ✓ Session config requires `candidate_identity_id` |
| LearningProgress never mutates SessionHistory | ✓ Derived read-only view |
| CandidateIdentity never modified during session | ✓ Only `display_name` is ever mutable; not touched by session pipeline |

---

## SECTION F — Future Authentication Compatibility

### Invariant

> **CandidateIdentity is the domain concept. Authentication is infrastructure. They are not the same thing.**

### Compatibility Analysis

| Auth System | V2 Integration Pattern | Domain model change? |
|---|---|---|
| Local (V1.2) | CandidateIdentity created at first launch; no login | None |
| GitHub OAuth | OAuth callback creates/links account to existing `candidate_identity_id` | None |
| Google OAuth | Same as GitHub | None |
| JWT | JWT payload carries `candidate_identity_id`; session requests are scoped to it | None |
| Enterprise SSO (SAML/OIDC) | SSO identity maps to `candidate_identity_id` on first login | None |
| Organizations (V2) | `TenantContext` added alongside; `CandidateIdentity` unchanged | TenantContext placeholder only (ADR-029) |
| Teams / Cohorts (V2) | Team membership is a relationship on the auth/org layer; `CandidateIdentity` carries no team reference | None |
| Multi-tenant (V2) | `candidate_identity_id` remains globally unique; `tenant_id` is a separate, nullable field on `SessionHistory` (ADR-029) | None |

### Why None of These Change the Domain Model

`CandidateIdentity` represents knowledge ownership, not authentication identity. The platform can always answer "which sessions belong to this candidate?" using `candidate_identity_id` — regardless of whether that ID was assigned locally, via OAuth, or via SSO. The authentication layer maps external identities to `candidate_identity_id`; the domain model never needs to understand the authentication mechanism.

---

## SECTION G — Persistence Strategy

### Ownership Hierarchy in Storage

```
candidates table
  └── candidate_identity_id (PK)
  └── created_at
  └── display_name (nullable)
  └── schema_version

sessions table
  └── session_id (PK)
  └── candidate_identity_id (FK → candidates)
  └── [full SessionHistory payload]
  └── created_at
  └── schema_version
  └── tenant_id (nullable; ADR-029)

observation_snapshots table (or JSONB column in sessions)
  └── session_id (FK → sessions)
  └── [ordered Observation list with freshness_at_close]

profile_snapshots table (or JSONB column in sessions)
  └── session_id (FK → sessions)
  └── [ProfileFeatures at close time + schema_version]
```

### Replay

Replay reads `SessionHistory` for one `candidate_identity_id` → presents sessions in reverse chronological order → renders full transcript on selection. The `ObservationStore snapshot` and `CandidateProfileSnapshot` inside `SessionHistory` are sufficient for complete replay without any live aggregate access.

### Progress Tracking

`LearningProgress` is computed on demand by querying all `SessionHistory` records for one `candidate_identity_id`, extracting dimensional scores, and computing trend lines. It is never persisted independently. It is always derived fresh from `SessionHistory`.

### Historical Comparison

Two `CandidateProfileSnapshot` objects with the same `candidate_identity_id` can be compared directly. No live profile access required. No LLM calls required. Pure data comparison.

---

## SECTION H — Language Independence

`CandidateIdentity` has zero dependency on any language concept.

| Concept | Dependency on CandidateIdentity? | CandidateIdentity dependency on it? |
|---|---|---|
| `ProgrammingLanguage` | None | None |
| `LanguageExecutor` | None | None |
| `LanguageProfile` | Stored in SessionHistory; not in CandidateIdentity | None |
| Interview type (Written/Coding/SQL) | Stored in SessionHistory metadata; not in CandidateIdentity | None |

`CandidateIdentity` is universal. A candidate who completes Python sessions, JavaScript sessions, SQL sessions, and written sessions is the same `CandidateIdentity`. `LearningProgress` and replay work identically across all session types.

---

## SECTION I — ADR Dependency Graph

```
ADR-033 (EvidenceSignal — V1.1 frozen)
ADR-046 (EvidenceStore — V1.1 frozen)
ADR-055 (Observation reservation — V1.1)
ADR-066 (Behavioral Observation migration — V1.1)
ADR-067 (Coaching pipeline decoupling — V1.1)
    │
    ▼
ADR-016 (Observation Schema & Observation Intelligence Architecture)
  Establishes: three-layer model, ObservationStore as Aggregate Root,
  ObservationExtractor as sole Observation producer,
  FeatureEngine as sole ProfileFeature producer
    │
    ▼
ADR-016A (CandidateIdentity & Session Ownership)
  Establishes: CandidateIdentity as domain Aggregate Root,
  ownership hierarchy for all session-level aggregates,
  auth/org compatibility contract
    │
    ├──────────────────────────────────────────────┐
    ▼                                              ▼
ADR-017                                       ADR-022
(ObservationStore Lifecycle)           (SessionHistory Schema Versioning)
  Depends on: ADR-016                    Depends on: ADR-016A (candidate_identity_id
  Unblocks: ADR-021 (Freshness)          is a required field in SessionHistory schema)
    │
    ▼
ADR-018 (ProfileFeature Schema Freeze)
  Depends on: ADR-016, ADR-016A
  Unblocks: ADR-020 (FeatureEngine), ADR-023 (NarrativeGenerator)
    │
    ▼
ADR-019 (LanguageConfig Design — parallel track, no dependency on ADR-016A)
```

### Why ADR-016A Is Inserted Between ADR-016 and ADR-017/ADR-022

- `ADR-017` (ObservationStore lifecycle) defines the ObservationStore snapshot stored in `SessionHistory`. The snapshot must carry a `candidate_identity_id` reference (or inherit it from `SessionHistory`). This dependency must be explicit before ADR-017 is written.
- `ADR-022` (SessionHistory schema versioning) cannot freeze the SessionHistory schema without knowing that `candidate_identity_id` is a non-nullable required field.
- `ADR-018` (ProfileFeature schema) must freeze the `CandidateProfileSnapshot` schema, which carries `candidate_identity_id`.

---

## Rationale

The absence of a `CandidateIdentity` concept in V1.1 was intentional — the platform was stateless. V1.2's persistence requirements make it impossible to reason about ownership without it. Introducing it now, before any persistence schema is frozen (ADR-022 is still pending), ensures that all downstream schemas are designed correctly from the start.

Defining `CandidateIdentity` as a domain concept (not an auth concept) ensures the domain model remains stable across V1.2 (no auth), V2 OAuth, V2 SSO, and V2 enterprise deployments. The auth layer will always adapt to the domain model — not the other way around.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Use session_id as the grouping key for progress/replay | Sessions belong to a candidate, not the reverse. Using session_id as the root would make progress queries require scanning all sessions with no ownership filter. |
| Introduce auth-linked User as the identity concept | Auth systems change (OAuth → SSO → enterprise). Tying the domain model to auth would require a domain redesign on every auth migration. |
| Defer CandidateIdentity to V2 | ADR-022 (SessionHistory schema) cannot be frozen without a `candidate_identity_id` field. Deferring creates a mandatory breaking schema migration at V2. |
| Make CandidateIdentity mutable | Changing `candidate_identity_id` would orphan all historical session data. Only `display_name` (cosmetic) is mutable. |

## Consequences

### Positive

- All V1.2 persistence schemas (`SessionHistory`, `CandidateProfileSnapshot`) are designed correctly from the start with a stable ownership anchor
- V2 auth integration requires zero domain model changes — only infrastructure mapping
- Progress tracking, replay, and historical comparison follow naturally from the identity hierarchy
- Enterprise multi-tenant extension (V2) requires only a nullable `tenant_id` alongside `candidate_identity_id` (ADR-029)

### Negative / Risks

- V1.2 local deployment must generate and persist a `CandidateIdentity` before the first session, adding a one-time setup step
- Without UI-level identity management (V2), the candidate has no way to recover their `candidate_identity_id` if local storage is lost — session history is unrecoverable (acceptable for V1.2 personal local deployment)

## Implementation Evidence

Architecture only. No production files modified.  
Relevant pending schemas (not yet created):
- `domain/contracts/identity/` — CandidateIdentity concept (V1.2 implementation phase)
- `SessionHistory` schema (ADR-022) — will include `candidate_identity_id` as non-nullable FK

## Review Trigger

- When V2 authentication is introduced (link auth identity to `candidate_identity_id`)
- When multi-tenant organisation accounts require a `tenant_id` alongside identity
- When cross-device or cloud-sync session history requires identity portability
