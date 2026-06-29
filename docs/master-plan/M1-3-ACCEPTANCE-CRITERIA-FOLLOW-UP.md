# M1-3 — Follow-up Engine: Acceptance Criteria

**Status:** FROZEN — no architectural decisions may be taken during implementation  
**Version:** 1.0  
**Date:** 2026-06-30  
**Authority:** PRD EPIC-03 · TDS §9 · ARCH-REVIEW-M1-1 · Audit M1-2 · ADR-010  
**Baseline test count:** 1427

---

## SECTION A — Scope Freeze

### IN SCOPE (V1.1 M1)

- Activate `humanizer_follow_up_enabled = True` as default
- Consolidate all follow-up configuration into `infrastructure/config/settings.py`
- `FollowUpSelector`: deterministic pre-selection of eligible follow-up slots before session start
- `FollowUpGuard`: deterministic rule-based validation of generated follow-up text (no embeddings)
- `supports_follow_up: bool = True` field on `Question` domain model
- Unified score source (`_resolve_trigger_score`) in `question_node`
- Structured error return from `HumanizerResponseParser` (no bare raise)
- `{{question_area}}` slot in `humanizer_v2.txt` + answer truncation in builder
- `FollowUpTriggeredEvent` and `FollowUpSkippedEvent` domain events
- Type `events` field as `list[InterviewEvent]` in `InterviewStateBase`
- Remove `le=MAX_FOLLOW_UPS_PER_INTERVIEW` Pydantic constraint; replace with explicit validator
- Minimal answer input sanitization in `question_node` (strip control chars, truncate)
- All required tests (unit, integration, regression, security)
- Update ADR-010 (activation note)
- File ADR-019 (Follow-up Question Engine design)
- File ADR-024 (deferred decision: per-seniority threshold)
- File ADR-025 (decision: local embedding, deferred to V1.2)

### OUT OF SCOPE — Deferred to V1.2

- Embedding-based relevance in `FollowUpGuard` (ADR-025 decision)
- Corpus-backed follow-up retrieval via ChromaDB
- Per-seniority `FOLLOW_UP_SCORE_THRESHOLD` (ADR-024 decision)
- Full `PromptSecurityLayer` wrapping humanizer (EPIC-05)
- `supports_follow_up` populated by question generation pipelines
- Follow-up analytics in `ProgressTracker` (EPIC-10)
- Follow-up effectiveness signal in coaching report

### Deferred to V2

- Model B: follow-up as independently evaluated `Question` object (ADR-010)
- Follow-up for `QuestionType.CODING` and `QuestionType.DATABASE`
- Follow-up replay diff in Replay Engine
- Follow-up analytics in Enterprise Analytics (EPIC-13)

---

## SECTION B — Final Architecture

### B1. `HumanizerPolicyEngine`

| | |
|---|---|
| **Current** | Imports `MAX_FOLLOW_UPS_PER_INTERVIEW` from `app/settings/constants.py` and `FOLLOW_UP_SCORE_THRESHOLD` from `infrastructure/config/evaluation.py` |
| **Target** | Imports both constants exclusively from `infrastructure/config/settings.py` |
| **File** | `services/humanizer/humanizer_policy_engine.py` |
| **Breaking change** | No — logic unchanged |
| **Regression risk** | Low — import path change only |
| **Tests** | Existing: `test_humanizer_policy_engine.py`, `test_followup_max_limit.py` — must all pass unchanged |

---

### B2. `HumanizerService`

| | |
|---|---|
| **Current** | No try/except around parser call; LLM failure caught only by outer `question_node` try/except |
| **Target** | Catches `ParseFailure` sentinel from parser; emits `FollowUpSkippedEvent(skip_reason="llm_fail")`; returns `(HumanizerDecision.DIRECT_QUESTION, fallback_output)` without propagating |
| **File** | `services/humanizer/humanizer_service.py` |
| **Breaking change** | No — return type `tuple[HumanizerDecision, HumanizerOutput]` unchanged |
| **Regression risk** | Low |
| **Tests** | New: test parse failure returns `DIRECT_QUESTION`; test skip event emitted on failure |

