# Architecture Review — M1-1: Follow-up Question Engine

**Version:** 1.0  
**Date:** 2026-06-30  
**Status:** Approved for Audit  
**Scope:** V1.1 Milestone M1-1  
**Authoritative references:** PRD EPIC-03, TDS §9, ADR-010, ADR-019

---

## Executive Summary

The Follow-up Question Engine already exists in skeleton form in V1.0:
policy decisions, state counters, conversation history, and the humanizer
prompt are all implemented and tested. The **sole blocker** for V1.1 is that
`humanizer_follow_up_enabled` is hardcoded `False` in
`infrastructure/config/settings.py`.

Activating the flag is **not sufficient by itself**. Before enabling it in
production the following gaps must be closed:

| Gap | Severity | Blocking? |
|-----|----------|-----------|
| No topic-anchoring in follow-up generation | High | Yes |
| No answer-relevance validation on generated follow-up | High | Yes |
| No fallback when LLM follow-up output fails schema parse | High | Yes |
| `follow_up_count` field upper-bound silently caps at `MAX_FOLLOW_UPS` via Pydantic `le=` — no event emitted | Medium | No |
| Follow-up applies only to `QuestionType.WRITTEN`; Coding/SQL excluded | Design decision | Must be explicit |
| `HumanizerInput` passes `last_answer` as freeform text to LLM with no sanitization | Medium | Yes (security) |
| No observable signal emitted when follow-up is triggered or skipped | Low | No |
| Score source for follow-up trigger is dual-path (`last_feedback_bundle` vs `last_question_context.quality_rank`) with inconsistent fallback | Medium | Yes |

---

## 1. Responsibilities

The Follow-up Question Engine is responsible for:

1. **Trigger decision** — determine whether the next conversational turn is a
   follow-up, a remark + new question, or a direct new question.
2. **Topic anchoring** — constrain the follow-up to the competency area of the
   question that elicited the high-quality answer.
3. **Text generation** — produce a natural-language follow-up question via LLM,
   grounded in the candidate's actual answer content.
4. **Budget enforcement** — enforce `MAX_FOLLOW_UPS_PER_INTERVIEW` and
   non-consecutive rule before any LLM call is made.
5. **Fallback handling** — degrade to `DIRECT_QUESTION` or `REMARK_PLUS_QUESTION`
   on any generation or parse failure without breaking session flow.
6. **State propagation** — update `follow_up_count` and
   `last_humanizer_follow_up` in `InterviewState` using policy output, never
   LLM output.

The engine explicitly does **not**:

- Create a new `Question` domain object.
- Add an entry to `planned_areas`.
- Run the evaluation pipeline against the follow-up answer independently.
- Alter question difficulty or area ordering.

---

## 2. New Components

### 2.1 No new top-level service class required for V1.1

The existing `HumanizerService` + `HumanizerPolicyEngine` +
`HumanizerPromptBuilder` structure is architecturally sound. V1.1 extends
and hardens these existing classes rather than introducing a parallel system.

### 2.2 New component: `FollowUpGuard`

**Location:** `services/humanizer/guards/follow_up_guard.py`

**Responsibility:** Validate generated follow-up output before it is accepted.
Owns answer-relevance check (embedding cosine similarity), topic-anchor
validation, and minimum-length check.

**Why separate:** Keeps `HumanizerResponseParser` a pure structural parser.
Keeps validation concerns orthogonal to LLM output parsing.

**Inputs:**
- `HumanizerOutput` (parsed LLM output)
- `HumanizerInput` (contains `last_answer`, `current_question`)
- `FollowUpGuardConfig` (thresholds: min_length, min_relevance_score)

**Outputs:**
- `FollowUpGuardResult`: `{ passed: bool, reason: str }`

### 2.3 New domain event: `FollowUpTriggeredEvent`

**Location:** `domain/events/follow_up_triggered_event.py`

**Emitted by:** `question_node` when `policy_decision == FOLLOW_UP`.

**Payload:** `{ session_id, question_index, question_area, trigger_score, follow_up_count_after }`

**Why:** Provides observability hook for monitoring and future replay audit.

### 2.4 New domain event: `FollowUpSkippedEvent`

**Location:** `domain/events/follow_up_skipped_event.py`

**Emitted when:** Follow-up budget exhausted, non-consecutive rule fired, or
`FollowUpGuard` rejects the generated output after max retries.

