# ADR-030 — Study Recommendation Resource Library & Learning Resource Governance

**Status:** Accepted  
**Milestone:** V1.2 — Final Architecture Milestone  
**Date:** 2026-07-01  
**Deciders:** Architecture Board  
**Supersedes:** none  
**Unblocks:** CoachingEngine implementation (EPIC-04)

---

## Context

ADR-025 defines `CoachingPlan` and establishes `StudyRecommendation` as an optional child of `CoachingAction`. It delegates the governance of those recommendations to a dedicated ADR.

The risk without governance: `StudyRecommendation` becomes a hardcoded string. If resources are embedded directly in prompts or CoachingEngine logic, the system degrades into an opinionated suggestion engine with no auditability, no lifecycle, no staleness policy, and no testability.

This ADR freezes the conceptual architecture for the Resource Library, the governance contract every resource must satisfy, the recommendation strategy principles, and the runtime ownership model.

---

## Section A — Why StudyRecommendation Is Not a Hardcoded Suggestion

### A.1 Definition

A `StudyRecommendation` is a **governed reference** — a pointer from a `CoachingAction` to a `LearningResource` — mediated by a recommendation strategy. It is never a literal string embedded in code or an LLM prompt.

### A.2 The problem with hardcoded suggestions

| Hardcoded approach | Consequence |
|---|---|
| String in LLM prompt | Non-deterministic, untraceable, cannot be audited |
| Literal URL in CoachingEngine | Stale on resource update, no version control |
| LLM chooses resource at runtime | No quality gate, no ownership, no freshness signal |
| No resource model | Duplicate recommendations, no deduplication, no ranking |

### A.3 The governed resource model

A `StudyRecommendation` is valid only if:
- It references a `LearningResource` with status `Approved`
- The resource covers the technology/topic identified in the `KnowledgeGap`
- The resource difficulty is compatible with the candidate's current `ProfileFeature` level
- The resource language availability matches the session `LanguageProfile`
- The recommendation carries a traceable rationale linking it to `KnowledgeGap` + `LearningObjective`

### A.4 Relationship with upstream domain entities

```
KnowledgeGap
  ↓ (identifies what the candidate does not know)
LearningObjective
  ↓ (defines what the candidate should be able to do)
StudyRecommendation
  ↓ (points to a governed resource that closes the gap)
LearningResource
  ↓ (the actual governed artefact in the Resource Library)
CoachingPlan
  ↓ (contains the ranked, traceable set of recommendations)
```

**KnowledgeGap** — The evidence-driven deficiency extracted from `CandidateProfile` and evaluation results. It is the trigger. CoachingEngine consumes it.

**LearningObjective** — The strategic outcome the candidate should achieve. Defined in `CoachingPlan` by CoachingEngine; references one or more `CoachingAction[]`.

**StudyRecommendation** — A concrete resource pointer with ranked relevance, difficulty match, and gap traceability. It is never free-form text.

**CandidateProfile** — Provides the current knowledge baseline (via `ProfileFeature`) so that difficulty and prerequisite matching is accurate. CoachingEngine reads it read-only.

### A.5 Frozen responsibilities

| Entity | Sole writer | Readers |
|---|---|---|
| `LearningResource` | Resource Library Governance (human/operator curation) | CoachingEngine (query-only) |
| `StudyRecommendation` | CoachingEngine | ReportBuilder, Narrative (reference only), Replay |
| `ResourceCollection` | Resource Library Governance | CoachingEngine |
| `ResourceTag` | Resource Library Governance | CoachingEngine, ResourceSelector |
| `ResourceVersion` | Resource Library Governance | CoachingEngine (version-locked at recommendation time) |

CoachingEngine is **consumer only** with respect to the Resource Library. It never creates or mutates resources.

---

## Section B — Resource Library Architecture (Conceptual)

### B.1 LearningResource

The atomic governed unit of the Resource Library.

A `LearningResource` represents a single addressable educational artefact: a book chapter, a tutorial, a documentation page, a course module, an exercise set. It is technology-specific but language-independent at the knowledge level.