---

### B3. `HumanizerPromptBuilder`

| | |
|---|---|
| **Current** | No `question_area` in context; passes full `last_answer` text to template |
| **Target** | Derives `question_area = input_data.current_question.area.value`; adds to context dict; truncates `last_answer` to `FOLLOW_UP_MAX_INPUT_CHARS` (800) chars at last whitespace boundary |
| **File** | `services/humanizer/builders/humanizer_prompt_builder.py` |
| **Breaking change** | No |
| **Regression risk** | Low — additive context change |
| **Tests** | New: test `question_area` present in rendered prompt; test truncation at boundary |

---

### B4. `HumanizerResponseParser`

| | |
|---|---|
| **Current** | `json.loads(response)` raises `JSONDecodeError` on malformed input |
| **Target** | Returns a `ParseFailure` sentinel value (e.g., `None` or typed dataclass) on any parse/validation error; does not raise; logs `warning` with response hash |
| **File** | `services/humanizer/humanizer_response_parser.py` |
| **Breaking change** | Return type widens to `HumanizerOutput \| None` (or equivalent sentinel) |
| **Regression risk** | Medium — callers must handle `None`; `HumanizerService` must check before proceeding |
| **Tests** | New: test malformed JSON returns `None`; test valid JSON still returns `HumanizerOutput` |

---

### B5. `question_node`

| | |
|---|---|
| **Current** | Dual score source (bundle → context fallback) with no log on `None`; no `supports_follow_up` check; no input sanitization; increments counter before guard |
| **Target** | (1) Unified `_resolve_trigger_score(state)` helper: returns `bundle.overall_quality.rank()` if bundle exists, else `last_question_context.quality_rank`, else `None` with `warning` log. (2) Type guard extended: skip humanizer follow-up if `question.supports_follow_up == False`. (3) Strip control chars + truncate `last_answer` to `FOLLOW_UP_MAX_INPUT_CHARS` before `HumanizerInput` construction. (4) Increment `follow_up_count` only after `FollowUpGuard` passes. (5) Emit `FollowUpTriggeredEvent` or `FollowUpSkippedEvent` on every follow-up decision path |
| **File** | `app/graph/nodes/question_node.py` |
| **Breaking change** | No — `InterviewState` output contract unchanged |
| **Regression risk** | Medium — counter-increment logic change; score-source change |
| **Tests** | New: test score source priority; test `supports_follow_up=False` suppresses follow-up; test counter NOT incremented on guard failure; test events emitted. Existing: all `test_followup_max_limit.py` tests must pass |

---

### B6. `InterviewStateBase`

| | |
|---|---|
| **Current** | `follow_up_count: int = Field(default=0, ge=0, le=MAX_FOLLOW_UPS_PER_INTERVIEW)` — Pydantic silently caps via field constraint |
| **Target** | `follow_up_count: int = Field(default=0, ge=0)` with explicit `@field_validator` raising `ValueError("follow_up_count exceeds MAX_FOLLOW_UPS_PER_INTERVIEW")` if value > configured max. `events: list[InterviewEvent]` typed. |
| **File** | `domain/contracts/interview_state/base.py` |
| **Breaking change** | Yes — test `test_follow_up_count_invalid` expects `ValidationError`; message changes. Must be updated atomically. |
| **Regression risk** | Low if test updated atomically |
| **Tests** | Existing: `test_follow_up_count_invalid` — rewrite to assert new validator message. Existing: `test_follow_up_count_valid`, `test_follow_up_count_limit_matches_constant` — must pass unchanged |

---

### B7. `Question`

| | |
|---|---|
| **Current** | No `supports_follow_up` field |
| **Target** | Add `supports_follow_up: bool = True` — default `True` preserves full backward compatibility for all existing questions |
| **File** | `domain/contracts/question/question.py` |
| **Breaking change** | No — additive field with default |
| **Regression risk** | Low |
| **Tests** | New: test default is `True`; test `question_node` skips follow-up when `False`. Existing question contract tests must pass |

---

### B8. `infrastructure/config/settings.py`

