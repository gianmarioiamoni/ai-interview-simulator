# Master Plan Index — AI Interview Simulator V1.1 / V1.2

**Status:** V1.1 M2-7A Architecture Freeze (2026-07-01). ADR-048–054 added. Detector catalog and implementation roadmap frozen.

| Document | File | Scope |
|---|---|---|
| Product Requirements Document | `PRD-V1.1-V1.2.md` | Vision, epics, prioritization, release plan |
| Technical Design Specification | `TDS-V1.1-V1.2.md` | Architecture, components, security, migration, implementation roadmap |
| Architecture Review M1-1 | `ARCH-REVIEW-M1-1-FOLLOW-UP-ENGINE.md` | Design history (superseded — see TDS §9 revised) |
| M1-3 Acceptance Criteria | `M1-3-ACCEPTANCE-CRITERIA-FOLLOW-UP.md` | Follow-up engine acceptance gates (44/44 PASS) |
| M1-4 Test Specification | `M1-4-TEST-SPECIFICATION-FOLLOW-UP.md` | Follow-up engine test plan (186 tests implemented) |

## Usage Rules

1. **Implementation:** every V1.1 and V1.2 task must reference the corresponding Epic and Milestone from this plan.
2. **Architectural deviations:** require an ADR (continue numbering from ADR-054).
3. **New ADRs supersede** the relevant TDS section but must be registered here.
4. **PRD is the acceptance authority** — acceptance criteria in each Epic define done.
5. **TDS §9 (revised) is the canonical description** of the shipped follow-up engine.
6. **TDS §17 is the canonical description** of EPIC-04 Interview Reasoner frozen contracts.
7. **TDS §18 is the canonical description** of the Advanced Detector Architecture (M2-7A freeze).
8. **ARCH-REVIEW-M1-1 is design history only** — deviations documented in ADR-019 revised and ADR-024–027.
9. **Every new detector** must comply with the extensibility rules in TDS §18.5 and ADR-051.

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

## M2 Contract Freeze Summary (EPIC-04)

| Contract | Location | Status |
|---|---|---|
| `domain/contracts/reasoning/` (19 files) | See TDS §17.1 | **Frozen** |
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
| `InterviewMemoryContext` deprecation | `domain/contracts/interview/interview_memory_context.py` | **Deprecated M2 / Remove M3** |

## M2-7A Detector Catalog (Frozen Execution Order)

| Priority | Detector | Milestone | Status |
|---|---|---|---|
| 5 | `EvaluationBridgeDetector` → `EvaluationSignalDetector` | Active / M2-7B | Active (will be replaced in M2-7B) |
| 10 | `CoverageDetector` | M2-3 | **Active** |
| 20 | `ConsistencyDetector` | M2-3 | **Active** |
| 30 | `TrendDetector` | M2-3 | **Active** |
| 40 | `ReasoningDepthDetector` | M2-7B | Planned |
| 50 | `EngineeringJudgmentDetector` | M2-7C | Planned |
| 60 | `CommunicationDetector` | M2-7D | Planned |
| 70 | `BehavioralPatternDetector` | M2-7E | Planned |
| 80 | `ConsistencyAcrossInterviewDetector` | M2-7F | Planned |
| 90 | `ConfidenceCalibrationDetector` | M2-7G | Planned |
| 100 | `LeadershipDetector` | V1.2 | Reserved |
| 110 | `CollaborationDetector` | V1.2 | Reserved |
| 120 | `AdaptabilityDetector` | V1.2 | Reserved |

## Active ADRs

| ADR | Title | Status |
|---|---|---|
| ADR-016 | Multi-language Coding Engine Strategy | Planned |
| ADR-017 | Prompt Security Layer Architecture | Planned |
| ADR-018 | Output Validation Layer Position | Planned |
| ADR-019 | Follow-up Question Engine Design (Revised) | **Accepted** |
| ADR-020 | Knowledge Gap Engine Classification | Planned |
| ADR-021 | Cost Optimization and Model Routing | Planned |
| ADR-022 | Progress Tracking Persistence Backend | Planned |
| ADR-023 | Replay Engine Storage Format | Planned |
| ADR-024 | Score Gating Deferred from V1.1 | **Accepted** |
| ADR-025 | Guard Retry Deferred to V1.2 | **Accepted** |
| ADR-026 | Dedicated Follow-up Prompt File | **Accepted** |
| ADR-027 | FollowUpSelector Determinism | **Accepted** |
| ADR-028 | Interview Reasoner Is Deterministic (No LLM) | **Accepted — M2** |
| ADR-029 | Reasoner Node Position: After Feedback, Before Decision | **Accepted — M2** |
| ADR-030 | Reasoner Outputs Are Advisory Only | **Accepted — M2** |
| ADR-031 | ReasonerDecision Transient; ReasoningHistory Persistent | **Accepted — M2** |
| ADR-032 | InterviewMemory as Session-Scoped Accumulated Intelligence | **Accepted — M2** |
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

## Document Versions

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-29 | AI Architect | Initial master plan |
| 1.1 | 2026-06-30 | Engineering | V1.1 M1 freeze: TDS §9 revised, ADR-019 revised, ADR-024–027 added, PRD EPIC-03 marked COMPLETED |
| 1.2 | 2026-06-30 | Engineering | V1.1 M2 contract freeze: TDS §17 added, ADR-028–040 registered, EPIC-04 contracts frozen |
| 1.3 | 2026-06-30 | Engineering | M2-1A freeze: ADR-042–047 added (future-proofing direction) |
| 1.4 | 2026-07-01 | Engineering | M2-7A architecture freeze: TDS §18 added, ADR-048–054 registered, detector catalog and ProfileFeature abstraction frozen |