Conceptual attributes:
- `resource_id` — stable opaque identifier (UUID)
- `resource_version` — semantic version string (see Section B.9)
- `title` — human-readable name
- `description` — short purpose summary (non-empty, non-generated)
- `url` — canonical location (may be versioned URL)
- `resource_type` — `ARTICLE | DOCUMENTATION | COURSE | EXERCISE | BOOK | VIDEO | INTERACTIVE`
- `difficulty` — (see Section B.7)
- `estimated_duration` — (see Section B.8)
- `prerequisites` — (see Section B.9)
- `learning_outcomes` — (see Section B.10)
- `technology_coverage` — list of technology identifiers (e.g. `python`, `react`, `docker`)
- `topic_tags` — list of `ResourceTag` references (e.g. `closures`, `async/await`, `sql-joins`)
- `language_availability` — list of `ProgrammingLanguage` identifiers if execution is required; empty if language-agnostic
- `quality_status` — governance lifecycle status (see Section G)
- `owner` — governance owner identifier (human or team)
- `last_review_date` — ISO date of last quality review
- `metadata` — `ResourceMetadata` (see Section B.6)

### B.2 StudyRecommendation

A `StudyRecommendation` is a **recommendation record**, not a raw resource. It is the link between a `CoachingAction` and a `LearningResource`, carrying the rationale and context.

Conceptual attributes:
- `recommendation_id` — opaque identifier
- `resource_id` — reference to `LearningResource.resource_id`
- `resource_version_at_recommendation` — snapshot of `resource_version` at CoachingPlan creation (immutable)
- `knowledge_gap_id` — reference to the `KnowledgeGap` that triggered this recommendation
- `learning_objective_id` — reference to the `LearningObjective` this recommendation serves
- `rank` — integer position within the recommendation set for this objective
- `relevance_score` — computed float [0–1] expressing gap-to-resource coverage alignment
- `difficulty_match` — `BELOW | MATCHED | ABOVE` relative to candidate's current level
- `rationale` — structured explanation (not prose): gap label + objective label + resource coverage overlap
- `is_mandatory` — boolean; primary resource vs supplementary
- `session_language_profile_id` — language context at recommendation time

`StudyRecommendation` is immutable after `CoachingPlan` is sealed.

### B.3 LearningPath

A `LearningPath` is an **ordered sequence of `LearningResource[]`** representing a structured curriculum for a specific topic or skill area.

Conceptual attributes:
- `path_id` — stable opaque identifier
- `path_version`
- `title`
- `description`
- `milestones` — `LearningMilestone[]` (checkpoint definitions)
- `completion_criteria` — conditions for path completion
- `estimated_total_duration` — sum of constituent resources
- `prerequisites` — skills or resources required before starting
- `dependency_graph` — directed acyclic graph of resource ordering constraints
- `resource_ids` — ordered list of `LearningResource.resource_id`

`LearningPath` is a **V1.3 concept**. It is introduced here to establish the conceptual boundary. No implementation in V1.2.

### B.4 ResourceCollection

A named grouping of `LearningResource[]` for a thematic or technological cluster.

Examples: `"Python Fundamentals"`, `"SQL Mastery"`, `"React Hooks"`, `"System Design Basics"`.

A `ResourceCollection` is not ordered (unlike `LearningPath`). It exists to enable efficient querying by topic without requiring individual tag traversal.

Conceptual attributes:
- `collection_id`
- `collection_version`
- `title`
- `technology_coverage`
- `topic_tags`
- `resource_ids`
- `quality_status`
- `owner`
- `last_review_date`

### B.5 ResourceTag

A controlled vocabulary term. Tags must be declared in the Tag Registry before assignment.

Conceptual attributes:
- `tag_id` — stable slug (e.g. `python.closures`, `sql.window-functions`, `react.hooks.useEffect`)
- `tag_label` — human-readable
- `tag_category` — `CONCEPT | PATTERN | TECHNOLOGY | LEVEL | DOMAIN`
- `parent_tag_id` — optional hierarchical parent (enables topic tree traversal)
- `status` — `ACTIVE | DEPRECATED`

Tags are language-agnostic at the category level. `python.closures` and `javascript.closures` are separate tags with a common parent `closures`.

### B.6 ResourceMetadata

Governance and provenance record attached to every `LearningResource`.

Conceptual attributes:
- `source_provider` — `"official-docs"`, `"third-party"`, `"internal"`, etc.
- `content_hash` — optional fingerprint for change detection
- `created_at`
- `updated_at`
- `review_history` — ordered list of `ResourceReviewEvent` (date, reviewer, outcome)
- `deprecation_reason` — populated when status = `DEPRECATED`
- `replacement_resource_id` — optional; populated on deprecation if a successor exists
- `accessibility_notes` — free text; e.g. paywall, login required

