# Master Plan Index — AI Interview Simulator V1.1 / V1.2

**Status:** V1.1.0 STABLE (2026-07-01) · **V1.2 Architecture Freeze COMPLETE (2026-07-02)** · **DOC-M1 Pattern Freeze COMPLETE (2026-07-02)** · **RC-C Methodology Freeze COMPLETE (2026-07-03)**. VERSION=1.1.0. 2802 tests passing. All P0/P1 findings resolved. Platform Engineering Manifest and Enterprise Engineering Playbook established. Stable Release Certificate issued (SR-1). V1.2 Architecture Certificate issued (AC-V1.2). Implementation Baseline frozen. DOC-M1 Pattern Freeze issued: PAT-01 to PAT-04 accepted. RC-C Methodology Freeze: PAT-05 and PAT-06 accepted; CAR, Pattern Extraction, Runtime Ownership, and Methodology Evolution formalised.

## V1.2 Architecture Freeze Summary

| Document | File | Status |
|---|---|---|
| **V1.2 Pattern Freeze** | **`V1.2-PATTERN-FREEZE.md`** | **FROZEN — DOC-M1 Pattern Documentation (2026-07-02)** |
| **V1.2 Architecture Certificate** | **`V1.2-ARCHITECTURE-CERTIFICATE.md`** | **CERTIFIED — AC-V1.2 (2026-07-02)** |
| **V1.2 Implementation Baseline** | **`V1.2-IMPLEMENTATION-BASELINE.md`** | **FROZEN — Implementation Baseline (2026-07-02)** |
| **V1.2 Implementation Roadmap** | **`V1.2-IMPLEMENTATION-ROADMAP.md`** | **FROZEN — Construction Phase Operational Guide (2026-07-02)** |
| V1.2 Domain Freeze | `V1.2-DOMAIN-FREEZE.md` | Frozen (K1 + K2 amendments) |
| V1.2 ADR Backlog Audit | `V1.2-ADR-BACKLOG-AUDIT.md` | Frozen (K2) |
| V1.2 Vision & Scope | `V1.2-VISION-SCOPE.md` | Frozen (K0) |

**Architecture Freeze Certificate:** AC-V1.2 — 16 core ADRs certified — 6 architectural layers — Overall maturity 9/10  
**Implementation Baseline:** Epic order frozen (EPIC-00 → EPIC-07) — Mandatory workflow frozen — Quality gates frozen  
**Ready for Implementation:** Phase 1 parallel tracks may begin.

---

## Foundational Documents

| Document | File | Scope |
|---|---|---|
| **Platform Engineering Manifest** | **`PLATFORM_ENGINEERING_MANIFEST.md`** | **FOUNDATIONAL — Engineering constitution for all versions ≥ V1.1. Defines principles, workflow, invariants, quality standards, release policy, and technical debt policy. Highest authority document in the repository.** |
| **Enterprise Engineering Playbook** | **`ENTERPRISE_ENGINEERING_PLAYBOOK.md`** | **FOUNDATIONAL — Operational handbook for day-to-day engineering execution. Defines project lifecycle, milestone workflow, prompt methodology, ADR workflow, architecture reviews, technical debt workflow, testing strategy, release workflow, and AI collaboration model. Complements the Manifest. Reusable across all future enterprise projects.** |

## Master Plan Documents


| Document | File | Scope |
|---|---|---|
| Product Requirements Document | `PRD-V1.1-V1.2.md` | Vision, epics, prioritization, release plan |
| Technical Design Specification | `TDS-V1.1-V1.2.md` | Architecture, components, security, migration, implementation roadmap |
| Architecture Review M1-1 | `ARCH-REVIEW-M1-1-FOLLOW-UP-ENGINE.md` | Design history (superseded — see TDS §9 revised) |
| M1-3 Acceptance Criteria | `M1-3-ACCEPTANCE-CRITERIA-FOLLOW-UP.md` | Follow-up engine acceptance gates (44/44 PASS) |
| M1-4 Test Specification | `M1-4-TEST-SPECIFICATION-FOLLOW-UP.md` | Follow-up engine test plan (186 tests implemented) |

## Usage Rules