**Payload:** `{ session_id, question_index, skip_reason: Literal["budget", "consecutive", "guard_fail", "llm_fail"] }`

---

## 3. Existing Components to Modify

| Component | File | Change Required |
|-----------|------|-----------------|
| `HumanizerPolicyEngine` | `services/humanizer/humanizer_policy_engine.py` | No logic change. Document preconditions explicitly. |
| `HumanizerPromptBuilder` | `services/humanizer/builders/humanizer_prompt_builder.py` | Add `question_area` to context dict; ensure `last_answer` is sanitized before interpolation. |
| `HumanizerResponseParser` | `services/humanizer/humanizer_response_parser.py` | Add `try/except` with structured `ParseFailure` return instead of bare `json.loads` raise. |
| `HumanizerService` | `services/humanizer/humanizer_service.py` | Wire `FollowUpGuard` call after parse; implement retry-on-guard-fail (max 1 retry); implement fallback-to-DIRECT_QUESTION on guard fail after retry. |
| `question_node` | `app/graph/nodes/question_node.py` | (1) Unify score source. (2) Sanitize `last_answer` before populating `HumanizerInput`. (3) Emit domain events. (4) Increment counter only after `FollowUpGuard` passes. |
| `InterviewStateBase` | `domain/contracts/interview_state/base.py` | Relax `le=MAX_FOLLOW_UPS_PER_INTERVIEW` field constraint — cap is enforced by policy, not by Pydantic. Emit event instead. |
| `settings.py` | `infrastructure/config/settings.py` | Change `humanizer_follow_up_enabled` default to `True`. |
| `humanizer_v2.txt` | `app/prompts/transformation/humanizer_v2.txt` | Add `{{question_area}}` slot; strengthen topic-anchor instruction for `follow_up` decision type. |

---

## 4. State Machine

```
─────────────────────────────────────────────────────────────────────────
PRECONDITIONS (evaluated by HumanizerPolicyEngine.decide())
─────────────────────────────────────────────────────────────────────────

[P1] follow_up_enabled == True                   (settings flag)
[P2] question.type == WRITTEN                    (non-written: skip)
[P3] follow_up_count < MAX_FOLLOW_UPS            (budget check)
[P4] last_turn_was_follow_up == False            (consecutive check)
[P5] last_answer_score >= FOLLOW_UP_SCORE_THRESHOLD (score = Quality.OPTIMAL.rank() = 4)

ALL FIVE must be True → decision = FOLLOW_UP
P1..P4 True, P5 False → decision = REMARK_PLUS_QUESTION
P3 False (budget) → decision = DIRECT_QUESTION
P4 False (consecutive) → decision = REMARK_PLUS_QUESTION
P1 False → DIRECT_QUESTION (policy short-circuits at engine construction)

─────────────────────────────────────────────────────────────────────────
GENERATION STATES (post-decision, only if FOLLOW_UP)
─────────────────────────────────────────────────────────────────────────

GENERATE_FOLLOW_UP
    │
    ▼
LLM_CALL → parse (HumanizerResponseParser)
    │
    ├── ParseFailure (JSON error) ──────────────→ FALLBACK_DIRECT_QUESTION
    │
    └── ParseOK
            │
            ▼
        FollowUpGuard.validate()
            │
            ├── PASS ──────────────────────────→ ACCEPT_FOLLOW_UP
            │                                       (increment counter, emit event)
            │
            └── FAIL (low relevance / wrong area / too short)
                    │
                    ▼
                RETRY_ONCE (max 1 retry)
                    │
                    ├── PASS ────────────────→ ACCEPT_FOLLOW_UP
                    └── FAIL again ──────────→ FALLBACK_DIRECT_QUESTION
                                                (do NOT increment counter)

─────────────────────────────────────────────────────────────────────────
TERMINAL STATES
─────────────────────────────────────────────────────────────────────────

ACCEPT_FOLLOW_UP      → set question_display_text, follow_up_count+1,
                        last_humanizer_follow_up=True, emit FollowUpTriggeredEvent
FALLBACK_DIRECT_QUESTION → set question_display_text to raw question.prompt,
                           follow_up_count unchanged, last_humanizer_follow_up=False,
                           emit FollowUpSkippedEvent
REMARK_PLUS_QUESTION  → set question_display_text to LLM remark+question text,
                         follow_up_count unchanged, last_humanizer_follow_up=False
DIRECT_QUESTION       → set question_display_text to raw question.prompt or
                         LLM-framed question, no counter change
```