| | |
|---|---|
| **Current** | Contains `humanizer_enabled`, `humanizer_follow_up_enabled=False` only |
| **Target** | Contains all follow-up parameters listed in Section C |
| **File** | `infrastructure/config/settings.py` |
| **Breaking change** | No — settings are additive; existing keys renamed if moving from other files (see Section C) |
| **Regression risk** | Medium — `HumanizerPolicyEngine` import path changes; any test patching the old import path must be updated |
| **Tests** | Existing: `test_production_config.py` assertions on `MAX_FOLLOW_UPS_PER_INTERVIEW == 2` must be updated to read from settings; any mock of `evaluation.py.FOLLOW_UP_SCORE_THRESHOLD` must be updated |

---

### B9. `humanizer_v2.txt`

| | |
|---|---|
| **Current** | No `{{question_area}}` slot; rule 10 is a generic text instruction |
| **Target** | Add `QUESTION COMPETENCY AREA: {{question_area}}` slot before RULES; strengthen rule 10: "For `follow_up`: the follow-up MUST probe within `{{question_area}}`. Do not introduce topics outside this area." |
| **File** | `app/prompts/transformation/humanizer_v2.txt` |
| **Breaking change** | No |
| **Regression risk** | Low — non-follow-up decision branches are unaffected by the new slot |
| **Tests** | New: prompt render test asserts `{{question_area}}` is substituted; test that unrendered placeholder is not present in final prompt |

---

### B10. `FollowUpGuard` (new)

| | |
|---|---|
| **Current** | Does not exist |
| **Target** | Deterministic rule-based validator. See Section E for full rule checklist. |
| **File** | `services/humanizer/guards/follow_up_guard.py` |
| **Breaking change** | N/A — new component |
| **Regression risk** | None on existing paths; `HumanizerService` must wire it |
| **Tests** | New: full guard test suite (see Section G) |

---

### B11. `FollowUpSelector` (new)

| | |
|---|---|
| **Current** | Does not exist; follow-up eligibility is evaluated lazily per turn |
| **Target** | Deterministic pre-selection at session start. Given `planned_areas` and `total_questions`, produces a frozen `Set[int]` of question indices eligible to trigger a follow-up. Selection respects all constraints in Section D. Stored in `InterviewState.follow_up_eligible_indices: frozenset[int]`. `question_node` checks membership before calling policy engine. |
| **File** | `services/humanizer/selector/follow_up_selector.py` |
| **Breaking change** | Requires new `follow_up_eligible_indices` field in `InterviewStateBase` |
| **Regression risk** | Low — field default is `frozenset()` which disables follow-up until selector runs; selector runs at session init |
| **Tests** | New: full selector test suite (see Section G) |

---

### B12. `FollowUpTriggeredEvent`, `FollowUpSkippedEvent` (new)

| | |
|---|---|
| **Current** | Do not exist |
| **Target** | Both extend `InterviewEvent`. Payloads defined in Section D of ARCH-REVIEW-M1-1. |
| **Files** | `domain/events/follow_up_triggered_event.py`, `domain/events/follow_up_skipped_event.py` |
| **Breaking change** | No |
| **Regression risk** | None |
| **Tests** | New: test both events are appended to `state.events` on the correct paths |

---

## SECTION C — Configuration Freeze

**Rule:** Every follow-up parameter lives exclusively in `infrastructure/config/settings.py` as a field of the `Settings` Pydantic model. No follow-up constant may remain in `evaluation.py`, `app/settings/constants.py`, or any other file. Existing constants in those files that are referenced by follow-up code must be removed from their current location and replaced with imports from `settings`.

