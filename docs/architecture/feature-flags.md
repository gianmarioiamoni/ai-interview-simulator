# Feature Flags Reference

**Status:** Partially complete — Humanizer flags and state flags documented; Decision Engine flags are stubs
**Owner:** Arch
**SSOT For:** All feature flags, their defaults, locations, and effect
**Update Trigger:** Any flag add/remove/default change
**ADR:** ADR-009, ADR-010

---

## Sections (to fill)

### 1. Flag Inventory

<!-- TODO: Fill from actual codebase scan -->

#### Environment / Settings Flags (`infrastructure/config/settings.py`)

| Flag | Default | Type | Effect |
|---|---|---|---|
| `HUMANIZER_ENABLED` | `True` | bool | Enables the Humanizer subsystem (conversational framing). Propagated to `InterviewState.enable_humanizer` at session start. |
| `HUMANIZER_FOLLOW_UP_ENABLED` | `False` | bool | Enables `FOLLOW_UP` decisions in the policy engine. Requires `HUMANIZER_ENABLED=True`. Disabled by default until V1.1 (score propagation and timing fixes required). |
| `CODING_DOMAIN_PROFILE_ENABLED` | `True` | bool | Enables domain vocabulary profiles in coding QI |
| `CODING_SCENARIO_ANCHOR_ENABLED` | `True` | bool | Enables scenario anchoring in coding questions |
| `CODING_DOMAIN_VOCABULARY_ENABLED` | `True` | bool | Enables domain vocabulary injection |

#### Runtime State Flags (`domain/contracts/interview_state/base.py`)

| Flag | Default | Set By | Effect |
|---|---|---|---|
| `enable_humanizer` | `True` | `settings.humanizer_enabled` via `start.py` | Enables humanizer LLM call for WRITTEN questions |
| `adaptive_interview_enabled` | `False` | `app/ui/state_handlers/start.py` | Enables adaptive navigation path |
| `question_display_text` | `None` | `question_node` | Humanized question text shown to candidate. Falls back to `question.prompt` when `None` (first question, non-WRITTEN, humanizer disabled). Reset to `None` on new session. |

#### Decision Engine Flags (`services/decision_engine/decision_policy.py` `POLICY["global"]`)

| Flag | Default | Effect |
|---|---|---|
| `enable_penalties` | — | Enables score penalty logic |
| `enable_downgrade` | — | Enables hire recommendation downgrade |

### 2. Flag Lifecycle

<!-- TODO: How flags are read, validated, propagated through graph -->

### 3. Adding a New Flag

<!-- TODO: Decision: env-var flag vs state flag vs policy flag -->
<!-- When to use each location -->

### 4. Interaction Matrix

<!-- TODO: Flag combinations and their effects -->
<!-- E.g. adaptive_interview_enabled=True + enable_humanizer=True -->

---

## Cross-References

- `configuration.md` — env var flags detail
- ADR-009 — adaptive interview flag rationale
- ADR-010 — humanizer flag rationale
- `runtime-flow.md` — where flags are consumed in graph