---

## 5. Sequence Diagram

```
question_node               HumanizerService         HumanizerPolicyEngine
     │                            │                         │
     │─ _resolve_trigger_score()  │                         │
     │    (unified score source)  │                         │
     │                            │                         │
     │─ sanitize(last_answer) ─→  │                         │
     │                            │                         │
     │─ humanize(input_data) ───→ │                         │
     │                            │─ decide(input_data) ──→ │
     │                            │←── decision ────────────│
     │                            │                         │
     │                            │  [if FOLLOW_UP]         │
     │                            │─ build_prompt(input, decision)
     │                            │─ llm.invoke(prompt) ──→ OpenAI
     │                            │←── raw_response ────────│
     │                            │─ parser.parse(response) │
     │                            │                         │
     │                            │  [ParseOK]              │
     │                            │─ guard.validate(output, input)
     │                            │                         │
     │                            │  [FAIL → retry once]    │
     │                            │─ llm.invoke(prompt) ──→ OpenAI
     │                            │←── raw_response ────────│
     │                            │─ parser.parse(response) │
     │                            │─ guard.validate(output, input)
     │                            │                         │
     │←── (policy_decision, output) ───────────────────────│
     │                            │                         │
     │─ update_state()            │                         │
     │    counter, flags, events  │                         │
```

---

## 6. Data Flow

```
InterviewState (read)
  ├── follow_up_count          → HumanizerPolicyEngine (budget check)
  ├── last_humanizer_follow_up → HumanizerPolicyEngine (consecutive check)
  ├── last_feedback_bundle     ┐
  ├── last_question_context    ┘ → _resolve_trigger_score() → last_answer_score
  ├── answers[-1].content      → sanitize() → HumanizerInput.last_answer
  ├── last_question_context    → HumanizerInput.previous_* fields
  └── current_question         → HumanizerInput.current_question

HumanizerInput (frozen, immutable) ──→ HumanizerPolicyEngine.decide()
                                   ──→ HumanizerPromptBuilder.build()

HumanizerDecision (enum) ──→ question_node (tracking only)
HumanizerOutput (parsed)  ──→ FollowUpGuard.validate()

InterviewState (write, model_copy)
  ├── question_display_text    ← humanized_text or raw question.prompt
  ├── chat_history             ← appended
  ├── follow_up_count          ← +1 only if ACCEPT_FOLLOW_UP
  ├── last_humanizer_follow_up ← True only if ACCEPT_FOLLOW_UP
  ├── memory_context           ← updated by InterviewMemoryUpdater
  └── events                   ← appended FollowUpTriggeredEvent or FollowUpSkippedEvent
```

---

## 7. Required Configuration

All configuration resides in two canonical locations (no magic numbers in
service code):

| Constant | Location | Current Value | V1.1 Value |
|----------|----------|---------------|------------|
| `humanizer_follow_up_enabled` | `infrastructure/config/settings.py` | `False` | `True` |
| `MAX_FOLLOW_UPS_PER_INTERVIEW` | `app/settings/constants.py` | `2` | `2` (unchanged) |
| `FOLLOW_UP_SCORE_THRESHOLD` | `infrastructure/config/evaluation.py` | `4` | `4` (= Quality.OPTIMAL.rank()) |
| `FOLLOW_UP_GUARD_MIN_LENGTH` | `infrastructure/config/evaluation.py` (add) | — | `20` chars |
| `FOLLOW_UP_GUARD_MIN_RELEVANCE` | `infrastructure/config/evaluation.py` (add) | — | `0.40` cosine similarity |
| `FOLLOW_UP_LLM_MAX_RETRIES` | `infrastructure/config/evaluation.py` (add) | — | `1` |

**Design rule:** `HumanizerPolicyEngine` reads only from constants/settings.
`FollowUpGuard` reads only from evaluation config. No threshold is inline.

---

## 8. Persistence Requirements

**V1.1: None.**

Follow-up decisions are ephemeral within a session. `follow_up_count` and
`last_humanizer_follow_up` live in `InterviewState` (in-memory). Domain events
(`FollowUpTriggeredEvent`, `FollowUpSkippedEvent`) are appended to
`state.events` and included in any session snapshot.