| Parameter | Type | Value | Previously in |
|---|---|---|---|
| `humanizer_follow_up_enabled` | `bool` | `True` | `settings.py` (already) — change default |
| `follow_up_score_threshold` | `int` | `4` | `infrastructure/config/evaluation.py` → **remove** |
| `max_follow_ups_per_interview` | `int` | `2` | `app/settings/constants.py` → **remove** |
| `follow_up_min_length` | `int` | `20` | New |
| `follow_up_max_input_chars` | `int` | `800` | New |
| `follow_up_min_keyword_overlap` | `int` | `1` | New |
| `follow_up_selector_policy` | `Literal["percentage", "fixed"]` | `"percentage"` | New |
| `follow_up_percentage` | `float` | `0.20` | New (was `DEFAULT_FOLLOWUP_RATE` in `constants.py`) |
| `follow_up_allowed_areas` | `list[str] \| None` | `None` (= all written areas) | New |
| `follow_up_allowed_types` | `list[str]` | `["written"]` | New |
| `follow_up_logging_enabled` | `bool` | `True` | New |
| `follow_up_sanitize_input` | `bool` | `True` | New |

**Explicit prohibition:**

- `FOLLOW_UP_SCORE_THRESHOLD` must NOT exist in `evaluation.py` after M1 implementation.
- `MAX_FOLLOW_UPS_PER_INTERVIEW` must NOT exist in `app/settings/constants.py` after M1 implementation.
- `DEFAULT_FOLLOWUP_RATE` must NOT exist in `app/settings/constants.py` after M1 implementation.
- No follow-up parameter may be hardcoded in service or node files.

---

## SECTION D — FollowUpSelector

### Behaviour contract

`FollowUpSelector` is a **pure function** of `(total_questions: int, planned_areas: list[str], settings: Settings) → frozenset[int]`.

It determines, before the session begins, which question indices are eligible for a follow-up turn. It is deterministic, reproducible, and not influenced by LLM output or runtime state.

### Selection algorithm

1. Compute `max_follow_ups = floor(total_questions × follow_up_percentage)`, capped at `max_follow_ups_per_interview`.
2. Filter candidate indices: keep only indices where `planned_areas[index]` is in `follow_up_allowed_areas` (or all written areas if `None`).
3. Remove index `0` (first question never eligible).
4. Remove index `total_questions - 1` (last question never eligible).
5. From remaining candidates, select `max_follow_ups` indices using a fixed spacing algorithm (evenly distributed, no consecutive pairs).
6. Return as `frozenset[int]`.

### Constraints (all must be enforced, all must be tested)

| Constraint | Rule |
|---|---|
| No first question | Index 0 is always excluded |
| No last question | Index `total_questions - 1` is always excluded |
| No consecutive indices | No two selected indices are adjacent |
| Percentage cap | Selected count ≤ `floor(total × percentage)` |
| Hard cap | Selected count ≤ `max_follow_ups_per_interview` |
| Area filter | Only areas in `follow_up_allowed_areas` (written areas only in V1.1) |
| `supports_follow_up` | Only questions where `Question.supports_follow_up == True` (checked at runtime in `question_node`, not in selector, since questions may not all exist at session start in adaptive mode) |
| No question count change | `FollowUpSelector` does not add or remove questions from `state.questions` |
| Adaptive compatibility | Selector runs on `planned_areas` (always fully known at session start), not on lazily generated `questions` list |
| Determinism | Given same inputs, output is always identical |

### Integration point

`InterviewStateBase` gains `follow_up_eligible_indices: frozenset[int] = Field(default_factory=frozenset)`.

The session factory (or graph init node) populates it by calling `FollowUpSelector.select(...)` once.

`question_node` checks `state.current_question_index in state.follow_up_eligible_indices` as precondition before evaluating policy.

---

## SECTION E — FollowUpGuard

### Version freeze: V1.1

**Embeddings are NOT used in V1.1.** The guard is entirely deterministic. All rules operate on string properties.

Embedding-based relevance is deferred to V1.2 (ADR-025 decision).

### Rule checklist (all must pass for output to be accepted)

