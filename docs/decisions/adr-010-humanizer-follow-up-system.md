# ADR-010 — Humanizer Follow-Up System

**Status:** Accepted
**Date:** 2026-06-18
**Owner:** Services

---

## Context

Bare `question.prompt` delivery is robotic and does not reflect real interviewer behavior.
The Humanizer subsystem wraps structured questions in conversational framing,
acknowledges prior answers (REMARK_PLUS_QUESTION), and optionally probes high-quality
answers with follow-up questions (FOLLOW_UP). Without this, the interview feels like a form.

## Decision

- Humanizer is enabled by default (`HUMANIZER_ENABLED=True`, env-var configurable).
- Humanizer applies only to `WRITTEN` question types.
- Policy engine governs decision: `DIRECT_QUESTION` | `REMARK_PLUS_QUESTION` | `FOLLOW_UP`.
- Maximum 2 follow-ups per interview (`MAX_FOLLOW_UPS_PER_INTERVIEW` — single source of truth in `app/settings/constants.py`).
- Follow-up semantic model: **conversational only** (Model A). Follow-up does not create new `Question` objects, does not extend `planned_areas`, and is not independently evaluated. Model B (evaluated follow-up) is deferred post-V1.
- `FOLLOW_UP` branch is feature-flagged off by default (`HUMANIZER_FOLLOW_UP_ENABLED=False`) pending V1.1 timing and score-propagation fixes.
- `FOLLOW_UP_SCORE_THRESHOLD = 4` aligns with `Quality.OPTIMAL.rank()` (maximum achievable rank).

## Rationale

- Model A is a 1-day fix; Model B requires 20–50h of new pipeline work with regression risk.
- Conversational framing alone significantly improves realism — REMARK_PLUS_QUESTION and DIRECT_QUESTION paths are production-safe.
- **Timing defect:** resolved — `navigation_node` and `adaptive_navigation_node` clear `question_display_text` on every index-advancing NEXT; stale display eliminated.
- **Score propagation:** resolved — `question_node` reads `last_answer_score` from `last_feedback_bundle`; falls back to `last_question_context.quality_rank` when bundle is cleared. `LastQuestionContext` snapshot implemented.
- **FOLLOW_UP remains disabled** (`HUMANIZER_FOLLOW_UP_ENABLED=False`) by product/rollout decision, not technical limitation. Technical blockers are resolved. Activation deferred to V1.1 after integration testing with real LLM output.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Always generate follow-ups | Fairness risk; max cap required |
| User-configured follow-up count | Adds UI complexity with marginal value |
| Model B (evaluated follow-up) | 3–4x more effort; deferred to V1.2 |
| Disable humanizer entirely for V1 | LLM cost already incurred; zero candidate value |

## Consequences

### Positive
- Conversational realism without new evaluation pipeline
- FOLLOW_UP safely gated behind feature flag
- Single source of truth for max follow-up cap

### Negative / Risks
- Q1 shown as raw prompt on initial session start (question_node not invoked on start path)
- FOLLOW_UP requires `humanizer_follow_up_enabled=True` (default `False`)

## Implementation Evidence

- `infrastructure/config/settings.py` — `humanizer_enabled`, `humanizer_follow_up_enabled`
- `infrastructure/config/evaluation.py` — `FOLLOW_UP_SCORE_THRESHOLD = 4`
- `app/settings/constants.py` — `MAX_FOLLOW_UPS_PER_INTERVIEW = 2`
- `domain/contracts/interview_state/base.py` — `enable_humanizer`, `follow_up_count` (le= from constant), `question_display_text`, `last_question_context`
- `domain/contracts/interview_state/factory.py` — `enable_humanizer` param in `create_initial`
- `domain/contracts/interview_state/last_question_context.py` — prior-question snapshot
- `services/humanizer/humanizer_policy_engine.py` — `follow_up_enabled` constructor param
- `services/humanizer/humanizer_service.py` — returns `(policy_decision, output)` tuple
- `app/graph/nodes/question_node.py` — sets `question_display_text` on all paths
- `app/graph/nodes/navigation_node.py` — captures `last_question_context` snapshot before index advance
- `app/graph/nodes/adaptive_navigation_node.py` — same snapshot capture on all NEXT paths
- `app/ui/response/sections/display_section.py` — renders `question_display_text` with fallback to `question.prompt`

## Hardening Notes (V1 release-ready)

- **Score propagation:** `question_node` reads `last_answer_score` from `last_feedback_bundle`; falls back to `last_question_context.quality_rank` when bundle is cleared by navigation (standard NEXT flow). FOLLOW_UP now reachable in production.
- **Stale display:** `navigation_node` and `adaptive_navigation_node` clear `question_display_text` on every index-advancing NEXT, preventing stale prior-question text.
- **Resilience:** `humanizer_service.humanize()` wrapped in try/except in `question_node`; LLM failure falls back to raw `question.prompt`, graph continues.
- **Schema ownership:** `question_node` stores plain prompt text only. `DisplaySection` exclusively renders the DATABASE schema block, preventing duplication.

## Review Trigger

V1.1: enable `HUMANIZER_FOLLOW_UP_ENABLED=True` in production after integration testing with real LLM output.