**V1.2:** When the Replay Engine (EPIC-09) and Progress Tracker (EPIC-10) are
implemented, `state.events` is persisted alongside the session record. Follow-up
trigger events will be queryable from session history at that point.

---

## 9. Interaction with Humanizer

The Follow-up Question Engine **is** the Humanizer operating in `FOLLOW_UP`
mode. The relationship is:

```
HumanizerService
  └── DECISION_BRANCH: follow_up
        ├── Uses: HumanizerPromptBuilder (decision="follow_up")
        ├── Adds: FollowUpGuard (V1.1, new)
        └── Produces: follow-up question text in HumanizerOutput.message
```

The `DIRECT_QUESTION` and `REMARK_PLUS_QUESTION` branches are unaffected.
The humanizer prompt template (`humanizer_v2.txt`) is shared across all
decision types, parameterised by the `{{decision}}` slot. Only the
`follow_up` decision branch requires the new `{{question_area}}` slot for
topic anchoring.

---

## 10. Interaction with Question Generator

**V1.1:** None. The follow-up question is generated entirely by the Humanizer
LLM call. The `LazyAdaptiveInterviewService` and all question pipelines are
not consulted.

This is the PRD EPIC-03 Model A design (conversational follow-up, no new
`Question` object). Model B (evaluated follow-up with a new `Question` object)
is deferred to V2 per ADR-010.

**Implication:** The follow-up text produced by `HumanizerOutput.message` is
displayed via `question_display_text`. It does NOT appear in `state.questions`.
Navigation indices (`current_question_index`) do NOT advance. The session
question count does NOT change.

---

## 11. Interaction with Evaluation

**V1.1:** The follow-up answer is collected as part of the normal answer flow.
The evaluation pipeline (`written_evaluation_node`) runs against it normally.
The resulting score contributes to dimensional averages as if it were a
response to the original question (since the question object is unchanged).

**Known limitation:** The evaluation prompt sees the original `Question.prompt`,
not the humanized follow-up text. The LLM evaluator therefore assesses the
answer against the base question context, which is correct for scoring
fairness — the follow-up probes depth of the same competency, not a new one.

**V2 consideration:** If Model B is implemented, the follow-up would become its
own `Question` with its own evaluation context.

---

## 12. Failure Modes

| Failure | Detection Point | Impact | Recovery |
|---------|----------------|--------|----------|
| LLM returns malformed JSON | `HumanizerResponseParser.parse()` | Follow-up text unavailable | Fallback to `DIRECT_QUESTION`; session continues |
| LLM returns valid JSON but wrong structure | `HumanizerOutput.model_validate()` | Pydantic raises `ValidationError` | Same fallback |
| FollowUpGuard: low relevance (answer and follow-up unrelated) | `FollowUpGuard.validate()` | Low-quality follow-up | 1 retry; then fallback to `DIRECT_QUESTION` |
| FollowUpGuard: topic mismatch (question_area differs) | `FollowUpGuard.validate()` | Follow-up strays into different domain | 1 retry; then fallback |
| FollowUpGuard: output too short | `FollowUpGuard.validate()` | Incomplete follow-up text | 1 retry; then fallback |
| `last_answer_score` is None (no previous answer) | `HumanizerPolicyEngine.decide()` | Cannot trigger follow-up | Policy returns `DIRECT_QUESTION`; no LLM call |
| Budget already exhausted | `HumanizerPolicyEngine.decide()` | — | Policy returns `DIRECT_QUESTION`; no LLM call |
| Consecutive follow-up attempted | `HumanizerPolicyEngine.decide()` | — | Policy returns `REMARK_PLUS_QUESTION`; no follow-up LLM call |
| LLM API timeout / rate limit | `llm.invoke()` raises | Humanizer fails entirely | `question_node` catches all `Exception`; falls back to raw `question.prompt` |

**Critical invariant:** `follow_up_count` is NEVER incremented on any failure
path. The counter increment is gated on `ACCEPT_FOLLOW_UP` only.

---

## 13. Recovery Strategy

The recovery hierarchy (most preferred → least preferred):

1. **Guard retry** — regenerate with identical prompt; valid for transient LLM
   variance.
2. **Fallback to DIRECT_QUESTION** — raw question prompt displayed; no
   conversational framing. Zero user-visible error.