### B.7 Difficulty

Conceptual enum: `BEGINNER | INTERMEDIATE | ADVANCED | EXPERT`

Rules:
- Assigned by governance, not inferred by LLM
- Matched against `ProfileFeature.maturity` to determine `difficulty_match` in `StudyRecommendation`
- A single `LearningResource` has exactly one `Difficulty` value
- Difficulty is technology-relative (an `ADVANCED` Python resource is not necessarily `ADVANCED` for TypeScript)

### B.8 EstimatedDuration

Conceptual: a structured time estimate, not a freeform string.

Fields: `minutes_min`, `minutes_max`, `pace` (`FOCUSED | CASUAL`).

Governance rule: duration estimates must be based on measured completion time, not publisher claims. Updated at each review cycle.

### B.9 Prerequisites

Conceptual: a list of prerequisite conditions a candidate must satisfy before the resource is useful.

Two types:
- `ResourcePrerequisite` — requires completion of another `LearningResource.resource_id`
- `KnowledgePrerequisite` — requires a `ProfileFeature` of at least a given level (e.g. `TechnicalSkill[python.functions] >= INTERMEDIATE`)

CoachingEngine uses prerequisites to filter recommendations: a resource whose prerequisites are unmet by the current `CandidateProfile` is assigned `difficulty_match = ABOVE`.

### B.9 (continued) ResourceVersion

Semantic versioning for `LearningResource`. Format: `MAJOR.MINOR.PATCH`.

- `MAJOR` bump: content substantially changed or replaced
- `MINOR` bump: new sections, updated examples
- `PATCH` bump: typos, broken links, metadata corrections

`StudyRecommendation.resource_version_at_recommendation` is frozen at CoachingPlan sealing time. Subsequent resource updates do not retroactively affect historical recommendations.

### B.10 LearningOutcome

What the candidate should be able to demonstrate after completing the resource.

Conceptual attributes:
- `outcome_id`
- `description` — verb-first statement (e.g. "Implement recursive data structures in Python")
- `maps_to_knowledge_topic` — reference to a topic in the Knowledge Taxonomy (V1.3 concept)
- `maps_to_profilefeature_type` — reference to a `ProfileFeatureType` (ADR-018)

LearningOutcome is the bridge between resource content and the domain knowledge model. It enables CoachingEngine to verify that a recommendation actually closes a specific `KnowledgeGap`.

---

## Section C — Governance

Every `LearningResource` in the library must satisfy the following governance contract at all times.

### C.1 Identifier

`resource_id` is a stable UUID assigned at resource creation. It never changes. URLs change; titles change; the identifier does not.

### C.2 Version

`resource_version` follows semantic versioning (Section B.9). A resource without a version is invalid. Every change to content, difficulty, or duration requires a version increment.

### C.3 Owner

Every resource has exactly one designated owner — a human or team responsible for maintenance and review scheduling. Ownerless resources must be flagged for review within one governance cycle.

### C.4 Tags

Every resource must have at least one `ResourceTag`. Untagged resources are invisible to the recommendation strategy and must be quarantined as `DRAFT` until tagged.

### C.5 Difficulty

Mandatory. Assigned by governance, not inferred. Resources submitted without difficulty are held in `DRAFT` status.

### C.6 Estimated Duration

Mandatory. Must be based on measured or validated completion time. Resources with no duration estimate are held in `DRAFT` status.

### C.7 Language Availability

For resources involving code execution: a list of supported `ProgrammingLanguage` identifiers. For conceptual/theoretical resources: empty list (language-agnostic). Missing this field blocks recommendation for language-specific `KnowledgeGap` types.

### C.8 Technology Coverage

A list of technologies the resource addresses. Required for routing by `KnowledgeGap.technology_context`. A resource covering Python closures must declare `technology_coverage = ["python"]`.

### C.9 Quality Status

Lifecycle state (see Section G). Resources in `DRAFT` or `ARCHIVED` are excluded from all recommendations.

### C.10 Last Review Date

ISO date of most recent governance review. Resources not reviewed within the defined review period (policy: 90 days for `Approved` resources) are automatically demoted to `REVIEWED` pending re-approval. Stale resources are flagged to the owner.

---

## Section D — Recommendation Strategy

### D.1 Principles