1. **Implementation:** every V1.1 and V1.2 task must reference the corresponding Epic and Milestone from this plan.
2. **Architectural deviations:** require an ADR (continue numbering from ADR-068).
3. **New ADRs supersede** the relevant TDS section but must be registered here.
4. **PRD is the acceptance authority** — acceptance criteria in each Epic define done.
5. **TDS §9 (revised) is the canonical description** of the shipped follow-up engine.
6. **TDS §17 is the canonical description** of EPIC-04 Interview Reasoner frozen contracts.
7. **TDS §18 is the canonical description** of the Advanced Detector Architecture (M2-7A freeze).
8. **TDS §21 is the canonical description** of the M2-8 Reasoner Consolidation, API Freeze, EvaluationSignalWriter runtime flow, and same-cycle visibility contract.
9. **ARCH-REVIEW-M1-1 is design history only** — deviations documented in ADR-019 revised and ADR-024–027.
10. **Every new detector** must comply with the extensibility rules in TDS §18.5 and ADR-051.
11. **TDS §20 is the canonical specification** for LeadershipDetector, CollaborationDetector, and AdaptabilityDetector (M2-7F design freeze).
12. **Reasoner pipeline is frozen** — no new detectors, contracts, or API changes without a new ADR and milestone boundary.

## M1 Frozen Baseline Summary

| Component | Status | Location |
|---|---|---|
| `FollowUpSelector` | Frozen | `services/humanizer/selector/` |
| `FollowUpPromptBuilder` | Frozen | `services/humanizer/follow_up/` |
| `follow_up_generation.txt` | Frozen | `app/prompts/humanizer/` |
| `FollowUpParser` (STRICT) | Frozen | `services/humanizer/follow_up/` |
| `FollowUpGuard` (17 rules) | Frozen | `services/humanizer/guards/` |
| `HumanizerService.generate_follow_up()` | Frozen | `services/humanizer/humanizer_service.py` |
| `QuestionNode` V1.1 integration | Frozen | `app/graph/nodes/question_node.py` |
| `FollowUpTriggeredEvent` / `FollowUpSkippedEvent` | Frozen | `domain/events/` |
| `settings.py` follow-up configuration | Frozen | `infrastructure/config/settings.py` |

## M2-8 API Freeze Summary (Reasoner Consolidation)

| Component | Public API | Status |
|---|---|---|
| `ReasonerService` | `reason(ReasonerInput) → (ReasonerDecision, ReasoningTrace)` | **Frozen** |
| `ReasoningContextBuilder` | `build(InterviewState) → ReasonerInput` | **Frozen** |
| `PatternDetector` (ABC) | `metadata → DetectorMetadata`, `detect(ReasonerInput) → DetectorResult` | **Frozen** |
| `PatternDetectorRegistry` | `register`, `unregister`, `enabled`, `ordered`, `by_name`, `exists`, `all` | **Frozen** |
| `CandidateProfileEngine` | `update(profile, signals, q_idx) → CandidateProfile`, `dominant_dimension(profile)` | **Frozen** |
| `EvaluationSignalWriter` | `write_evaluation_signals(evaluation, q_idx, area, store) → EvidenceStore` | **Frozen** |
| `reasoner_node` | `reasoner_node(InterviewState) → InterviewState` | **Frozen** |
| `ReasonerDecision` | All fields frozen, `schema_version="1.0"` | **Frozen** |
| `ReasonerInput` | All fields frozen, `extra=forbid` | **Frozen** |
| `InterviewMemory` | 5-substructure composition, `extra=forbid` | **Frozen** |
| `CandidateProfile` | `dimension_scores`, `signals` (reserved), `questions_answered`, `areas_covered`, `last_updated_at_question_index` | **Frozen** |
| `EvidenceSignal` | All fields frozen, `schema_version="1.0"` | **Frozen** |
| `PatternMatch` / `PatternDetectionResult` | All fields frozen | **Frozen** |
| `ReasoningTrace` / `ReasoningTraceStep` | All fields frozen, INTERNAL ONLY | **Frozen** |
| `DetectorResult` | All fields frozen, execution_time_ms populated by pipeline | **Frozen** |

## M2-8 EvaluationSignalWriter — Runtime Flow

