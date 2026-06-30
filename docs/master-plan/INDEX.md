# Master Plan Index — AI Interview Simulator V1.1 / V1.2

**Status:** V1.1 M1 FROZEN (2026-06-30). TDS §9 and ADR-019 revised. ADR-024–027 added.

| Document | File | Scope |
|---|---|---|
| Product Requirements Document | `PRD-V1.1-V1.2.md` | Vision, epics, prioritization, release plan |
| Technical Design Specification | `TDS-V1.1-V1.2.md` | Architecture, components, security, migration, implementation roadmap |
| Architecture Review M1-1 | `ARCH-REVIEW-M1-1-FOLLOW-UP-ENGINE.md` | Design history (superseded — see TDS §9 revised) |
| M1-3 Acceptance Criteria | `M1-3-ACCEPTANCE-CRITERIA-FOLLOW-UP.md` | Follow-up engine acceptance gates (44/44 PASS) |
| M1-4 Test Specification | `M1-4-TEST-SPECIFICATION-FOLLOW-UP.md` | Follow-up engine test plan (186 tests implemented) |

## Usage Rules

1. **Implementation:** every V1.1 and V1.2 task must reference the corresponding Epic and Milestone from this plan.
2. **Architectural deviations:** require an ADR (continue numbering from ADR-027).
3. **New ADRs supersede** the relevant TDS section but must be registered here.
4. **PRD is the acceptance authority** — acceptance criteria in each Epic define done.
5. **TDS §9 (revised) is the canonical description** of the shipped follow-up engine.
6. **ARCH-REVIEW-M1-1 is design history only** — deviations from it are documented in ADR-019 revised and ADR-024–027.

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

## Active ADRs (V1.1 era)

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

## Document Versions

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-29 | AI Architect | Initial master plan |
| 1.1 | 2026-06-30 | Engineering | V1.1 M1 freeze: TDS §9 revised, ADR-019 revised, ADR-024–027 added, PRD EPIC-03 marked COMPLETED |