**Evidence-driven.** Every recommendation traces to a `KnowledgeGap` supported by `Observation[]` and expressed in `ProfileFeature` confidence/coverage values. No recommendation is generated without gap evidence.

**KnowledgeGap-driven.** The primary routing signal is the `KnowledgeGap.topic` and `KnowledgeGap.severity`. Resources are matched against gap coverage, not general topic interest.

**LearningObjective-driven.** Recommendations are scoped to the `LearningObjective` they serve. A resource recommended for "improve Python recursion" is not duplicated under "improve problem decomposition" even if it appears relevant.

**Language-independent.** The recommendation strategy operates on knowledge topics. If a gap is in `recursion`, the strategy can recommend resources regardless of language, then filter by `LanguageProfile` as a post-filter. The core ranking logic never branches on language.

**Technology-independent.** The ranking algorithm is identical whether the session involved Python, JavaScript, SQL, or TypeScript. Technology filtering is applied via `resource.technology_coverage` intersection, never by hardcoded conditionals.

**Personalized.** Difficulty matching is computed against the candidate's current `ProfileFeature` levels. Two candidates with the same `KnowledgeGap` may receive different resources if their baseline proficiency differs.

**Ranked.** `StudyRecommendation.rank` is deterministic and justified: primary resource (rank 1) has the highest `relevance_score` and `MATCHED` difficulty. Supplementary resources are ranked by relevance then difficulty match.

**Explainable.** `StudyRecommendation.rationale` is always populated with a structured explanation. The candidate (and any audit) can see exactly why each resource was recommended.

**Never random.** Under identical inputs (`KnowledgeGap`, `CandidateProfile`, `LanguageProfile`, `ResourceLibrary` state), the recommendation output is deterministic. No sampling, no stochastic selection, no LLM-chosen resources.

### D.2 Ranking algorithm (conceptual)

Input: `KnowledgeGap[]`, `CandidateProfile`, `LanguageProfile`, `ResourceLibrary`

Steps:
1. For each `KnowledgeGap`, query `ResourceLibrary` for resources with overlapping `topic_tags`
2. Filter by `quality_status = APPROVED`
3. Filter by `language_availability` (if gap is language-specific)
4. Compute `relevance_score` = tag overlap ratio
5. Compute `difficulty_match` against `ProfileFeature.maturity` for the gap topic
6. Filter out resources where prerequisites are unmet
7. Rank: primary = highest `relevance_score` + `MATCHED` difficulty; supplementary = remaining by score
8. Attach `rationale` (gap label + objective + coverage overlap)
9. Freeze as `StudyRecommendation[]` in `CoachingPlan`

No LLM is invoked in steps 1–9.

---

## Section E — Learning Paths

### E.1 Concept

A `LearningPath` is a structured, ordered curriculum for a skill domain. Where a `ResourceCollection` is a flat grouping, a `LearningPath` encodes:
- Sequencing (resource A before resource B)
- Milestones (checkpoints with completion criteria)
- Prerequisite dependencies (resource B requires resource A AND a ProfileFeature condition)
- Estimated total duration
- A directed acyclic graph of resource ordering

### E.2 Relationship to StudyRecommendation

In V1.2, `StudyRecommendation` references individual `LearningResource[]`. In V1.3, CoachingEngine will optionally reference a `LearningPath` as the recommendation unit for candidates with multiple related gaps in the same domain.

### E.3 V1.3 reservation

`LearningPath` is architecturally introduced here to reserve its place in the domain model and prevent conflicting conventions. No V1.2 code, contract, or schema implements `LearningPath`. The DAG topology, milestone events, and path completion tracking are V1.3 concerns.

---

## Section F — Technology Independence

### F.1 Separation invariant

```
KnowledgeGap            ← technology context: optional annotation only
     ↓
StudyRecommendation     ← technology context: filter input only
     ↓
LearningResource        ← technology context: content attribute only
```

The knowledge model (KnowledgeGap, LearningObjective, ProfileFeature, CoachingPlan) never encodes technology conditionals. Technology is a **routing attribute**, not a structural dimension.

### F.2 Technology coverage

Resources may reference any technology: Python, JavaScript, TypeScript, React, Node.js, Docker, AWS, LangChain, SQL, Bash, and any future technology. The resource library grows without changes to the domain model.

### F.3 Domain model independence