```
reasoner_node
  → _inject_evaluation_signals(state)
      → write_evaluation_signals(evaluation, q_idx, area, store)
          → idempotency guard (source=EVALUATION, q_idx already written? → skip)
          → _build_signals: score → EvidenceType mapping
              score ≥ 80  → [] (no signal)
              50 ≤ score < 80  → SHALLOW_ANSWER
              30 ≤ score < 50  → REASONING_GAP
              score < 30  → KNOWLEDGE_GAP
          → store.append(signal) × N
      → returns updated EvidenceStore (never mutates original)
  → state updated with new evidence_store in interview_memory
  → ReasoningContextBuilder.build(state) → ReasonerInput
  → ReasonerService.reason(ReasonerInput)
      → EvaluationSignalDetector reads store (same-cycle visibility guaranteed)
```

**Same-cycle visibility contract (ADR-046, ADR-052):**  
Signals written by `EvaluationSignalWriter` in `_inject_evaluation_signals` ARE visible to detectors in the same cycle, because they are written to `EvidenceStore` before `ReasonerService.reason()` is called. Signals generated by detectors within the same cycle are NOT visible to subsequent detectors in the same cycle (isolated pipeline — ADR-046).



| Contract | Location | Status |
|---|---|---|
| `domain/contracts/reasoning/` (27 files) | See TDS §17.1 | **Frozen** |
| `InterviewMemory` (5-substructure composition) | `domain/contracts/reasoning/interview_memory.py` | **Frozen** |
| `EvidenceSignal` (with id, polarity, type, source, strength, schema_version) | `domain/contracts/reasoning/evidence_signal.py` | **Frozen** |
| `CandidateProfile` (DimensionTrace without raw scores) | `domain/contracts/reasoning/candidate_profile.py` | **Frozen** |
| `ReasonerInput` (single immutable input DTO) | `domain/contracts/reasoning/reasoner_input.py` | **Frozen** |
| `ReasonerDecision` (fully structured, no free text) | `domain/contracts/reasoning/reasoner_decision.py` | **Frozen** |
| `PatternDetectorRegistry` + pipeline | `services/interview_reasoner/pattern_detection/` | **Frozen (architecture)** |
| `CandidateProfileEngine` + updaters | `services/interview_reasoner/profile/` | **Frozen (M2-6C)** |
| `ENGINEERING_JUDGMENT` ProfileDimension | `domain/contracts/reasoning/profile_dimension.py` | **Frozen** |
| `EvidenceSource.DERIVED` | Reserved for V1.2 | **Reserved** |
| Evidence freshness weighting | Reserved for V1.2 | **Reserved (ADR-039)** |
| `ProfileFeature` abstraction | Reserved for V1.2 | **Reserved (ADR-048)** |
| `EvaluationSignalWriter` | `services/interview_reasoner/evaluation_signal_writer.py` | **Frozen (M2-8)** |
| `EvaluationBridgeDetector` | `services/interview_reasoner/pattern_detection/detectors/evaluation_bridge_detector.py` | **Deprecated M2-7B / Remove V1.2** |
| `LeadershipDetector` full specification | TDS §20.2 | **Design Frozen (M2-7F)** |
| `CollaborationDetector` full specification | TDS §20.3 | **Design Frozen (M2-7F)** |
| `AdaptabilityDetector` full specification | TDS §20.4 | **Design Frozen (M2-7F)** |
| Behavioral family responsibility matrix | TDS §20.5 | **Design Frozen (M2-7F)** |
| `LeadershipObservation` / `CollaborationObservation` / `AdaptabilityObservation` | TDS §20.6 | **Reserved V1.2** |
| `LeadershipFeature` / `CollaborationFeature` / `AdaptabilityFeature` | TDS §20.7 | **Reserved V1.2** |
| `CoachingEngine` pipeline architecture | TDS §20.8 | **Reserved V1.2** |
| EvidenceType catalog (35 total post-M2-7F) | TDS §20.5.5 | **Design Frozen** |

## M2-7A Detector Catalog (Frozen Execution Order)