3. **Fallback to raw `question.prompt`** — `question_node` outer try/except
   catches any unhandled exception from `HumanizerService`. Already implemented
   in V1.0.

No failure mode surfaces an error to the candidate. Failures are logged
(`logger.warning`) and emitted as `FollowUpSkippedEvent`.

---

## 14. Determinism

The engine is deterministic with respect to the follow-up **decision**:

- `HumanizerPolicyEngine.decide()` is a pure function of `HumanizerInput` fields.
- Given identical `follow_up_count`, `last_turn_was_follow_up`, and
  `last_answer_score`, the decision is always the same.

The engine is **not** deterministic with respect to the follow-up **text**:

- LLM generation is inherently stochastic (temperature > 0).
- This is expected and acceptable — conversational phrasing variance is a
  feature, not a bug.

**Reproducibility design:** Domain events capture the trigger score and
decision at each turn. A replay of session state can reconstruct exactly which
turns triggered a follow-up and why, even if the exact text differed.

---

## 15. Prompt Strategy

### Current prompt: `humanizer_v2.txt`

**Strengths:**
- Shared across decision types via `{{decision}}` slot.
- Instructions are explicit and concise.
- JSON output format is well-defined.

**Gaps for V1.1:**
1. No `{{question_area}}` slot — the follow-up has no topic anchor beyond the
   vague "same competency area" rule in line 10 of the template.
2. `{{previous_answer}}` is the full raw answer text. For long answers, this
   approaches token budget boundary. No truncation logic.
3. The output contract (`score`, `follow_up_used`) adds tokens to every call.
   For non-follow-up decision types, these fields are irrelevant.

**V1.1 changes to prompt:**
- Add `{{question_area}}` slot with explicit instruction: "The follow-up MUST
  probe deeper into {{question_area}}. Do not introduce unrelated topics."
- Cap `{{previous_answer}}` at 800 chars (truncate at last sentence boundary)
  before interpolation in `HumanizerPromptBuilder`.
- Keep shared template; do not split into per-decision templates (the shared
  structure simplifies prompt registry governance).

### Prompt security note

`{{previous_answer}}` is a user-supplied field. It must be passed through
input sanitization before interpolation (see §18). This is the only
user-supplied field in the humanizer prompt.

---

## 16. Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R1 | LLM ignores topic anchor instruction; follow-up strays into unrelated domain | Medium | High | FollowUpGuard topic-anchor check + retry |
| R2 | `FOLLOW_UP_SCORE_THRESHOLD = 4` (OPTIMAL only) is too strict; very few follow-ups in practice | Medium | Medium | Configurable; can lower to `3` (CORRECT) if insufficient follow-up rate observed in A/B |
| R3 | Token cost per follow-up-eligible session increases | Low | Low | Budget cap in future EPIC-07; current cost acceptable at `gpt-4o-mini` pricing |
| R4 | `FollowUpGuard` relevance check adds local embedding latency (~50ms) | Low | Low | Acceptable within p95 latency budget (< 4s for follow-up generation) |
| R5 | Prompt injection via `last_answer` field | Medium | High | Input sanitization before `HumanizerInput` construction (§18) |
| R6 | `follow_up_count` Pydantic `le=MAX_FOLLOW_UPS` silently truncates if policy has bug | Low | Medium | Remove `le=` constraint from field definition; enforce at policy layer only |
| R7 | Dual score source (`last_feedback_bundle` vs `last_question_context.quality_rank`) produces inconsistent trigger | Medium | High | Unify in `_resolve_trigger_score()` helper; single source of truth |
| R8 | Follow-up fires on Coding/SQL questions unexpectedly if `question.type` check is removed or bypassed | Low | High | Type guard in `question_node` is an explicit early return; covered by existing tests |

---

## 17. Extension Points

The architecture is designed to accommodate the following future extensions
without structural changes:

| Extension | V target | What changes |
|-----------|----------|--------------|
| Model B: evaluated follow-up (new `Question` object) | V2 | `FollowUpService` generates a `Question`; navigation node handles it; evaluation runs independently. `HumanizerService` is not changed. |
| Corpus-backed follow-up retrieval (ChromaDB) | V1.2 | `FollowUpGuard` replaced by `FollowUpSelector` that first queries corpus; falls back to LLM generation. |
| Follow-up for Coding/SQL types | V2 | Remove type guard in `question_node`; add coding/SQL-specific follow-up prompt variant. |
| Configurable trigger threshold per seniority level | V1.2 | `HumanizerPolicyEngine` receives `SeniorityLevel`; threshold looked up from a config dict. |
| Follow-up analytics in progress tracking | V1.2 | `FollowUpTriggeredEvent` is already emitted; `ProgressTracker` (EPIC-10) consumes it. |