Adding Go, Java, Rust, or any new language requires:
- New `LanguageExecutor` (ADR-027)
- New `LanguagePolicy` (ADR-031)
- New question corpus entries
- New `LearningResource[]` with appropriate `technology_coverage`

It does **not** require:
- Changes to `KnowledgeGap` schema
- Changes to `ProfileFeature` types
- Changes to `CoachingEngine` logic
- Changes to recommendation ranking algorithm
- Changes to `StudyRecommendation` structure

### F.4 Language availability vs technology coverage

`language_availability`: which `ProgrammingLanguage` identifiers are required to execute or understand the resource's code examples. Empty = language-agnostic.

`technology_coverage`: which named technologies the resource teaches. Always populated.

These are independent attributes. A resource on SQL joins has `technology_coverage = ["sql"]` and `language_availability = []`.

---

## Section G — Quality Governance

### G.1 Resource lifecycle

```
DRAFT
  ↓  (review completed, quality criteria met)
REVIEWED
  ↓  (governance approval by owner + quality gate)
APPROVED
  ↓  (resource superseded, outdated, or policy change)
DEPRECATED
  ↓  (removed from active library; retained for historical reference)
ARCHIVED
```

### G.2 Lifecycle rules

**DRAFT:** Created by contributor. Not visible to CoachingEngine. All required governance fields must be populated before promotion.

**REVIEWED:** All fields populated; content verified accurate. Eligible for approval. Visible to governance team only.

**APPROVED:** Cleared for use in `StudyRecommendation`. Duration, difficulty, tags, and outcomes validated. Owner confirmed active. Review date set.

**DEPRECATED:** Resource is no longer recommended for new `CoachingPlan`. Existing `StudyRecommendation[]` that reference this version remain valid (version-locked). `replacement_resource_id` should be populated.

**ARCHIVED:** Removed from all query paths. Retained for replay immutability (historical `StudyRecommendation` remain resolvable via version-locked reference). Not returned by any CoachingEngine query.

### G.3 Approval policy

Every `StudyRecommendation` generated by CoachingEngine must reference a resource with `quality_status = APPROVED`. This is a hard invariant. CoachingEngine must verify this at recommendation generation time.

### G.4 Review cadence

`APPROVED` resources: reviewed every 90 days.

Resources overdue for review: automatically flagged to owner; status demoted to `REVIEWED` pending re-approval.

Resources without an owner for more than one governance cycle: quarantined as `DRAFT`.

### G.5 Deprecation protocol

1. Owner marks resource `DEPRECATED` with `deprecation_reason`
2. If a replacement exists: `replacement_resource_id` populated
3. Existing `StudyRecommendation[]` not retroactively changed (version-locked)
4. Resource excluded from all new recommendations immediately upon deprecation
5. After 2 governance cycles (180 days): eligible for `ARCHIVED`

---

## Section H — Future Concepts

These concepts are introduced to establish naming conventions and prevent collision in V1.3+ design. None are implemented in V1.2.

**Learning Catalog** — A structured, browsable catalog of `LearningResource[]` and `ResourceCollection[]`. Interface for governance tooling and operator management. V1.3.

**Technology Catalog** — Canonical registry of all supported technologies, their identifiers, aliases, and version history. Prevents `technology_coverage` fragmentation across resources. V1.3.

**Skill Catalog** — Maps topic tags and knowledge concepts to formal skill definitions (e.g. aligned to SFIA or custom taxonomy). Enables cross-session skill tracking. V1.3.

**Certification Catalog** — Registry of industry certifications (AWS, GCP, CKA, etc.) with mapped skill prerequisites. Enables CoachingEngine to recommend certification paths. V1.3.

**Provider Catalog** — Registry of resource providers: official documentation sites, platforms (Coursera, Pluralsight, etc.), open-source references. Used in `ResourceMetadata.source_provider`. V1.3.

**Resource Provider** — An entity that publishes or maintains `LearningResource[]`. Provider-level quality policies supplement per-resource governance. V1.3.

**Learning Analytics** — Aggregated signals on resource effectiveness across candidate populations. Used to calibrate `relevance_score` weights. V1.3.

**Recommendation Feedback** — Candidate-reported feedback on received recommendations (useful/not useful, completed/abandoned). Feeds `Learning Analytics`. V1.3.

**Resource Effectiveness** — A computed quality signal derived from `Recommendation Feedback` + `Learning Analytics`. Supplements governance approval with empirical effectiveness data. V1.3.