| Priority | Detector | Milestone | Status |
|---|---|---|---|
| 5 | `EvaluationSignalDetector` | M2-7B | **Active** |
| 10 | `CoverageDetector` | M2-3 | **Active** |
| 20 | `ConsistencyDetector` | M2-3 | **Active** |
| 30 | `TrendDetector` | M2-3 | **Active** |
| 40 | `ReasoningDepthDetector` | M2-7B | **Active** |
| 50 | `EngineeringJudgmentDetector` | M2-7C | **Active** |
| 60 | `CommunicationDetector` | M2-7D | **Active** |
| 70 | `BehavioralPatternDetector` | M2-7E | **Active** |
| 80 | `ConsistencyAcrossInterviewDetector` | M2-7F | **Active** |
| 90 | `ConfidenceCalibrationDetector` | M2-7G/K | **Active** |
| 100 | `LeadershipDetector` | M2-7H | **Active** |
| 110 | `CollaborationDetector` | M2-7I | **Active** |
| 120 | `AdaptabilityDetector` | M2-7J | **Active** |
| — | `EvaluationBridgeDetector` | M2-6A (superseded) | **Deprecated — not in registry** |

## Active ADRs

| ADR | Title | Status |
|---|---|---|
| ADR-016 | Observation Schema & ObservationExtractor Design | **Accepted — V1.2 Architecture Freeze** |
| ADR-016A | CandidateIdentity & Session Ownership | **Accepted — V1.2 Architecture Freeze** |
| ADR-017 | ObservationStore Lifecycle & Temporal Semantics | **Accepted — V1.2 Architecture Freeze** |
| ADR-018 | ProfileFeature Schema Freeze & Versioning Policy | **Accepted — V1.2 Architecture Freeze** |
| ADR-019 | Language Independence Layer & LanguageConfig Architecture | **Accepted — V1.2 Architecture Freeze** |
| ADR-020 | FeatureEngine Architecture — Knowledge Construction Engine | **Accepted — V1.2 Architecture Freeze** |
| ADR-021 | Knowledge Freshness, Temporal Decay & Replay Strategy | **Accepted — V1.2 Architecture Freeze** |
| ADR-022 | Knowledge Persistence & SessionHistory Architecture | **Accepted — V1.2 Architecture Freeze** |
| ADR-023 | NarrativeGenerator Profile-Feature-Aware Prompt Design | **Accepted — V1.2 Architecture Freeze** |
| ADR-024 | Calibration Framework CI Gate Design | Pending — Support ADR (non-blocking) |
| ADR-025 | CoachingEngine Ranking Algorithm | **Accepted — V1.2 Architecture Freeze** |
| ADR-026 | Replay Snapshot Model | **Accepted — V1.2 Architecture Freeze** |
| ADR-027 | LanguageExecutor Abstraction — Runtime Dispatch Interface | **Accepted — V1.2 Architecture Freeze** |
| ADR-028 | Language Selection Policy — Session Config Rules | **Accepted — V1.2 Architecture Freeze** |
| ADR-029 | Enterprise Extensibility — TenantContext Placeholder Design | Pending — Support ADR (non-blocking) |
| ADR-030 | StudyRecommendation Resource Library Governance | **Accepted — V1.2 Architecture Freeze** |
| ADR-031 | LanguagePolicy Governance — Change Control & Calibration Impact | **Accepted — V1.2 Architecture Freeze** |
| ADR-032 | CandidateProfileSnapshot Strategy | **Accepted — V1.2 Architecture Freeze** |
| ADR-033 | EvidenceSignal as Universal Signal Abstraction | **Accepted — M2** |
| ADR-034 | PatternDetector Decomposed into Registry-Backed Pipeline | **Accepted — M2** |
| ADR-035 | ReasonerDecision Is Fully Structured — No Free Text | **Accepted — M2** |
| ADR-036 | Two-Tier Confidence Model (ReasoningConfidence) | **Accepted — M2** |
| ADR-037 | CandidateProfile Inside InterviewMemory, No Raw Score Duplication | **Accepted — M2** |
| ADR-038 | InterviewMemory Internal Composition (5 substructures) | **Accepted — M2** |
| ADR-039 | Evidence Freshness — Architectural Reservation (V1.2) | **Accepted — Deferred** |
| ADR-040 | ProfileDimension: ENGINEERING_JUDGMENT | **Accepted — M2** |
| ADR-041 | Reasoner Explainability — Internal Audit Trail (ReasoningTrace) | **Accepted — Architecture; impl deferred** |
| ADR-042 | CandidateProfile Internal Composition — Future Sub-profiles | **Accepted — Arch direction; V1.2** |
| ADR-043 | ReasonerDecision Composition — Future Composed Decisions | **Accepted — Arch direction; V1.2** |
| ADR-044 | Recommendation Hierarchy — Future Base Protocol | **Accepted — Arch direction; V1.2** |
| ADR-045 | PatternDetector Metadata Model — Registry Introspection | **Accepted — Arch direction; M2-2** |
| ADR-046 | EvidenceStore Responsibility Contract | **Accepted — Partially M2-1; extend M2-2** |
| ADR-047 | ReasoningTrace Audit Hashes — input_hash/output_hash | **Accepted — Arch direction; V1.2** |
| ADR-048 | ProfileFeature Abstraction — V1.2 Extension Point | **Accepted — Arch direction; V1.2** |
| ADR-049 | Advanced Detector Layering (4 tiers, frozen priority ranges) | **Accepted — M2-7A** |
| ADR-050 | NarrativeGenerator Consumes ProfileFeatures, Not Detector Outputs | **Accepted — Arch direction; M2-8** |
| ADR-051 | Detector Extensibility Contract (Plugin Architecture) | **Accepted — M2-7A** |
| ADR-052 | Evidence Freshness Sliding Window (EvaluationSignalDetector) | **Accepted — M2-7B** |
| ADR-053 | Detector Compatibility Policy | **Accepted — M2-7A** |
| ADR-054 | Detector Performance Budget | **Accepted — M2-7A** |
| ADR-055 | Observation Abstraction — Reserved for V1.2 | **Proposed — M2-7C** |
| ADR-056 | Detector File Size Limits | **Accepted — M2-7E** |
| ADR-057 | Detector Dependency Direction Enforcement | **Accepted — M2-7E** |
| ADR-058 | Detector Versioning and Compatibility | **Accepted — M2-7E** |
| ADR-059 | Detector Deprecation Policy | **Accepted — M2-7E** |
| ADR-060 | Detector Test Coverage Standard | **Accepted — M2-7E** |
| ADR-061 | Detector Framework Stability Guarantee | **Accepted — M2-7E** |
| ADR-062 | Behavioral Detector Family — Responsibility Matrix | **Accepted — M2-7F** |
| ADR-063 | LeadershipFeature — Dimension Anchor and Update Strategy | **Accepted — M2-7F** |
| ADR-064 | CollaborationFeature — Dimension Anchor | **Accepted — M2-7F** |
| ADR-065 | AdaptabilityDetector — Recovery Detection Algorithm | **Accepted — M2-7F** |
| ADR-066 | Behavioral Observation Model — V1.2 Extension Contract | **Accepted — Arch direction; V1.2** |
| ADR-067 | Behavioral Coaching Pipeline — Detector-to-CoachingEngine Decoupling | **Accepted — Arch direction; V1.2** |