| # | Rule | Check |
|---|---|---|
| G-R1 | Minimum length | `len(output.message.strip()) >= follow_up_min_length` (default: 20 chars) |
| G-R2 | Keyword overlap | At least `follow_up_min_keyword_overlap` word(s) from `last_answer` (≥ 4 chars, non-stopword) appear in `output.message` |
| G-R3 | Question area anchor | `output.message` contains at least one token from `question.area.value` label or a synonyms list (configurable per area) |
| G-R4 | Not verbatim duplicate | Normalised `output.message` must differ from `question.prompt` by > 30% character edit distance |
| G-R5 | No raw JSON | `output.message` does not start with `{` and does not contain `"decision":` or `"message":` substrings |
| G-R6 | No markdown | `output.message` does not contain `#`, ` ``` `, `**`, `__` sequences |
| G-R7 | No unrendered placeholders | `output.message` does not match `\{\{[^}]+\}\}` |
| G-R8 | Contains a question | `output.message` contains `?` |
| G-R9 | Input sanitized | `last_answer` passed to overlap check is the sanitized version (control chars stripped, truncated) |
| G-R10 | Output sanitized | `output.message` has no control characters (strip before evaluation) |

### Retry policy

On guard failure: 1 retry (re-invoke LLM with identical prompt).  
On second failure: `FollowUpSkippedEvent(skip_reason="guard_fail")`; fall back to `DIRECT_QUESTION`.  
Counter is NOT incremented on guard failure.

---

## SECTION F — Security Acceptance

| Threat | Mitigation | Applied at |
|---|---|---|
| Direct prompt injection via `last_answer` | Strip control chars + truncate to `FOLLOW_UP_MAX_INPUT_CHARS` | `question_node` before `HumanizerInput` construction |
| Indirect prompt injection via `last_answer` | Sanitized text placed in `{{previous_answer}}` slot (human-message, after RULES block) | `HumanizerPromptBuilder` |
| Prompt override (`ignore previous instructions`, `new role:`) | Not addressed in V1.1 (full PromptSecurityLayer is EPIC-05, V1.2). Partially mitigated by truncation + position-after-rules. | V1.2 |
| Role override (`You are now...`) | Same as above — V1.2 |
| Markdown injection in follow-up output | G-R6 in `FollowUpGuard` rejects output containing markdown syntax | `FollowUpGuard` |
| JSON injection in follow-up output | G-R5 in `FollowUpGuard` rejects JSON-shaped output | `FollowUpGuard` |
| Unrendered placeholder in output | G-R7 in `FollowUpGuard` | `FollowUpGuard` |
| Answer length abuse (DoS via long answers) | `FOLLOW_UP_MAX_INPUT_CHARS` truncation | `question_node` |
| Sensitive prompt leakage in follow-up output | Not addressed in V1.1; no system prompt sentinel yet. V1.2 (EPIC-05 OutputValidationLayer). | V1.2 |
| Prompt delimiter escaping | `{{previous_answer}}` is placed inside the human-message slot, after all instruction sections. No additional escaping in V1.1. V1.2 adds structured delimiter wrapping. | V1.2 |

**Explicit acknowledgement:** Threats marked V1.2 are known-accepted risks for V1.1. The minimal truncation + position mitigations reduce the attack surface to an acceptable level for the single-user Gradio deployment. They are insufficient for multi-tenant or public API deployments (V2 scope).

---

## SECTION G — Testing Acceptance

### Unit Tests (new, required)

| Test file | Covers |
|---|---|
| `tests/services/humanizer/guards/test_follow_up_guard.py` | All 10 G-R rules pass; each rule fails independently; retry path; fallback path |
| `tests/services/humanizer/selector/test_follow_up_selector.py` | All 7 selector constraints (first/last/consecutive/cap/area/determinism/adaptive) |
| `tests/services/humanizer/test_humanizer_response_parser.py` (extend) | Malformed JSON returns `None`; valid JSON returns `HumanizerOutput` |
| `tests/services/humanizer/test_humanizer_service.py` (extend) | `ParseFailure` triggers `DIRECT_QUESTION` return; `FollowUpSkippedEvent` emitted |
| `tests/services/humanizer/builders/test_humanizer_prompt_builder.py` (extend) | `question_area` present in context; truncation at 800 chars; `{{question_area}}` rendered |
| `tests/domain/events/test_follow_up_events.py` | `FollowUpTriggeredEvent` fields; `FollowUpSkippedEvent` `skip_reason` enum |
| `tests/domain/contracts/test_question.py` (extend) | `supports_follow_up` default `True`; `False` suppresses follow-up in node |

### Integration Tests (new, required)

| Test file | Covers |
|---|---|
| `tests/graph/nodes/test_question_node_followup.py` | Score source priority; `supports_follow_up=False` suppresses; counter increment gated on guard pass; events appended to state; fallback on guard fail |
| `tests/graph/nodes/test_question_node_selector.py` | `follow_up_eligible_indices` membership check gates policy call |

### Regression Tests (existing — must NOT break)

- `tests/services/humanizer/test_humanizer_policy_engine.py` — all tests
- `tests/services/humanizer/test_followup_max_limit.py` — all tests (update import path if settings move)
- `tests/services/humanizer/test_humanizer_prompt_builder.py` — all tests
- `tests/domain/contracts/test_interview_state.py` — `test_follow_up_count_valid` (passes), `test_follow_up_count_limit_matches_constant` (update constant import), `test_follow_up_count_invalid` (rewrite: assert new validator message, same `ValidationError` type)
- `tests/services/question_intelligence/test_production_config.py` — update `MAX_FOLLOW_UPS_PER_INTERVIEW` import to `settings`
- All 1427 existing tests: net addition only; zero regressions

### Property Tests (new, recommended)

| Property | Assertion |
|---|---|
| Selector determinism | `select(n, areas, s) == select(n, areas, s)` for 100 random inputs |
| Selector no-consecutive | For all pairs `(i, j)` in output: `abs(i-j) > 1` |
| Guard idempotency | `guard.validate(output, input) == guard.validate(output, input)` |

### Prompt Tests (new, required)

| Test | Assertion |
|---|---|
| `humanizer_v2.txt` renders without unresolved placeholders given full context | No `{{...}}` in rendered output |
| `{{question_area}}` substituted correctly | Rendered prompt contains `area.value` string |
| `{{previous_answer}}` truncated to ≤ 800 chars | Rendered field length ≤ 800 |

### Parser Tests (new, required — extend existing file)

- Malformed JSON → `None`
- Valid JSON missing required fields → `None`
- Valid complete JSON → `HumanizerOutput`
- `follow_up_used=True` JSON → parsed correctly

### Guard Tests (new, required — in guard test file)

- Each of G-R1 through G-R10 independently triggers `FAIL` when violated
- All rules passing → `PASS`
- Empty string → FAIL on G-R1 and G-R8
- Verbatim copy of base question → FAIL on G-R4

### Selector Tests (new, required — in selector test file)

- Zero eligible questions when total < 3
- Single eligible question when total = 3
- Consecutive constraint enforced at boundary
- Area filter excludes non-written areas
- `follow_up_percentage=0.0` → empty set
- `max_follow_ups_per_interview=0` → empty set
- Identical inputs → identical output (10 repetitions)

### Security Tests (new, required)

| Test | Input | Assertion |
|---|---|---|
| Truncation | `last_answer` > 800 chars | `HumanizerInput.last_answer` ≤ 800 chars |
| Control char strip | `last_answer` with `\x00`, `\r`, `\x1b` | Characters absent in `HumanizerInput.last_answer` |
| Guard rejects JSON output | `output.message = '{"decision": "follow_up"}'` | Guard G-R5 FAIL |
| Guard rejects markdown | `output.message = "# Follow up\n..."` | Guard G-R6 FAIL |
| Guard rejects placeholder | `output.message = "Tell me about {{topic}}"` | Guard G-R7 FAIL |

---

## SECTION H — Regression Checklist

| Component | Can change? | Reason |
|---|---|---|
| `InterviewScoringEngine` | NO | Scoring is independent of follow-up |
| `DecisionEngine` (hire decision) | NO | Unaffected by conversational framing |
| `SignalEnrichmentStep` (Strategy B) | NO | Operates on evaluation results, not questions |
| `WrittenEvaluationNode` | NO | Evaluates against `Question.prompt`, not humanized text |
| `ExecutionNode` / `EvaluationNode` (coding/SQL) | NO | Follow-up is `WRITTEN` only |
| `NarrativeAssembler` / coaching report | NO | No follow-up signal in narrative (V1.1) |
| `FeedbackBundle` / `FeedbackBuilder` | NO | Unchanged |
| `InterviewEvaluationService` | NO | Unchanged |
| `AdaptiveNavigationNode` | NO | Follow-up does not affect index or `planned_areas` |
| All `QuestionResult` DTOs | NO | Public JSON contracts frozen |
| `InterviewEvaluation` DTO | NO | |
| `HireDecision` enum | NO | |
| `EvaluationDecision` schema | NO | |
| PDF/JSON export | NO | Report content unaffected |
| `HumanizerDecision` enum | NO — additive only | New values forbidden in V1.1 |
| `HumanizerInput` | NO | No new fields required |
| `HumanizerOutput` | NO | `follow_up_used` field already present |
| `question_node` counter logic | YES — intentional | Guard-gated increment (C in ARCH-REVIEW) |
| `InterviewStateBase` `follow_up_count` validator | YES — intentional | Remove `le=`, add explicit validator |
| `InterviewStateBase` `events` type | YES — intentional | `list` → `list[InterviewEvent]` |
| `Question` model | YES — additive | `supports_follow_up: bool = True` |
| `settings.py` | YES — additive | New follow-up parameters |

---

## SECTION I — Acceptance Gates

| Gate | Description | Criterion |
|---|---|---|
| G01 | Config consolidated | Zero follow-up constants in `evaluation.py` or `constants.py`; all in `settings.py` |
| G02 | `humanizer_follow_up_enabled` default | `settings.humanizer_follow_up_enabled == True` |
| G03 | Selector deterministic | 100 repeated calls with same input produce identical output |
| G04 | Selector: no first/last | Index 0 and `total-1` never in selected set |
| G05 | Selector: no consecutive | No two selected indices are adjacent |
| G06 | Selector: cap respected | Selected count ≤ `max_follow_ups_per_interview` |
| G07 | `supports_follow_up` field | `Question` model has field; default `True`; `False` suppresses follow-up in node |
| G08 | `FollowUpSelector` integrated | `state.follow_up_eligible_indices` populated at session init |
| G09 | Score source unified | `_resolve_trigger_score` returns `None` + warning when both sources absent; never silently returns stale value |
| G10 | Parser structured return | `HumanizerResponseParser.parse` returns `None` (not raises) on malformed JSON |
| G11 | Service fallback on parse fail | `HumanizerService` returns `DIRECT_QUESTION` when parser returns `None` |
| G12 | Guard passes G-R1..G-R10 | All 10 rules enforced; each independently tested |
| G13 | Guard retry policy | 1 retry on guard fail; fallback to `DIRECT_QUESTION` on second fail |
| G14 | Counter integrity | `follow_up_count` incremented only on `ACCEPT_FOLLOW_UP` (policy == FOLLOW_UP AND guard passes) |
| G15 | Events emitted | `FollowUpTriggeredEvent` or `FollowUpSkippedEvent` appended to `state.events` on every follow-up decision path |
| G16 | Prompt anchor | Rendered `humanizer_v2.txt` contains `question_area` value; no unrendered `{{...}}` |
| G17 | Input sanitization | `last_answer` stripped of control chars and truncated to `FOLLOW_UP_MAX_INPUT_CHARS` before `HumanizerInput` |
| G18 | Security: guard rejects JSON output | Follow-up containing `"decision":` substring fails guard G-R5 |
| G19 | Security: guard rejects markdown | Follow-up containing ` ``` ` or `#` fails guard G-R6 |
| G20 | No regression | All 1427 baseline tests pass (net additions only) |
| G21 | ADR-010 updated | Contains activation note for V1.1 |
| G22 | ADR-019 filed | Follow-up Question Engine design decision documented |
| G23 | ADR-024 filed | Per-seniority threshold decision documented (decision: deferred to V1.2) |
| G24 | ADR-025 filed | Embedding model decision documented (decision: local model, deferred to V1.2) |
| G25 | `events` field typed | `InterviewStateBase.events: list[InterviewEvent]` |