---

## Section I — Runtime

### I.1 Runtime DAG

```
KnowledgeGap
     ↓
LearningObjective
     ↓
StudyRecommendation  ←──── ResourceLibrary (APPROVED resources, read-only)
     ↓
LearningResource (version-locked reference)
     ↓
CoachingPlan (sealed, immutable)
     ↓
Narrative (references CoachingPlan for coherence; does not modify it)
     ↓
KnowledgeSnapshot (contains sealed CoachingPlan)
     ↓
SessionHistory (persisted write-once)
```

### I.2 Ownership and writer rules

| Rule | Statement |
|---|---|
| Single writer for StudyRecommendation | CoachingEngine only |
| Single writer for LearningResource | Resource Library Governance only |
| Single ownership of CoachingPlan | CoachingEngine; sealed at session close |
| Immutability | CoachingPlan immutable after sealing; StudyRecommendation version-locked |
| Knowledge preservation | LearningResource referenced by historical recommendations never deleted; archived with stable `resource_id` |
| Language independence | Recommendation ranking algorithm is language-neutral; language filtering is post-processing only |
| Technology independence | No technology conditionals in CoachingEngine core logic; technology is a routing attribute only |

### I.3 Validation of DAG integrity

**Single writer:** CoachingEngine is the only producer of `StudyRecommendation`. Resource Library Governance is the only producer of `LearningResource`.

**Single ownership:** `CoachingPlan.study_recommendations` is owned exclusively by CoachingEngine from creation through KnowledgeSnapshot sealing. No other component writes to it.

**Immutability:** `StudyRecommendation.resource_version_at_recommendation` is frozen at CoachingPlan creation. Subsequent resource library updates do not alter sealed plans.

**Knowledge preservation:** `ARCHIVED` resources remain resolvable by `resource_id` + `resource_version` for replay and historical audit. No hard-delete policy.

**Language independence:** Verified in Section F. The ranking algorithm (Section D.2) contains zero language conditionals. Language filtering is applied in step 3 as an attribute filter, not as a branching logic change.

**Technology independence:** Verified in Section F.3. Adding new technologies touches only the resource library content, not the recommendation engine or domain model.

---

## Section J — Architecture Closure Audit

### J.1 All ADRs reviewed

| ADR | Decision Summary | Responsibilities Frozen | Ownership Unambiguous | No Circular Deps |
|---|---|---|---|---|
| ADR-016 | ObservationStore, ObservationExtractor, FeatureEngine | ✓ | ✓ | ✓ |
| ADR-016A | CandidateIdentity as aggregate root | ✓ | ✓ | ✓ |
| ADR-017 | ObservationStore lifecycle and temporal semantics | ✓ | ✓ | ✓ |
| ADR-018 | ProfileFeature knowledge model and versioning | ✓ | ✓ | ✓ |
| ADR-019 | Language independence layer, LanguageConfig | ✓ | ✓ | ✓ |
| ADR-020 | FeatureEngine architecture, three platform engines | ✓ | ✓ | ✓ |
| ADR-021 | Freshness decay, replay principles | ✓ | ✓ | ✓ |
| ADR-022 | Knowledge persistence, SessionHistory | ✓ | ✓ | ✓ |
| ADR-023 | NarrativeGenerator architecture | ✓ | ✓ | ✓ |
| ADR-025 | CoachingEngine architecture, CoachingPlan taxonomy | ✓ | ✓ | ✓ |
| ADR-026 | Replay snapshot model | ✓ | ✓ | ✓ |
| ADR-027 | LanguageExecutor abstraction | ✓ | ✓ | ✓ |
| ADR-028 | Language selection policy | ✓ | ✓ | ✓ |
| ADR-030 | Resource Library governance (this ADR) | ✓ | ✓ | ✓ |
| ADR-031 | LanguagePolicy governance | ✓ | ✓ | ✓ |
| ADR-032 | CandidateProfileSnapshot strategy | ✓ | ✓ | ✓ |

### J.2 No duplicated responsibilities