## Engineering Pattern Registry

| ID | Name | Document | Status |
|---|---|---|---|
| PAT-01 | Engine Five-Artifact Pattern | `V1.2-PATTERN-FREEZE.md` | **Accepted — DOC-M1 (2026-07-02)** |
| PAT-02 | Runtime First, Orchestration Second | `V1.2-PATTERN-FREEZE.md` | **Accepted — DOC-M1 (2026-07-02)** |
| PAT-03 | Construction Parallelism Review (CPR) | `V1.2-PATTERN-FREEZE.md` | **Accepted — DOC-M1 (2026-07-02)** |
| PAT-04 | Temporary Construction Placeholder (TCP) | `V1.2-PATTERN-FREEZE.md` | **Accepted — DOC-M1 (2026-07-02)** |
| PAT-05 | Builder-only Construction | `V1.2-PATTERN-FREEZE.md` | **Accepted — RC-C (2026-07-03)** |
| PAT-06 | Single Runtime Orchestrator | `V1.2-PATTERN-FREEZE.md` | **Accepted — RC-C (2026-07-03)** |

**Pattern Freeze Authority:** Platform Engineering Manifest v1.2 §Engineering Pattern Registry  
**Operational Guidance:** Enterprise Engineering Playbook v1.2 §Section N  
**Implementation Reference:** V1.2-IMPLEMENTATION-BASELINE §B8  
**CAR Authority:** Enterprise Engineering Playbook v1.2 §Section O; V1.2-PATTERN-FREEZE.md §Construction Architecture Review