---

## 18. Dependency Analysis

```
question_node
  ├── HumanizerService             [modify: wire FollowUpGuard]
  │     ├── HumanizerPolicyEngine  [no change to logic]
  │     ├── HumanizerPromptBuilder [modify: add question_area slot, truncate last_answer]
  │     ├── HumanizerResponseParser [modify: structured error return]
  │     └── FollowUpGuard          [NEW]
  │           └── sentence-transformers (all-MiniLM-L6-v2)  [already in requirements]
  ├── InterviewMemoryUpdater       [no change]
  ├── settings                     [change humanizer_follow_up_enabled default]
  ├── evaluation config            [add 3 new constants]
  └── domain/events                [add 2 new event types]
```

**External dependencies introduced:** None. `all-MiniLM-L6-v2` is already
present in `requirements.txt` for deduplication and planning services.

---

## 19. Performance Impact

| Operation | Current latency | V1.1 delta | Notes |
|-----------|----------------|------------|-------|
| Non-follow-up question turn | ~100ms (humanizer LLM) | 0 | Policy returns early; no guard call |
| Follow-up question turn (happy path) | ~1.5s (LLM) | +~50ms (embedding + guard) | Within p95 budget of 4s |
| Follow-up turn (1 retry) | ~1.5s | +~1.5s | Still < 4s p95 budget |
| Follow-up turn (fallback) | ~1.5s (failed) | +~50ms | Fallback to raw text: near-instant |

**Token cost per follow-up:** approximately +300–500 tokens (input + output for
humanizer call). At `gpt-4o-mini` pricing (~$0.15/1M input, $0.60/1M output),
cost delta per triggered follow-up ≈ $0.0004. Negligible.

---

## 20. Security Considerations

### 20.1 Prompt injection via `last_answer`

`last_answer` is the primary injection vector. It is interpolated into
`{{previous_answer}}` in the humanizer prompt, which is in the human-message
slot (not the system prompt).

**V1.1 mitigation (minimal, pre-Prompt Security Layer):**
- Truncate `last_answer` to 800 chars in `HumanizerPromptBuilder` before
  interpolation.
- Strip null bytes and control characters in `question_node` before
  constructing `HumanizerInput`.
- The prompt structure places `{{previous_answer}}` after the RULES section;
  instruction injection would need to override already-delivered system
  instructions — low probability of success with `gpt-4o-mini`.

**V1.1 does NOT implement full PromptSecurityLayer** (that is EPIC-05, M1 of
V1.1 in the PRD). The sanitization above is a minimal guard sufficient for
the Follow-up Engine specifically.

**V1.2 (EPIC-05):** Full PromptSecurityLayer wraps all LLM calls including
humanizer; `last_answer` passes through `PromptSecurityLayer` before any
interpolation.

### 20.2 Follow-up output injection

The generated follow-up text (`HumanizerOutput.message`) is rendered directly
to the candidate UI. It does not flow back into any subsequent LLM prompt.
No injection risk from the output side in V1.1.

---

## 21. Acceptance Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Follow-up rate is too low to be noticeable in user testing (OPTIMAL threshold too strict) | Medium | Run A/B with threshold=3 (CORRECT) in parallel |
| Follow-up text is generic / not grounded in candidate's answer | Medium | FollowUpGuard relevance check filters low-quality output |
| Follow-up appears on wrong interview type (Coding/SQL) | Low | Existing type guard in `question_node`; covered by existing tests |
| Counter bug: follow-up counted even when guard rejects | Low | Critical invariant: counter increment is gated on `ACCEPT_FOLLOW_UP`; must be unit-tested |
| Session length appears longer to candidate (follow-up replaces nothing visually) | Medium | UX clarification: follow-up is NOT an additional question; coaching report makes this clear |

---

## 22. Open Architectural Decisions

### ADR-024 (proposed): Follow-up trigger threshold per seniority

**Question:** Should `FOLLOW_UP_SCORE_THRESHOLD` vary by seniority level?