| Concern | Sole owner |
|---|---|
| Raw evidence production | EvidenceSignal (V1.1 detectors) |
| Observation creation | ObservationExtractor (ADR-016) |
| ProfileFeature creation | FeatureEngine (ADR-018/020) |
| Knowledge gap identification | KnowledgeGapEngine (architecture target) |
| Recommendation creation | CoachingEngine (ADR-025) |
| Resource governance | Resource Library Governance (ADR-030) |
| Narrative prose | NarrativeGenerator (ADR-023) |
| Replay | ReplayEngine consuming KnowledgeSnapshot (ADR-026) |
| Language execution | LanguageExecutor (ADR-027) |
| Language interpretation policy | LanguagePolicy (ADR-031) |
| Candidate identity | CandidateIdentity aggregate (ADR-016A) |
| Profile snapshot | FeatureEngine → KnowledgeSnapshot pipeline (ADR-032) |

No overlaps detected.

### J.3 No ownership ambiguity

All write paths have a single declared owner. Read paths are explicitly listed in each ADR. No entity has two declared sole writers.

### J.4 No circular dependencies

Runtime DAG (verified):
```
EvidenceSignal
  → Observation (ObservationExtractor)
    → ProfileFeature (FeatureEngine)
      → CandidateProfile
        → KnowledgeGap (KnowledgeGapEngine)
          → LearningObjective
            → CoachingPlan + StudyRecommendation (CoachingEngine)
              → KnowledgeSnapshot (sealed)
                → SessionHistory (persisted)
```

Narrative and Report consume `CandidateProfile` + `CoachingPlan` read-only. They are leaves in the DAG (no outputs feed back to producers).

LanguageExecutor is infrastructure (leaf). LanguagePolicy is configuration consumed at evaluation time (no upstream feedback to FeatureEngine).

No cycles detected.

### J.5 All runtime DAGs connected

Full V1.2 runtime DAG:

```
InterviewSetup
  → LanguageProfile (ADR-028)
  → Question (QuestionIntelligence, V1.1)

CandidateCode / CandidateAnswer
  → LanguageExecutor (ADR-027)
  → Evaluation (EvaluationGovernance, ADR-011)
  → EvidenceSignal

EvidenceSignal
  → ObservationExtractor (ADR-016)
  → Observation → ObservationStore (ADR-017)

ObservationStore
  → FeatureEngine (ADR-020)
  → ProfileFeature → CandidateProfile (ADR-018)

CandidateProfile
  → KnowledgeGapEngine
  → KnowledgeGap

KnowledgeGap + CandidateProfile + LanguageProfile
  → CoachingEngine (ADR-025)
  → CoachingPlan + StudyRecommendation ← ResourceLibrary (ADR-030)

CandidateProfile + KnowledgeGap + CoachingPlan
  → NarrativeGenerator (ADR-023)
  → Narrative

CoachingPlan + Narrative + CandidateProfileSnapshot + ObservationStoreSnapshot
  → KnowledgeSnapshot (ADR-022)
  → SessionHistory (ADR-022)

SessionHistory
  → ReplayEngine (ADR-026)
  → LearningProgress (derived, ADR-016A)
```

All nodes connected. No orphaned components.

### J.6 All extension points accounted for

| Extension point | Reserved by | Status |
|---|---|---|
| New ProgrammingLanguage | ADR-027/031 | Frozen — new executor + policy only |
| New technology in ResourceLibrary | ADR-030 | Frozen — new resources only, zero model change |
| LearningPath | ADR-030 Section E | V1.3 reserved |
| Learning Catalog / Skill Catalog | ADR-030 Section H | V1.3 reserved |
| Recommendation Feedback / Effectiveness | ADR-030 Section H | V1.3 reserved |
| TenantContext | ADR-029 (not written; backlog) | V1.2 placeholder on SessionHistory |
| Calibration CI Gate | ADR-024 (not written; backlog) | V1.2 EPIC-06 |
| LearningUpdater | ADR-020 | V1.3 reserved |
| REST API | V2 | Explicitly deferred |

### J.7 All V1.1 frozen assets preserved

V1.1 produced and froze:
- Detector layer (EvidenceSignal sources): unmodified
- CandidateProfile (V1.1 shape with `dimension_scores`): extended by FeatureEngine in V1.2 without breaking V1.1 schema
- Humanizer follow-up engine: unmodified; Model B evaluation deferred
- Multi-language execution infrastructure: extended by LanguageExecutor abstraction in ADR-027
- Prompt catalog (ADR-012): unchanged
- Evaluation governance (ADR-011): unchanged
- ObservationStore / ObservationExtractor (designed in ADR-016): V1.2 implementation target; not V1.1 rewrite