## Official Patterns (ARC-01)

| ID | Name | Document | Status |
|---|---|---|---|
| OP-01 | Cascading Closure | `ARC-01-ARCHITECTURE-CONSTITUTION.md` §5; `ARCHITECTURE-GUIDE.md` §8 | **Official — ARC-01** |
| OP-02 | Projection Artifact | `ARC-01-ARCHITECTURE-CONSTITUTION.md` §5; `ARCHITECTURE-GUIDE.md` §8 | **Official — ARC-01** |
| OP-03 | Runtime First / Projection Later | `ARC-01-ARCHITECTURE-CONSTITUTION.md` §5; `ARCHITECTURE-GUIDE.md` §8 | **Official — ARC-01** |
| OP-04 | Sole Writer Node | `ARC-01-ARCHITECTURE-CONSTITUTION.md` §5; `ARCHITECTURE-GUIDE.md` §8 | **Official — ARC-01** |
| OP-05 | Single Builder | `ARC-01-ARCHITECTURE-CONSTITUTION.md` §5; `ARCHITECTURE-GUIDE.md` §8 | **Official — ARC-01** |
| OP-06 | Immutable Accumulation | `ARC-01-ARCHITECTURE-CONSTITUTION.md` §5; `ARCHITECTURE-GUIDE.md` §8 | **Official — ARC-01** |

