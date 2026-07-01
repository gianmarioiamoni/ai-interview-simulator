# ADR-023 — Narrative Intelligence Architecture

**Status:** Accepted — V1.2 Architecture (Action Layer Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Action Layer
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, ADR-019, ADR-020, ADR-021, ADR-022
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-022, ADR-025, ADR-026, ADR-032

---

## Context

ADR-016 through ADR-022 froze the complete V1.2 knowledge model — from raw EvidenceSignal through Observation, FeatureEngine, ProfileFeature, CandidateProfile, freshness, replay, and persistence. Every knowledge concept has been defined, frozen, and validated.

What remained undefined:

- The formal architecture of NarrativeGenerator as the first Action Layer consumer
- Why NarrativeGenerator is not an LLM wrapper but a knowledge-to-human-understanding translator
- The input boundary: which knowledge objects NarrativeGenerator may and may not read
- The output taxonomy: Narrative, NarrativeSection, NarrativeInsight, and their composition
- The narrative principles governing what statements are permitted and what is forbidden
- The runtime flow positioning NarrativeGenerator as a terminal consumer
- The engineering invariants protecting knowledge layer immutability

This ADR freezes all of the above. No implementation, no contracts, no code.

---

## Decision

**NarrativeGenerator is the Knowledge-to-Human-Understanding translator of the platform. It is not an LLM wrapper.**

Its role is to transform the platform's structured knowledge about a candidate — expressed as ProfileFeatures, KnowledgeGaps, and KnowledgeSnapshot — into human-readable, evidence-grounded, explainable narrative. LLM variability is permitted only inside prose generation. Every statement the LLM produces must be traceable to a ProfileFeature. The structure of the output is deterministic.

---

## SECTION A — Purpose: Knowledge-to-Human-Understanding Translator

### Why NarrativeGenerator Is Not an LLM Wrapper

An LLM wrapper is a thin translation layer: input text in, output text out, with no knowledge of the semantic content it processes. NarrativeGenerator is the opposite:

1. **It knows what it received.** NarrativeGenerator receives structured, typed, versioned knowledge: ProfileFeature objects with confidence scores, evidence counts, quality metadata, and provenance. It does not receive a text summary — it receives the platform's formal model of the candidate.

2. **It enforces evidence traceability.** Every statement NarrativeGenerator produces — whether about strengths, weaknesses, or growth areas — must map to one or more ProfileFeatures. A statement without a traceable ProfileFeature is a hallucination and is architecturally forbidden.

3. **It applies deterministic structure.** The sections of the Narrative — Executive Summary, Strengths, Weaknesses, Growth Recommendations — are determined by the input knowledge, not by the LLM. The LLM generates prose within pre-determined structural slots.

4. **It is the boundary between knowledge and language.** FeatureEngine produces language-independent knowledge. NarrativeGenerator translates that knowledge into language-specific communication. The translation is one-way: knowledge becomes prose; prose never becomes knowledge.

5. **It carries communication intent.** A NarrativeGenerator decision about which insights to surface, which weaknesses to soften, and which growth recommendations to prioritise is a communication design decision — not an LLM prompt decision. These decisions are governed by the Narrative Principles (Section D).

### The Three Platform Action Consumers

The V1.2 Action Layer has two terminal consumers of knowledge:

```
Knowledge Layer (frozen)
    │
    ├──→ NarrativeGenerator    — translates knowledge into human understanding
    │        Output: Narrative (NarrativeSections + NarrativeInsights)
    │
    └──→ CoachingEngine         — translates knowledge into actions
             Output: CoachingPlan (LearningObjectives + CoachingActions)
```

NarrativeGenerator is responsible for communication. CoachingEngine is responsible for action. They are parallel, independent, and terminal.

---

## SECTION B — Input Boundary

### Permitted Inputs

NarrativeGenerator may consume the following knowledge objects:

| Input | Source | Purpose |
|---|---|---|
| `CandidateProfile` | FeatureEngine (read-only) | Access to all ProfileFeatures with confidence, evidence count, quality metadata, and provenance |
| `KnowledgeSnapshot` | ADR-022 (read-only) | Self-contained session closure reference; used when generating post-session narrative |
| `ProfileFeatures` | Via CandidateProfile (read-only) | The primary knowledge input; every narrative statement must trace to a ProfileFeature |
| `KnowledgeGaps` | KnowledgeGapEngine output (read-only) | Weaknesses and growth areas derived from evaluation results |
| `Interview metadata` | Session configuration (read-only) | Role, seniority, session index, mode — contextualises narrative framing |
| `LanguageProfile` | Session configuration (read-only) | Active programming languages; enables language-aware narrative framing |
| `Evaluation summary` | EvaluationEngine output (read-only) | Aggregate dimension scores; provides session performance context |

### Forbidden Inputs

NarrativeGenerator must **never** read:

| Forbidden | Reason |
|---|---|
| `ObservationStore` | Direct access to raw observations bypasses the FeatureEngine knowledge construction contract; NarrativeGenerator must consume knowledge, not evidence |
| `EvidenceStore` | Same reason; EvidenceStore contains raw signals, not interpreted knowledge |
| `FeatureEngine internals` | FeatureEngine is the knowledge producer; NarrativeGenerator is a consumer; crossing the boundary inverts the pipeline |
| `Detector outputs` | Pattern detectors produce intermediate reasoning artefacts; NarrativeGenerator must consume the final knowledge product (ProfileFeatures), not the reasoning path |
| `ReasonerDecision internals` | Same reason as detector outputs |

**Frozen invariant B-01:** NarrativeGenerator reads CandidateProfile (ProfileFeatures) and KnowledgeGaps as its sole knowledge inputs. It never queries ObservationStore, EvidenceStore, or any FeatureEngine internal.

**Frozen invariant B-02:** NarrativeGenerator is a read-only consumer of all its inputs. It never mutates any knowledge object.

---

## SECTION C — Output Taxonomy

### Narrative (Root Object)

The root output of NarrativeGenerator. One Narrative is produced per session. The Narrative is stored inside `KnowledgeSnapshot` at session close (ADR-022).

```
Narrative
    ├── executive_summary:     NarrativeSection  (mandatory)
    ├── strengths:             NarrativeSection  (mandatory)
    ├── weaknesses:            NarrativeSection  (mandatory)
    ├── growth_areas:          NarrativeSection  (mandatory)
    ├── recommendations:       NarrativeSection  (mandatory — high-level only)
    ├── insights:              NarrativeInsight[]  (0..N)
    └── schema_version:        str (narrative schema version for ADR-022 compatibility)
```

### NarrativeSection (Structural Unit)

A NarrativeSection is one thematic segment of the Narrative. Its structure is deterministic — determined by the input ProfileFeatures. Its prose is LLM-generated within the section's semantic constraints.

```
NarrativeSection
    ├── section_type:          NarrativeSectionType  (EXECUTIVE_SUMMARY | STRENGTHS | WEAKNESSES | GROWTH | RECOMMENDATIONS)
    ├── prose:                 str  (LLM-generated; variable)
    ├── feature_references:    FeatureIdentity[]  (ProfileFeatures that ground this section)
    ├── confidence_context:    str  (LLM-generated description of evidence confidence)
    └── is_evidence_grounded:  bool  (must be True for all sections; False is an invariant violation)
```

### NarrativeInsight (Atomic Finding)

A NarrativeInsight is a single, atomic observation about the candidate that merits explicit surfacing. It is more specific than a NarrativeSection.

```
NarrativeInsight
    ├── insight_type:          NarrativeInsightType  (STRENGTH_SIGNAL | RISK_SIGNAL | GROWTH_OPPORTUNITY | ANOMALY)
    ├── prose:                 str  (LLM-generated; variable)
    ├── source_feature_id:     FeatureIdentity  (exactly one ProfileFeature this insight traces to)
    ├── confidence:            float  (inherited from source ProfileFeature)
    └── is_traceable:          bool  (must be True; False is an invariant violation)
```

### Output Taxonomy Frozen Invariants

**C-01:** Every NarrativeSection carries at least one `feature_references` entry. A section with zero feature references is forbidden.

**C-02:** Every NarrativeInsight carries exactly one `source_feature_id`. A NarrativeInsight without a traceable ProfileFeature is forbidden.

**C-03:** Recommendations in the Narrative are high-level only. Specific study plans, resources, and ranked action items are the responsibility of CoachingEngine (ADR-025), not NarrativeGenerator.

**C-04:** `schema_version` is always populated at generation time. It is stored in `KnowledgeSnapshot.narrative_schema_version` (ADR-022).

---

## SECTION D — Narrative Principles

All five principles are frozen. Violation of any principle is an architectural breach.

### Principle 1: Evidence-Based

Every narrative statement must be grounded in ProfileFeature data. NarrativeGenerator does not invent capabilities, weaknesses, or recommendations. The LLM's role is to express what the knowledge model already knows — not to hypothesise what it does not.

### Principle 2: Explainable

Every NarrativeSection and NarrativeInsight must carry the ProfileFeature identity (or identities) that grounds it. A human reviewer must be able to trace every statement in the Narrative back to a specific ProfileFeature without accessing any LLM internals.

### Principle 3: Deterministic Structure

The structure of the Narrative — which sections exist, in what order, with what section types — is determined by the algorithm, not the LLM. Given the same ProfileFeatures and KnowledgeGaps, the same NarrativeSections are always produced (with LLM-variable prose inside each section).

### Principle 4: LLM Variability Contained Inside Prose

LLM non-determinism is permitted only inside the `prose` field of NarrativeSection and NarrativeInsight. Section existence, section type, feature references, confidence values, and traceability flags are all computed deterministically. The LLM is a prose generator — it does not determine content strategy.

### Principle 5: No Hallucinated Facts

NarrativeGenerator must never produce a statement that cannot be traced to a ProfileFeature. If a ProfileFeature does not exist for a topic, that topic is not mentioned in the Narrative. Confidence thresholds may gate which ProfileFeatures are narratable. Absence of evidence is not evidence of absence — but absence of a ProfileFeature means silence, not speculation.

---

## SECTION E — Runtime Positioning

### Canonical Position in the Pipeline

```
CandidateProfile (ProfileFeatures — produced by FeatureEngine)
    │
    ▼  [read-only consumer: NarrativeGenerator]
NarrativeGenerator
    │
    ▼  [single writer: NarrativeGenerator]
Narrative (NarrativeSections + NarrativeInsights)
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
| **Single writer** | NarrativeGenerator is the sole writer of Narrative. No other component produces or modifies Narrative. ✓ |
| **Immutability** | Narrative is immutable after generation. Once stored in KnowledgeSnapshot, no field may be updated. ✓ |
| **Determinism** | Given the same ProfileFeatures and KnowledgeGaps, NarrativeGenerator always produces the same Narrative structure (LLM prose variation is expected and accepted). ✓ |
| **Terminal consumer** | NarrativeGenerator reads knowledge; it writes Narrative; it does not write back to CandidateProfile, ObservationStore, or any upstream component. ✓ |
| **No upstream writes** | Narrative never flows back into the knowledge pipeline. The DAG has no cycles at the Narrative node. ✓ |

---

## SECTION F — Engineering Invariants

| Invariant | Statement |
|---|---|
| **N-01** | Narrative never changes knowledge. NarrativeGenerator is a terminal consumer. It reads knowledge and produces prose. It never writes to CandidateProfile, FeatureEngine, ObservationStore, or EvidenceStore. |
| **N-02** | Narrative never modifies CandidateProfile. The profile is the input; the narrative is the output. No feedback loop exists. |
| **N-03** | Narrative never computes ProfileFeatures. ProfileFeature computation is exclusively FeatureEngine's responsibility. NarrativeGenerator receives already-computed ProfileFeatures. |
| **N-04** | Narrative is terminal. The Narrative is the final communication artefact for the session. Nothing downstream of Narrative writes back upstream. |
| **N-05** | Every narrative statement is traceable. A statement without a ProfileFeature reference is an invariant violation detectable at generation time. |
| **N-06** | LLM variability is bounded. The LLM operates inside structural constraints defined by the algorithm. The LLM never determines section existence, feature references, or confidence values. |
| **N-07** | Narrative is language-independent in structure. The NarrativeSection taxonomy (STRENGTHS, WEAKNESSES, etc.) does not reference any ProgrammingLanguage. Language-specific framing is permitted inside `prose` only. |
| **N-08** | Narrative is immutable after session close. Once stored in KnowledgeSnapshot (ADR-022), no Narrative field may be updated, extended, or deleted. |

---

## SECTION G — V1.1 Compatibility

**Confirmed. No frozen V1.1 asset requires change.**

| V1.1 Asset | Status |
|---|---|
| `EvidenceSignal` schema | Protected. NarrativeGenerator does not read EvidenceSignal. |
| `EvidenceStore` contract | Protected. NarrativeGenerator does not read EvidenceStore. |
| `CandidateProfile` V1.1 fields | Protected. NarrativeGenerator reads but never writes. |
| Pattern detectors (10 existing) | Protected. NarrativeGenerator does not read detector outputs. |
| `ReasonerService` | Protected. NarrativeGenerator is downstream of FeatureEngine; Reasoner is invisible to it. |
| `EvaluationEngine` | Protected. NarrativeGenerator reads Evaluation summary only (read-only aggregate). |

---

## SECTION H — ADR Backlog Update

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-022 | Knowledge Persistence & SessionHistory Architecture | ACCEPTED | ACCEPTED (unchanged) |
| ADR-023 | NarrativeGenerator Profile-Feature-Aware Prompt Design | NEXT MILESTONE — P1 | **ACCEPTED** |
| ADR-025 | CoachingEngine Ranking Algorithm | P2; parallel | **NEXT MILESTONE — P1 (parallel)** |
| ADR-026 | Replay Snapshot Model | UNBLOCKED | Unchanged — unblocked |
| ADR-032 | CandidateProfileSnapshot Strategy | UNBLOCKED | Unchanged — unblocked |

---

## SECTION I — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ ADR-023 frozen | **FROZEN** |
| ✓ NarrativeGenerator purpose frozen | **FROZEN** — Section A: knowledge-to-human-understanding translator, not LLM wrapper |
| ✓ Input boundaries frozen | **FROZEN** — Section B: CandidateProfile + KnowledgeGaps permitted; ObservationStore + EvidenceStore + Detector outputs forbidden |
| ✓ Output taxonomy frozen | **FROZEN** — Section C: Narrative, NarrativeSection, NarrativeInsight; 4 invariants (C-01 through C-04) |
| ✓ Narrative principles frozen | **FROZEN** — Section D: 5 principles; evidence-based, explainable, deterministic structure, LLM variability contained, no hallucinated facts |
| ✓ Runtime validated | **VALIDATED** — Section E: single writer, immutability, determinism, terminal consumer, no upstream writes |
| ✓ Engineering invariants frozen | **CONFIRMED** — Section F: 8 invariants (N-01 through N-08) |
| ✓ Language independence confirmed | **CONFIRMED** — NarrativeSection taxonomy is language-independent; language framing permitted only inside prose |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section G: no frozen V1.1 asset requires change |
| ✓ No duplicated responsibilities | **CONFIRMED** — Recommendations are high-level only; specific coaching actions belong to ADR-025 |

---

## Final Recommendation

**ADR-023 is ACCEPTED.**

NarrativeGenerator's architecture is frozen. It is the knowledge-to-human-understanding translator of the platform — not an LLM wrapper. All input boundaries, output taxonomy, narrative principles, runtime positioning, and engineering invariants are frozen.

**Immediate next action: ADR-025 (CoachingEngine Ranking Algorithm)** — the parallel Action Layer consumer that translates knowledge into actions rather than prose.

---

## Rationale

NarrativeGenerator must be architecturally distinct from a generic LLM wrapper because the platform's credibility depends on every narrative statement being traceable to structured knowledge. An unconstrained LLM wrapper will hallucinate plausible-sounding but groundless statements. By making NarrativeGenerator a knowledge-aware translator — one that receives structured ProfileFeatures and produces structurally-constrained prose — the platform guarantees that the narrative reflects what was actually observed, not what the LLM imagines.

The containment of LLM variability to the `prose` field only is the architectural mechanism that enables this guarantee. The structure is deterministic; only the language is variable.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| NarrativeGenerator as a pure LLM wrapper (CandidateProfile text-serialised and injected into a prompt) | No traceability guarantees; LLM may hallucinate facts; narrative structure becomes unpredictable; cannot guarantee evidence grounding |
| NarrativeGenerator reading ObservationStore directly | Bypasses the knowledge abstraction boundary; couples Narrative to raw evidence schema; violates the principle that narrative consumers receive knowledge, not evidence |
| Delegating high-level recommendations to NarrativeGenerator and keeping specific coaching in CoachingEngine | Creates overlap between the two Action Layer consumers; recommendation responsibility must be unambiguous |
| Storing Narrative outside KnowledgeSnapshot | Breaks the self-sufficiency principle of KnowledgeSnapshot (ADR-022); replay would require a separate Narrative query |

## Consequences

### Positive

- Every narrative statement is auditable without accessing LLM internals
- Structural determinism makes Narrative output testable (section existence, feature references are stable)
- Clear separation between NarrativeGenerator (communication) and CoachingEngine (action)
- Language independence enables multi-language platform extension without Narrative redesign
- Immutable Narrative inside KnowledgeSnapshot guarantees replay fidelity (ADR-022)

### Negative / Risks

- ProfileFeature coverage determines narrative coverage — thin ProfileFeature data produces thin narratives
- LLM prose quality for a given ProfileFeature depends on prompt design (implementation concern; not an architectural risk)
- Confidence threshold tuning (which ProfileFeatures are narratable) requires calibration during EPIC-03 implementation

## Implementation Evidence

Architecture only. No production files modified.
Relevant existing assets (unchanged):
- `domain/profile/candidate_profile.py` (unchanged — NarrativeGenerator input)
- `domain/contracts/reasoning/evidence_signal.py` (frozen — NarrativeGenerator does not read this)
- All V1.1 evaluation pipeline files (unchanged)

## Review Trigger

- When a second NarrativeSectionType is added that does not fit the current taxonomy
- When confidence threshold calibration requires architectural changes to the traceability model
- When multi-language prose generation requires a LanguagePolicy injection model into NarrativeGenerator
- When LLM provider changes require structural changes to the prose generation interface