All V1.1 assets preserved.

### J.8 All V1.2 architectural objectives satisfied

| V1.2 Objective | Covered by |
|---|---|
| Language independence | ADR-019, 027, 028, 031 |
| Knowledge model (Observation → Feature) | ADR-016, 017, 018, 020 |
| Knowledge freshness | ADR-021 |
| Narrative V2 | ADR-023 |
| Coaching engine | ADR-025 |
| Resource governance | ADR-030 |
| Calibration framework | ADR-024 (pending — not blocking coaching) |
| Session persistence | ADR-022, 026, 032 |
| Replay | ADR-026 |
| Candidate identity | ADR-016A |
| LanguagePolicy governance | ADR-031 |
| Profile snapshot strategy | ADR-032 |

All V1.2 architecture objectives satisfied. ADR-024 (Calibration Framework CI Gate) and ADR-029 (TenantContext placeholder) are documented gaps in the ADR backlog; neither blocks V1.2 implementation.

---

## Section K — Acceptance Checklist

- [x] ADR-030 frozen and accepted
- [x] Resource Library architecture frozen (LearningResource, StudyRecommendation, LearningPath, ResourceCollection, ResourceTag, ResourceMetadata, Difficulty, EstimatedDuration, Prerequisites, LearningOutcome, ResourceVersion)
- [x] Governance contract frozen (identifier, version, owner, tags, difficulty, estimated duration, language availability, technology coverage, quality status, last review date)
- [x] Recommendation strategy frozen (evidence-driven, KnowledgeGap-driven, LearningObjective-driven, language-independent, technology-independent, personalized, ranked, explainable, never random)
- [x] Resource lifecycle frozen (DRAFT → REVIEWED → APPROVED → DEPRECATED → ARCHIVED)
- [x] LearningPath concept introduced (V1.3 reserved; DAG topology and milestones deferred)
- [x] Future catalogs introduced (Learning, Technology, Skill, Certification, Provider, Resource Effectiveness — all V1.3 reserved)
- [x] Runtime DAG validated (single writer, single ownership, immutability, knowledge preservation, language independence, technology independence)
- [x] Architecture closure audit passed (16 ADRs reviewed; no duplicated responsibilities; no ownership ambiguity; no circular dependencies; all DAGs connected; all extension points accounted for)
- [x] No duplicated responsibilities (12 concerns mapped to unique owners)
- [x] V1.1 compatibility confirmed (all V1.1 assets preserved and unmodified)

---

## Decisions

1. `StudyRecommendation` is a governed resource reference, never a hardcoded string or LLM-chosen suggestion.
2. Every `LearningResource` must satisfy the 10-field governance contract (Section C) before reaching `APPROVED` status.
3. CoachingEngine is consumer-only with respect to the Resource Library; it never creates or mutates resources.
4. `StudyRecommendation` is immutable after `CoachingPlan` sealing; version-locked at recommendation time.
5. The recommendation ranking algorithm is deterministic, language-neutral, and technology-neutral.
6. `LearningPath` is reserved for V1.3; no V1.2 implementation.
7. Future catalogs (Learning, Technology, Skill, Certification, Provider) are reserved for V1.3.
8. `APPROVED` resources are subject to 90-day review cycles; overdue resources are demoted to `REVIEWED`.
9. `ARCHIVED` resources are retained for replay immutability; hard-delete is prohibited.
10. Architecture closure audit confirms no circular dependencies, no duplicated responsibilities, and full V1.2 objective coverage across all 16 accepted ADRs.

---

## Consequences

**Positive:**
- Recommendations are auditable, traceable, and deterministic
- Resource quality is independently governed from coaching logic
- Adding technologies or languages does not require changes to the recommendation engine
- Historical recommendations are stable across resource library evolution
- LearningPath and catalog concepts have a defined home for V1.3 extension

**Negative / Accepted trade-offs:**
- Resource Library requires governance process and operator tooling (V1.3)
- In V1.2, resource library is a static curated set; dynamic provider integration is deferred
- `LearningPath` deferral means multi-resource curricula are not available until V1.3

**Neutral:**
- ADR-024 (Calibration Framework CI Gate) and ADR-029 (TenantContext) remain in backlog; neither blocks V1.2 coaching implementation

---

*ADR-030 accepted. Architecture closed. V1.2 ready for implementation.*