- Junior: threshold = 3 (CORRECT) — easier to trigger; more coaching value
- Mid: threshold = 4 (OPTIMAL) — current default
- Senior: threshold = 4 (OPTIMAL) — or add upper cap to avoid following up on
  trivial answers already given at senior depth

**V1.1 recommendation:** Keep single threshold = 4. Introduce per-seniority
config in V1.2 only after observing actual follow-up rate data.

**Status:** Deferred to V1.2.

---

### ADR-025 (proposed): FollowUpGuard embedding model choice

**Question:** Which embedding model to use for answer-relevance check in
`FollowUpGuard`?

Option A: `all-MiniLM-L6-v2` (local, already in requirements) — fast (~10ms),
free, no API call.

Option B: `text-embedding-3-small` (OpenAI) — higher quality, +~100ms,
+~$0.00002 per check.

**V1.1 recommendation:** Option A. The relevance check is a rough quality
gate, not a precision recall task. Local model is sufficient and adds zero
external dependency or latency budget.

**Status:** Decision for V1.1: Option A.

---

## 23. Recommended Architecture for V1.1

### Structural summary

```
services/humanizer/
  ├── humanizer_service.py          [modify: wire FollowUpGuard, 1-retry loop]
  ├── humanizer_policy_engine.py    [no logic change]
  ├── humanizer_response_parser.py  [modify: structured error return]
  ├── builders/
  │   └── humanizer_prompt_builder.py  [modify: question_area slot, answer truncation]
  ├── contracts/
  │   ├── humanizer_input.py        [no change]
  │   ├── humanizer_output.py       [no change]
  │   └── humanizer_decision.py     [no change]
  └── guards/
      └── follow_up_guard.py        [NEW]

domain/events/
  ├── follow_up_triggered_event.py  [NEW]
  └── follow_up_skipped_event.py    [NEW]

infrastructure/config/
  ├── settings.py                   [humanizer_follow_up_enabled = True]
  └── evaluation.py                 [add 3 guard constants]

app/prompts/transformation/
  └── humanizer_v2.txt              [add {{question_area}} slot]

app/graph/nodes/
  └── question_node.py              [unify score source, sanitize answer, emit events]

domain/contracts/interview_state/
  └── base.py                       [remove le= constraint from follow_up_count]
```

### Key design invariants (must be enforced in implementation)

1. **Policy owns counter** — `follow_up_count` incremented only by
   `question_node` based on `policy_decision == FOLLOW_UP` AND
   `FollowUpGuard.passed == True`. Never by `HumanizerService` directly.

2. **LLM output never controls counter** — `HumanizerOutput.follow_up_used` is
   ignored for counter purposes. It exists only for prompt observability.

3. **Type guard is non-negotiable** — Follow-up decision is only evaluated for
   `QuestionType.WRITTEN`. Non-written questions return before `HumanizerInput`
   is constructed.

4. **Fallback is transparent** — Candidate sees a coherent question regardless
   of which path executed. No error state is surfaced.

5. **Score source is unified** — `_resolve_trigger_score()` in `question_node`
   returns the score from `last_feedback_bundle` if available, otherwise from
   `last_question_context.quality_rank`. This eliminates the dual-source
   inconsistency in V1.0.

---

## 24. V1.1 / V1.2 / V2 Classification

### Required for V1.1

- Unified score source in `question_node`
- Input sanitization for `last_answer` (minimal, pre-EPIC-05)
- `FollowUpGuard` (relevance + topic + length check, 1 retry)
- Structured error return in `HumanizerResponseParser`
- `{{question_area}}` slot in prompt + answer truncation
- `FollowUpTriggeredEvent` and `FollowUpSkippedEvent`
- Remove `le=` Pydantic constraint from `follow_up_count`
- `humanizer_follow_up_enabled = True` default
- Three new evaluation config constants

### Recommended for V1.2

- Full `PromptSecurityLayer` wrapping humanizer prompt (EPIC-05)
- Per-seniority follow-up threshold (ADR-024)
- Corpus-backed follow-up retrieval via ChromaDB (replaces pure LLM generation)
- Follow-up analytics in `ProgressTracker` (EPIC-10 dependency)

### Future (V2+)

- Model B: follow-up as independently evaluated `Question` object (ADR-010)
- Follow-up for Coding/SQL question types
- Follow-up effectiveness signal in coaching report ("You demonstrated deeper
  Redis knowledge when probed")