---

## SECTION J — Deliverables

### Code

- `services/humanizer/guards/follow_up_guard.py` (new)
- `services/humanizer/selector/follow_up_selector.py` (new)
- `domain/events/follow_up_triggered_event.py` (new)
- `domain/events/follow_up_skipped_event.py` (new)
- `services/humanizer/humanizer_policy_engine.py` (modified)
- `services/humanizer/humanizer_service.py` (modified)
- `services/humanizer/builders/humanizer_prompt_builder.py` (modified)
- `services/humanizer/humanizer_response_parser.py` (modified)
- `app/graph/nodes/question_node.py` (modified)
- `domain/contracts/interview_state/base.py` (modified)
- `domain/contracts/question/question.py` (modified)
- `infrastructure/config/settings.py` (modified)
- `infrastructure/config/evaluation.py` (modified — remove `FOLLOW_UP_SCORE_THRESHOLD`)
- `app/settings/constants.py` (modified — remove `MAX_FOLLOW_UPS_PER_INTERVIEW`, `DEFAULT_FOLLOWUP_RATE`)

### Tests

- `tests/services/humanizer/guards/test_follow_up_guard.py` (new)
- `tests/services/humanizer/selector/test_follow_up_selector.py` (new)
- `tests/domain/events/test_follow_up_events.py` (new)
- `tests/graph/nodes/test_question_node_followup.py` (new)
- `tests/graph/nodes/test_question_node_selector.py` (new)
- `tests/services/humanizer/test_humanizer_response_parser.py` (extended)
- `tests/services/humanizer/test_humanizer_service.py` (extended)
- `tests/services/humanizer/builders/test_humanizer_prompt_builder.py` (extended)
- `tests/domain/contracts/test_interview_state.py` (modified — update `test_follow_up_count_invalid`)
- `tests/domain/contracts/test_question.py` (extended)
- `tests/services/question_intelligence/test_production_config.py` (modified — update imports)

