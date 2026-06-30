# Master Plan Index — AI Interview Simulator V1.1 / V1.2

**Status:** V1.1 M2 Contract Freeze (2026-06-30). ADR-028–040 added. EPIC-04 contracts frozen.

| Document | File | Scope |
|---|---|---|
| Product Requirements Document | `PRD-V1.1-V1.2.md` | Vision, epics, prioritization, release plan |
| Technical Design Specification | `TDS-V1.1-V1.2.md` | Architecture, components, security, migration, implementation roadmap |
| Architecture Review M1-1 | `ARCH-REVIEW-M1-1-FOLLOW-UP-ENGINE.md` | Design history (superseded — see TDS §9 revised) |
| M1-3 Acceptance Criteria | `M1-3-ACCEPTANCE-CRITERIA-FOLLOW-UP.md` | Follow-up engine acceptance gates (44/44 PASS) |
| M1-4 Test Specification | `M1-4-TEST-SPECIFICATION-FOLLOW-UP.md` | Follow-up engine test plan (186 tests implemented) |

## Usage Rules

1. **Implementation:** every V1.1 and V1.2 task must reference the corresponding Epic and Milestone from this plan.
2. **Architectural deviations:** require an ADR (continue numbering from ADR-040).
3. **New ADRs supersede** the relevant TDS section but must be registered here.
4. **PRD is the acceptance authority** — acceptance criteria in each Epic define done.
5. **TDS §9 (revised) is the canonical description** of the shipped follow-up engine.
6. **TDS §17 is the canonical description** of EPIC-04 Interview Reasoner frozen contracts.
7. **ARCH-REVIEW-M1-1 is design history only** — deviations documented in ADR-019 revised and ADR-024–027.

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
| `ENGINEERING_JUDGMENT` ProfileDimension | `domain/contracts/reasoning/profile_dimension.py` | **Frozen** |
| `EvidenceSource.DERIVED` | Reserved for V1.2 | **Reserved** |
| Evidence freshness weighting | Reserved for V1.2 | **Reserved (ADR-039)** |
| `InterviewMemoryContext` deprecation | `domain/contracts/interview/interview_memory_context.py` | **Deprecated M2 / Remove M3** |

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

## Document Versions

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-29 | AI Architect | Initial master plan |
| 1.1 | 2026-06-30 | Engineering | V1.1 M1 freeze: TDS §9 revised, ADR-019 revised, ADR-024–027 added, PRD EPIC-03 marked COMPLETED |
| 1.2 | 2026-06-30 | Engineering | V1.1 M2 contract freeze: TDS §17 added, ADR-028–040 registered, EPIC-04 contracts frozen |
