# ADR-025 — Coaching Intelligence Architecture

**Status:** Accepted — V1.2 Architecture (Action Layer Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Action Layer
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, ADR-019, ADR-020, ADR-021, ADR-022, ADR-023
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-022, ADR-023, ADR-026, ADR-030, ADR-032, ADR-067

---

## Context

ADR-016 through ADR-022 froze the complete V1.2 knowledge model. ADR-023 froze the Narrative Intelligence Architecture — the first Action Layer consumer. CoachingEngine is the second and parallel Action Layer consumer.

What remained undefined:

- The formal architecture of CoachingEngine as an action generator, not a report generator
- Why CoachingEngine is not a recommendation filter or a templating system
- The input boundary: which knowledge objects CoachingEngine may and may not read
- The output taxonomy: CoachingPlan, LearningObjectives, CoachingActions, StudyRecommendations, and their composition
- The coaching principles governing prioritisation, personalisation, and explainability
- The runtime flow positioning CoachingEngine as a terminal consumer
- The engineering invariants protecting knowledge layer immutability
- The relationship to ADR-067 (Behavioral Coaching Pipeline — Detector-to-CoachingEngine Decoupling)

This ADR freezes all of the above. No implementation, no contracts, no code.

---

## Decision

**CoachingEngine is the Knowledge-to-Action translator of the platform. It is not a report generator.**

Its role is to transform the platform's structured knowledge about a candidate — expressed as KnowledgeGaps, ProfileFeatures, and LearningProgress — into a prioritised, personalised, actionable coaching plan. Recommendations must be ranked, evidence-driven, and traceable to ProfileFeatures or KnowledgeGaps. The CoachingEngine determines what the candidate should do next — not what they did.

---

## SECTION A — Purpose: Knowledge-to-Action Translator

### Why CoachingEngine Is Not a Report Generator

A report generator assembles pre-existing findings into a presentational format. CoachingEngine does more:

1. **It synthesises knowledge into actions.** CoachingEngine receives KnowledgeGaps and ProfileFeatures — structured, ranked, prioritised knowledge — and derives concrete actions from them. The actions are not pre-written templates; they are derived from the candidate's specific knowledge state.

2. **It applies prioritisation logic.** Not all gaps are equally important. CoachingEngine must rank CoachingActions by severity, impact on interview readiness, and estimated learning cost. This ranking is an algorithmic decision — not a display order.

3. **It generates a forward-looking plan.** NarrativeGenerator describes what happened. CoachingEngine prescribes what should happen. The CoachingPlan is future-oriented: it is a directive, not a summary.

4. **It personalises to the candidate's knowledge state.** Two candidates with the same KnowledgeGaps may receive different CoachingPlans based on their LearningProgress, ProfileFeature confidence levels, and session history depth. Personalisation is a first-class CoachingEngine responsibility.

5. **It is language-independent.** CoachingEngine operates on ProfileFeature identities and KnowledgeGap identities — both of which are abstract, language-independent domain concepts (ADR-018, ADR-019). The same CoachingEngine logic produces valid plans for Python candidates and Go candidates without modification.

### The Two Terminal Action Layer Consumers

```
Knowledge Layer (frozen)
    │
    ├──→ NarrativeGenerator    — translates knowledge into human understanding
    │        Output: Narrative (NarrativeSections + NarrativeInsights)
    │
    └──→ CoachingEngine         — translates knowledge into actions
             Output: CoachingPlan (LearningObjectives + CoachingActions)
```

Both consumers are parallel, independent, terminal, and read-only with respect to the knowledge layer.

---

## SECTION B — Input Boundary

### Permitted Inputs

CoachingEngine may consume the following knowledge objects:

| Input | Source | Purpose |
|---|---|---|
| `CandidateProfile` | FeatureEngine (read-only) | Access to all ProfileFeatures with confidence, evidence count, quality metadata — grounds every CoachingAction |
| `KnowledgeGaps` | KnowledgeGapEngine output (read-only) | The primary action driver; gaps determine what must be addressed |
| `ProfileFeatures` | Via CandidateProfile (read-only) | Confidence levels and quality metadata inform priority ranking |
| `LearningProgress` | Derived from SessionHistory[] (read-only) | Cross-session view; enables adaptive coaching that avoids repeating prior session recommendations |
| `LanguageProfile` | Session configuration (read-only) | Active programming languages; scopes StudyRecommendations to relevant language ecosystem |
| `Interview metadata` | Session configuration (read-only) | Role, seniority, session index — contextualises priority and action framing |
| `Narrative` | ADR-023 output (read-only; conditional) | May be consumed for coherence checking only — CoachingEngine must not derive new knowledge from Narrative prose |

### Forbidden Inputs

CoachingEngine must **never** read:

| Forbidden | Reason |
|---|---|
| `ObservationStore` | Direct access to raw observations bypasses the FeatureEngine knowledge construction contract; CoachingEngine must consume knowledge, not evidence |
| `EvidenceStore` | Same reason; EvidenceStore contains raw signals, not interpreted knowledge |
| `FeatureEngine internals` | FeatureEngine is the knowledge producer; CoachingEngine is a consumer; crossing the boundary inverts the pipeline |
| `Detector outputs` | Pattern detectors produce intermediate reasoning artefacts; CoachingEngine must consume the final knowledge product (ProfileFeatures via CandidateProfile), not the reasoning path |
| `ReasonerDecision internals` | Same reason as detector outputs; ADR-067 enforces this boundary explicitly |

**Frozen invariant B-01:** CoachingEngine reads KnowledgeGaps and CandidateProfile (ProfileFeatures) as its sole knowledge inputs. It never queries ObservationStore, EvidenceStore, or any FeatureEngine internal.

**Frozen invariant B-02:** CoachingEngine is a read-only consumer of all its inputs. It never mutates any knowledge object.

**Frozen invariant B-03:** Narrative may be read for coherence alignment only. CoachingEngine never re-derives KnowledgeGaps or ProfileFeature values from Narrative prose. Narrative is not a knowledge source.

---

## SECTION C — Output Taxonomy

### CoachingPlan (Root Object)

The root output of CoachingEngine. One CoachingPlan is produced per session. The CoachingPlan is stored inside `KnowledgeSnapshot` at session close (ADR-022).

```
CoachingPlan
    ├── objectives:            LearningObjective[]     (1..N; ranked)
    ├── actions:               CoachingAction[]        (1..N; ranked by priority)
    ├── study_recommendations: StudyRecommendation[]   (0..N; optional resource links)
    ├── future_backlog:        FutureActionItem[]      (0..N; deferred items for next session)
    ├── priority_summary:      str                     (human-readable ranking rationale)
    └── schema_version:        str                     (coaching schema version for ADR-022 compatibility)
```

### LearningObjective (Strategic Goal)

A LearningObjective is a high-level strategic goal that the candidate should achieve before the next interview. It groups related CoachingActions.

```
LearningObjective
    ├── objective_id:          str              (stable identifier for cross-session tracking)
    ├── title:                 str              (short, action-oriented label)
    ├── description:           str              (LLM-generated or template-filled prose)
    ├── source_gap_ids:        KnowledgeGapId[] (KnowledgeGaps this objective addresses)
    ├── source_feature_ids:    FeatureIdentity[] (ProfileFeatures that informed this objective)
    ├── priority_rank:         int              (1 = highest priority; determined by ranking algorithm)
    └── is_traceable:          bool             (must be True; False is an invariant violation)
```

### CoachingAction (Tactical Action)

A CoachingAction is a specific, concrete activity the candidate should perform. It belongs to exactly one LearningObjective.

```
CoachingAction
    ├── action_id:             str              (stable identifier)
    ├── action_type:           CoachingActionType  (STUDY | PRACTICE | REVIEW | BUILD | REVISIT)
    ├── title:                 str
    ├── description:           str              (specific, measurable, time-bounded if possible)
    ├── source_gap_id:         KnowledgeGapId   (exactly one KnowledgeGap this action addresses)
    ├── source_feature_id:     FeatureIdentity  (exactly one ProfileFeature that contextualises priority)
    ├── priority_score:        float            (composite priority score from ranking algorithm)
    ├── estimated_effort:      str              (LOW | MEDIUM | HIGH — effort estimate)
    └── is_traceable:          bool             (must be True; False is an invariant violation)
```

### StudyRecommendation (Resource Pointer)

A StudyRecommendation is a pointer to a specific learning resource. It is optional and language-scoped.

```
StudyRecommendation
    ├── recommendation_id:     str
    ├── resource_type:         StudyResourceType  (DOCUMENTATION | EXERCISE | ARTICLE | VIDEO | PROJECT)
    ├── title:                 str
    ├── url:                   str | None       (may be absent; ADR-030 governs resource library)
    ├── language_scope:        ProgrammingLanguage | None  (None = language-independent resource)
    ├── related_action_id:     str              (CoachingAction this resource supports)
    └── is_curated:            bool             (True if from curated library; False if LLM-suggested)
```

### FutureActionItem (Deferred Backlog)

Items the CoachingEngine identifies as important but deprioritises for the current session — deferred to the next session coaching plan.

```
FutureActionItem
    ├── item_id:               str
    ├── title:                 str
    ├── rationale:             str              (why deferred, not dropped)
    ├── source_gap_id:         KnowledgeGapId
    └── deferred_from_session: int              (session_index; enables continuity tracking)
```

### Output Taxonomy Frozen Invariants

**C-01:** Every LearningObjective carries at least one `source_gap_ids` entry and at least one `source_feature_ids` entry. An objective with zero sources is forbidden.

**C-02:** Every CoachingAction carries exactly one `source_gap_id` and exactly one `source_feature_id`. An action without traceable sources is forbidden.

**C-03:** `schema_version` is always populated at generation time. It is stored in `KnowledgeSnapshot.coaching_schema_version` (ADR-022).

**C-04:** StudyRecommendations are optional; their absence does not invalidate a CoachingPlan. A CoachingPlan without StudyRecommendations is valid if it contains at least one CoachingAction.

**C-05:** CoachingActions are ranked by `priority_score`. The ranking algorithm is deterministic: given the same inputs, it produces the same ordering.

---

## SECTION D — Coaching Principles

All six principles are frozen. Violation of any principle is an architectural breach.

### Principle 1: Evidence-Driven

Every CoachingAction and LearningObjective must map to a KnowledgeGap or a ProfileFeature. CoachingEngine does not invent problems for the candidate to solve. The coaching plan reflects what the platform actually observed.

### Principle 2: Actionable

Every item in the CoachingPlan must describe something the candidate can do, not just something they lack. "Study dynamic programming" is actionable. "Lacks algorithmic depth" is an observation — it belongs in the Narrative, not the CoachingPlan.

### Principle 3: Prioritised

All CoachingActions must be ranked. Ranking is not cosmetic ordering — it is an algorithmic output of the priority ranking model. The candidate receives a signal about what to address first. An unranked CoachingPlan is an invariant violation.

### Principle 4: Personalised

CoachingEngine uses LearningProgress (cross-session derived view) to avoid repeating prior session recommendations that the candidate has already addressed. A candidate who received "Practice dynamic programming" in session 1 and showed improvement in session 2 should not receive the same recommendation in session 2.

### Principle 5: Language-Independent

CoachingEngine operates on language-independent knowledge: ProfileFeature identities (ADR-018), KnowledgeGap identities, LearningObjective identities. Language-specific framing (e.g., "Study Python generators") enters only in StudyRecommendation scope via `language_scope`, not in the core CoachingAction logic.

### Principle 6: Explainable

Every LearningObjective and CoachingAction carries its source KnowledgeGap and ProfileFeature identities. A human reviewer can audit why any recommendation was made without accessing CoachingEngine internals.

---

## SECTION E — Runtime Positioning

### Canonical Position in the Pipeline

```
CandidateProfile (ProfileFeatures — produced by FeatureEngine)
    │
    ├──→ KnowledgeGapEngine ──→ KnowledgeGap[]
    │                              │
    ▼                              ▼
    └──────────────────────────────→ CoachingEngine
                                         │
                                         ▼  [single writer: CoachingEngine]
                                    CoachingPlan
                                         │
                                         ▼  [stored at session close]
                                    KnowledgeSnapshot
                                         │
                                         ▼  [written once by session completion pipeline]
                                    SessionHistory
```

### Parallel Runtime (Action Layer)

```
CandidateProfile
    │
    ├──→ NarrativeGenerator ──→ Narrative
    │
    └──→ CoachingEngine     ──→ CoachingPlan
    
Both outputs ──→ KnowledgeSnapshot ──→ SessionHistory
```

### Runtime Invariant Validation

| Property | Status |
|---|---|
| **Single writer** | CoachingEngine is the sole writer of CoachingPlan. No other component produces or modifies CoachingPlan. ✓ |
| **Immutability** | CoachingPlan is immutable after generation. Once stored in KnowledgeSnapshot, no field may be updated. ✓ |
| **Determinism** | Given the same ProfileFeatures and KnowledgeGaps, CoachingEngine always produces the same CoachingPlan structure and the same priority ranking. ✓ |
| **Terminal consumer** | CoachingEngine reads knowledge; it writes CoachingPlan; it does not write back to CandidateProfile, ObservationStore, or any upstream component. ✓ |
| **No upstream writes** | CoachingPlan never flows back into the knowledge pipeline. The DAG has no cycles at the CoachingPlan node. ✓ |
| **Language independence** | CoachingEngine logic is language-independent. Language scoping enters only at StudyRecommendation level. ✓ |

---

## SECTION F — Engineering Invariants

| Invariant | Statement |
|---|---|
| **CE-01** | CoachingPlan never changes knowledge. CoachingEngine is a terminal consumer. It reads knowledge and produces actions. It never writes to CandidateProfile, FeatureEngine, ObservationStore, or EvidenceStore. |
| **CE-02** | CoachingPlan never modifies CandidateProfile. The profile is the input; the coaching plan is the output. No feedback loop exists. |
| **CE-03** | CoachingEngine never computes ProfileFeatures. ProfileFeature computation is exclusively FeatureEngine's responsibility. CoachingEngine receives already-computed ProfileFeatures. |
| **CE-04** | Coaching is terminal. The CoachingPlan is the final action directive for the session. Nothing downstream of CoachingPlan writes back upstream. |
| **CE-05** | Every CoachingAction is traceable. An action without a KnowledgeGap reference and a ProfileFeature reference is an invariant violation detectable at generation time. |
| **CE-06** | Priority ranking is deterministic. Given the same inputs, the ranking algorithm produces the same output. Ranking is not delegated to an LLM. |
| **CE-07** | CoachingEngine is language-independent in structure. CoachingAction taxonomy does not reference ProgrammingLanguage. Language scoping is permitted only in StudyRecommendation. |
| **CE-08** | CoachingPlan is immutable after session close. Once stored in KnowledgeSnapshot (ADR-022), no CoachingPlan field may be updated, extended, or deleted. |
| **CE-09** | Narrative is not a knowledge source. CoachingEngine may read Narrative for coherence only. It never derives KnowledgeGaps or ProfileFeature values from Narrative prose. |

---

## SECTION G — Relationship to ADR-067

ADR-067 (Behavioral Coaching Pipeline — Detector-to-CoachingEngine Decoupling) established that:

- `CandidateProfile.features` is the only interface between detectors and CoachingEngine
- CoachingEngine must not read detector outputs or intermediate reasoning artefacts

ADR-025 extends this frozen boundary:

- ADR-067 defines the **boundary** (what CoachingEngine must not read)
- ADR-025 defines the **architecture** (what CoachingEngine produces, how it is structured, and what principles govern it)

These two ADRs are complementary and non-conflicting. ADR-067 is preserved unchanged.

---

## SECTION H — V1.1 Compatibility

**Confirmed. No frozen V1.1 asset requires change.**

| V1.1 Asset | Status |
|---|---|
| `EvidenceSignal` schema | Protected. CoachingEngine does not read EvidenceSignal. |
| `EvidenceStore` contract | Protected. CoachingEngine does not read EvidenceStore. |
| `CandidateProfile` V1.1 fields | Protected. CoachingEngine reads but never writes. |
| Pattern detectors (10 existing) | Protected. CoachingEngine does not read detector outputs. |
| `ReasonerService` | Protected. CoachingEngine is downstream of FeatureEngine; Reasoner is invisible to it. |
| `EvaluationEngine` | Protected. CoachingEngine reads KnowledgeGaps (derived from evaluation) but not EvaluationEngine internals. |

---

## SECTION I — ADR Backlog Update

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-022 | Knowledge Persistence & SessionHistory Architecture | ACCEPTED | ACCEPTED (unchanged) |
| ADR-023 | Narrative Intelligence Architecture | ACCEPTED | ACCEPTED (unchanged) |
| ADR-025 | Coaching Intelligence Architecture | NEXT MILESTONE — P1 (parallel) | **ACCEPTED** |
| ADR-026 | Replay Snapshot Model | UNBLOCKED | Unchanged — unblocked |
| ADR-030 | StudyRecommendation Resource Library Governance | Blocked on ADR-025 | **UNBLOCKED** |
| ADR-032 | CandidateProfileSnapshot Strategy | UNBLOCKED | Unchanged — unblocked |

---

## SECTION J — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ ADR-025 frozen | **FROZEN** |
| ✓ CoachingEngine purpose frozen | **FROZEN** — Section A: knowledge-to-action translator, not report generator |
| ✓ Input boundaries frozen | **FROZEN** — Section B: KnowledgeGaps + CandidateProfile permitted; ObservationStore + EvidenceStore + Detector outputs forbidden |
| ✓ Output taxonomy frozen | **FROZEN** — Section C: CoachingPlan, LearningObjectives, CoachingActions, StudyRecommendations, FutureActionBacklog; 5 invariants (C-01 through C-05) |
| ✓ Coaching principles frozen | **FROZEN** — Section D: 6 principles; evidence-driven, actionable, prioritised, personalised, language-independent, explainable |
| ✓ Runtime validated | **VALIDATED** — Section E: single writer, immutability, determinism, terminal consumer, no upstream writes, language independence |
| ✓ Engineering invariants frozen | **CONFIRMED** — Section F: 9 invariants (CE-01 through CE-09) |
| ✓ Language independence confirmed | **CONFIRMED** — CoachingAction taxonomy is language-independent; language scoping permitted only in StudyRecommendation |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section H: no frozen V1.1 asset requires change |
| ✓ No duplicated responsibilities | **CONFIRMED** — CoachingEngine owns action; NarrativeGenerator owns communication; no overlap |
| ✓ ADR-067 compatibility confirmed | **CONFIRMED** — Section G: ADR-025 extends ADR-067 boundary; no conflict |

---

## Final Recommendation

**ADR-025 is ACCEPTED.**

CoachingEngine's architecture is frozen. It is the knowledge-to-action translator of the platform — not a report generator. All input boundaries, output taxonomy, coaching principles, runtime positioning, and engineering invariants are frozen. The Action Layer is complete: both NarrativeGenerator (ADR-023) and CoachingEngine (ADR-025) are accepted.

**Critical path forward:**

- ADR-026 (Replay Snapshot Model) — unblocked; reads KnowledgeSnapshot which now contains both Narrative and CoachingPlan
- ADR-030 (StudyRecommendation Resource Library Governance) — unblocked by ADR-025
- ADR-032 (CandidateProfileSnapshot Strategy) — unblocked; all preconditions met

---

## Rationale

CoachingEngine must be architecturally distinct from a generic recommendation template system because effective coaching depends on ranking quality, personalisation, and evidence traceability — three properties that a template system cannot provide. By designing CoachingEngine as a knowledge-to-action translator with a deterministic ranking algorithm and full source traceability, the platform guarantees that every coaching recommendation is auditable, personalised to the candidate's actual knowledge state, and non-redundant with prior session coaching.

The strict separation between CoachingEngine (actions) and NarrativeGenerator (communication) prevents responsibility overlap. Both are necessary; neither can substitute for the other.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| CoachingEngine as a generic LLM recommendation generator (KnowledgeGaps serialised and injected into a prompt) | No traceability guarantees; LLM-derived ranking is non-deterministic; personalisation requires LearningProgress access which an unstructured prompt cannot leverage |
| CoachingEngine reading ObservationStore directly | Bypasses the knowledge abstraction boundary; violates ADR-067; couples coaching to raw evidence schema |
| Merging NarrativeGenerator and CoachingEngine into a single "Report Generator" | Conflates communication (narrative) with action (coaching); produces monolithic outputs that cannot be stored, replayed, or versioned independently; breaks single responsibility |
| Delegating priority ranking to an LLM | Ranking non-determinism makes CoachingPlan tests unstable; priority is an algorithmic property, not a prose property |
| Storing CoachingPlan outside KnowledgeSnapshot | Breaks the self-sufficiency principle of KnowledgeSnapshot (ADR-022); replay would require a separate CoachingPlan query |

## Consequences

### Positive

- Every coaching recommendation is auditable without accessing CoachingEngine internals
- Deterministic ranking makes CoachingPlan output testable (same inputs → same priority order)
- Clear separation between CoachingEngine (action) and NarrativeGenerator (communication)
- Language independence enables multi-language platform extension without coaching redesign
- Immutable CoachingPlan inside KnowledgeSnapshot guarantees replay fidelity (ADR-022)
- FutureActionBacklog enables cross-session coaching continuity without requiring live session state

### Negative / Risks

- KnowledgeGap coverage determines coaching coverage — thin gap analysis produces thin coaching plans
- Priority ranking algorithm design (gap severity × IRS impact formula) is deferred to EPIC-04 implementation
- LearningProgress cross-session derivation adds query cost at coaching generation time (implementation concern)
- StudyRecommendation curation is governed by a separate ADR (ADR-030); until ADR-030 is accepted, StudyRecommendations may be LLM-suggested only

## Implementation Evidence

Architecture only. No production files modified.
Relevant existing assets (unchanged):
- `domain/profile/candidate_profile.py` (unchanged — CoachingEngine input)
- `domain/contracts/reasoning/evidence_signal.py` (frozen — CoachingEngine does not read this)
- All V1.1 evaluation pipeline files (unchanged)

## Review Trigger

- When the priority ranking algorithm (gap severity × IRS impact formula) requires architectural changes
- When LearningProgress cross-session derivation cost requires caching changes to SessionHistory reads
- When multi-language StudyRecommendations require a LanguagePolicy injection model
- When FutureActionBacklog cross-session continuity becomes a first-class feature requiring its own ADR