**Constitutional principle (not a PAT):** [P-08 — Reconstruction Completeness](ARC-01-ARCHITECTURE-CONSTITUTION.md#p-08--reconstruction-completeness) — remains ARC-01 principle; not registered as PAT-07.

**Namespace rule (EPIC-V13-10 / AR-01):** PAT-01…06 (Engineering Pattern Registry) and OP-01…06 (Official Patterns) are **distinct namespaces**. Do **not** renumber OPs as PAT-07+. Numeric ID collision is managed by namespace labels.

**Master Plan wording note (AR-01 / REG-05):** “five new PATs” = **OP-01…04 + P-08**. The six original PATs remain PAT-01…06. P-08 wording in the Master Plan is a historical synonym for the constitutional principle, not a Pattern Freeze PAT.

---

## Document Versions

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-29 | AI Architect | Initial master plan |
| 1.1 | 2026-06-30 | Engineering | V1.1 M1 freeze: TDS §9 revised, ADR-019 revised, ADR-024–027 added, PRD EPIC-03 marked COMPLETED |
| 1.2 | 2026-06-30 | Engineering | V1.1 M2 contract freeze: TDS §17 added, ADR-028–040 registered, EPIC-04 contracts frozen |
| 1.3 | 2026-06-30 | Engineering | M2-1A freeze: ADR-042–047 added (future-proofing direction) |
| 1.4 | 2026-07-01 | Engineering | M2-7A architecture freeze: TDS §18 added, ADR-048–054 registered, detector catalog and ProfileFeature abstraction frozen |
| 1.5 | 2026-07-01 | Engineering | M2-7F design freeze: TDS §20 added, ADR-062–067 registered, Leadership/Collaboration/Adaptability detectors and Behavioral family fully frozen |
| 1.6 | 2026-07-01 | Engineering | M2-8 Reasoner Consolidation: INDEX updated, API Freeze table added, EvaluationSignalWriter flow documented, detector catalog corrected to Active, EvaluationBridgeDetector deprecated, TDS §21 added, Technical Debt Register added |
| 1.7 | 2026-07-01 | Engineering | EP-1 Foundational documentation: ENTERPRISE_ENGINEERING_PLAYBOOK.md created and registered as second FOUNDATIONAL DOCUMENT |
| 1.8 | 2026-07-01 | Engineering | SR-1 Stable Release: INDEX status promoted to V1.1.0 STABLE, Stable Release Certificate issued, V1.2 transition confirmed |
| 1.9 | 2026-07-02 | Engineering | AC-V1.2 Architecture Freeze: V1.2 Architecture Certificate and Implementation Baseline created; 16 V1.2 core ADRs certified; Architecture Freeze Summary added; STATUS promoted to V1.2 Architecture Freeze COMPLETE |
| 2.0 | 2026-07-02 | Engineering | V1.2 Construction Phase: V1.2-IMPLEMENTATION-ROADMAP.md created; Construction Phase operational guide registered; Construction Readiness Assessment: GO |
| 2.1 | 2026-07-02 | Engineering | DOC-M1 Pattern Freeze: V1.2-PATTERN-FREEZE.md created; PAT-01 to PAT-04 registered; Pattern Registry section added; Manifest v1.1 and Playbook v1.1 updated |
| 2.2 | 2026-07-03 | Engineering | RC-C Methodology Freeze: PAT-05 and PAT-06 registered; CAR, Pattern Extraction, Runtime Ownership, Methodology Evolution formalised; Manifest v1.2 and Playbook v1.2 updated; Implementation Baseline v1.2 updated; STATUS promoted to RC-C COMPLETE |
| 2.3 | 2026-07-21 | Engineering | EPIC-V13-10 P1: Official Patterns (ARC-01) section — OP-01…06 + P-08 cross-link; dual PAT/OP namespace note; Master Plan “five new PATs” = OP-01…04 + P-08 |

## Technical Debt Register (M2-8)

### V1.1 Closed

| ID | Item | Resolution |
|---|---|---|
| TD-001 | EvaluationSignalWriter missing (P0-1 from M2-7M audit) | Shipped in M2-8; `evaluation_signal_writer.py` |
| TD-002 | `questions_answered` counter not incremented per cycle (P0-2) | Fixed in `ReasonerService._propagate_evidence()` |
| TD-003 | `EvaluationBridgeDetector` superseded but still present in codebase | Deprecated; removed from registry; file retained for V1.2 removal window |
| TD-004 | `domain/contracts/reasoning/` count mismatch in INDEX (stated 19, actual 27) | Corrected in INDEX v1.6 |
| TD-005 | Detector catalog in INDEX showed all detectors as "Planned" | Corrected to Active in INDEX v1.6 |

### V1.1 Deferred

| ID | Item | Priority | Reason | Planned Milestone | ADR |
|---|---|---|---|---|---|
| TD-006 | `EvaluationBridgeDetector` file deletion | P3 | Retained one-milestone per ADR-059 deprecation policy | V1.2 | ADR-059 |
| TD-007 | `InterviewMemoryContext` full removal | P2 | Deprecated M2; safe to remove once all consumers verified | M3 | ADR-032 |
| TD-008 | `ReasoningTrace` not attached to `ReasonerDecision` output (ADR-041 arch-only) | P3 | Internal audit only; no external consumer yet | V1.2 | ADR-041 |
| TD-009 | `ReasoningTrace` audit hashes (`input_hash`/`output_hash`) not implemented | P3 | ADR-047 arch direction | V1.2 | ADR-047 |
| TD-010 | `DetectorPipeline` abstraction (composable pipeline object) | P3 | ADR deferred; depends on NarrativeGenerator requirements | V1.2 | TDS §19.9.4 |
| TD-011 | `CandidateProfile.signals` field never populated | P3 | Reserved for ProfileFeature layer (ADR-048) | V1.2 | ADR-048 |
| TD-012 | `EvidenceSource.DERIVED` never used | P3 | Reserved for V1.2 | V1.2 | ADR-039 |
| TD-013 | `_session_trend` only reads `reasoning_confidence` (not domain signals) | P3 | Sufficient for V1.1; signal-based trend is V1.2 scope | V1.2 | — |

### V1.2 Planned

| ID | Item | Priority | ADR |
|---|---|---|---|
| TD-014 | `ProfileFeature` abstraction activation | P1 | ADR-048 |
| TD-015 | Evidence freshness weighting (sliding window) | P2 | ADR-039 |
| TD-016 | `CoachingEngine` pipeline | P1 | ADR-067 |
| TD-017 | `NarrativeGenerator` (M2-8 deferred) | P1 | ADR-050 |
| TD-018 | `ObservationModel` (Leadership/Collaboration/Adaptability) | P2 | ADR-055, ADR-066 |

---

## V1.1.0 Stable Release Certificate

**Certificate ID:** SR-1  
**Version:** 1.1.0  
**Date:** 2026-07-01  
**Status:** CERTIFIED STABLE

### Architecture

| Item | Status |
|---|---|
| DDD layered architecture | Frozen |
| 16-node LangGraph interview graph | Frozen |
| InterviewMemory 5-substructure composition | Frozen |
| PatternDetectorRegistry plugin architecture | Frozen |
| All M1 and M2 public APIs | Frozen (extra=forbid, schema_version="1.0") |
| 67 Architecture Decision Records | Accepted |

### Tests

| Metric | Value |
|---|---|
| Total tests | 2,802 |
| Passed | 2,802 |
| Failed | 0 |
| Skipped | 0 |
| Test modules | 280 |

### Documentation

| Document | Status |
|---|---|
| Platform Engineering Manifest | Current (v1.0) |
| Enterprise Engineering Playbook | Current (v1.0) |
| PRD-V1.1-V1.2.md | Current |
| TDS-V1.1-V1.2.md (§9, §17, §18, §20, §21) | Current |
| INDEX.md | Current (v1.8) |
| README.md | Current — Stable status |
| CHANGELOG.md | Current — [1.1.0] entry added |
| Technical Debt Register | Current — 18 items registered |

### Quantitative Summary

| Metric | Value |
|---|---|
| ADR count | 67 |
| Active detectors | 13 |
| EvidenceType catalog entries | 35 |
| Frozen contracts (domain/contracts/) | 27 files |
| Deferred technical debt items | 13 (V1.1 deferred + V1.2 planned) |
| Forbidden technical debt items | 0 |

### Certification Verdict

All Forbidden technical debt: **ZERO**  
All P0/P1 audit findings: **RESOLVED**  
Full test suite: **2,802 PASSED / 0 FAILED**  
Documentation freeze: **COMPLETE**  
API freeze: **COMPLETE**

**RECOMMENDATION: CERTIFIED FOR V1.1.0 STABLE RELEASE**

---

## V1.2 Transition Summary

### Protected Assets (Must Not Be Modified Without ADR)

- All contracts in `domain/contracts/reasoning/` (27 files, extra=forbid, schema_version="1.0")
- `ReasonerService`, `ReasoningContextBuilder`, `PatternDetectorRegistry`, `CandidateProfileEngine`, `EvaluationSignalWriter` public APIs
- All 13 active detector implementations and their frozen execution priorities
- `InterviewMemory` 5-substructure composition
- `FollowUpSelector`, `FollowUpGuard`, `FollowUpPromptBuilder`, `FollowUpParser` (M1 frozen)
- ADR-001 through ADR-067 (supersession requires new ADR, not modification)

### Available Extension Points for V1.2

| Extension Point | Governing ADR | Description |
|---|---|---|
| `ProfileFeature` abstraction | ADR-048 | Structured feature layer above raw detector outputs |
| `NarrativeGenerator` consuming ProfileFeatures | ADR-050 | Narrative coaching from features, not raw signals |
| `CoachingEngine` pipeline | ADR-067 | Decoupled coaching recommendation pipeline |
| Evidence freshness weighting | ADR-039 | Sliding window on EvidenceStore signals |
| `ObservationModel` (Leadership/Collaboration/Adaptability) | ADR-055, ADR-066 | Structured behavioral observations |
| `EvidenceSource.DERIVED` | ADR-039 | Reserved evidence source variant |
| `ReasoningTrace` audit hashes | ADR-047 | input_hash/output_hash for audit trail |
| `DetectorPipeline` abstraction | TDS §19.9.4 | Composable pipeline object |
| `CandidateProfile.signals` field | ADR-048 | ProfileFeature population target |

### Next ADR Numbering

V1.2 ADRs start from **ADR-068**.

### First Planned V1.2 Milestones

| Milestone | Scope | Governing ADRs |
|---|---|---|
| V1.2 M1 | ProfileFeature abstraction activation | ADR-048 |
| V1.2 M2 | NarrativeGenerator (ProfileFeature-consuming) | ADR-050 |
| V1.2 M3 | CoachingEngine pipeline | ADR-067 |
| V1.2 M4 | Behavioral ObservationModel | ADR-055, ADR-066 |
| V1.2 M5 | Evidence freshness weighting | ADR-039 |
| V1.2 M6 | EvaluationBridgeDetector removal | ADR-059, TD-006 |
| V1.2 M7 | Domain layer cleanup (InterviewMemoryContext removal) | ADR-032, TD-007 |