### Prompt

- `app/prompts/transformation/humanizer_v2.txt` (modified)

### Configuration

- `infrastructure/config/settings.py` — all 12 follow-up parameters frozen per Section C

### ADRs

- `docs/decisions/adr-010-humanizer-follow-up-system.md` (updated — activation note)
- `docs/decisions/adr-019-follow-up-question-engine.md` (new)
- `docs/decisions/adr-024-follow-up-per-seniority-threshold.md` (new)
- `docs/decisions/adr-025-follow-up-guard-embedding-model.md` (new)

### Documentation

- `docs/architecture/feature-flags.md` (update `humanizer_follow_up_enabled` entry)
- `docs/master-plan/INDEX.md` (update ADR registry entries)

---

## SECTION K — Exit Criteria

The milestone is considered **COMPLETE** if and only if ALL of the following are true:

1. All 25 Acceptance Gates (G01–G25) show **PASS**
2. Total test count ≥ 1427 (baseline) with zero net regressions
3. `pytest` exits with code 0 across full test suite
4. No unresolved `TODO`, `FIXME`, or `HACK` comments in modified files
5. All deliverables listed in Section J exist and are committed
6. No follow-up configuration constant exists outside `infrastructure/config/settings.py`
7. No architectural decision is open or deferred without a filed ADR
8. ADR-019, ADR-024, ADR-025 are filed and in `ACCEPTED` status
9. `docs/architecture/feature-flags.md` reflects `humanizer_follow_up_enabled = True`
10. Implementation team confirms no deviation from ARCH-REVIEW-M1-1 or this document

---

## SECTION L — Final Recommendation

This document constitutes the complete design freeze for V1.1 M1 Follow-up Question Engine.

All architectural decisions are resolved. The required changes (C1–C15 from Audit M1-2) are fully decomposed into component-level specifications, configuration parameters, test requirements, and gate criteria.

**Once all 25 gates pass and all exit criteria are met, the milestone may be closed without further architectural audit.**

The implementation team must not take any new architectural decision during implementation. Any deviation from this document requires a new ADR and approval before merging.
