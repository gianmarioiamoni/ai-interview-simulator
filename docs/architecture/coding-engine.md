# Coding Interview Subsystem Architecture

## Purpose

The Coding subsystem generates, executes, and evaluates algorithmic coding questions within the interview pipeline. It is responsible for:

- **Coding question generation** — producing domain-framed algorithmic problems calibrated to role and seniority level.
- **Hidden test generation** — generating edge-case test cases via LLM, driven by `CodingSpec` and optional domain hints.
- **Code execution** — running candidate-submitted Python code against visible and hidden test cases in a sandboxed environment.
- **Code evaluation** — producing a structured `ExecutionResult` consumed by the evaluation graph node.

The Coding subsystem is bounded by:
- **Input**: `BusinessContext`, `RoleType`, `SeniorityLevel`, optional JD/company description.
- **Output**: `Question` (with `CodingSpec`, visible tests, hidden tests), `ExecutionResult`.

It does not perform scoring or feedback generation; those are responsibilities of the evaluation pipeline.

---

## High-Level Architecture

```
BusinessContext
      ↓
CodingDomainProfileRegistry
      ↓
CodingDomainProfile
      ↓
CodingQuestionGenerator
      ↓
Question
      ↓
AITestGenerator
      ↓
ExecutionEngine
      ↓
Evaluator
```

---

## Core Components

### CodingDomainProfileRegistry

**Responsibilities:**
- Single source of truth for `BusinessContext` → `CodingDomainProfile` resolution.
- Profile lookup via `get(business_context: BusinessContext) → CodingDomainProfile`.
- Provides a `GENERIC` fallback when no context-specific profile is registered.

**Supported contexts:**

| Context      | Description                                              |
|--------------|----------------------------------------------------------|
| `GENERIC`    | Algorithm-first; no domain framing.                     |
| `FINTECH`    | Payments, transactions, ledgers, fraud, risk.            |
| `ECOMMERCE`  | Products, orders, inventory, pricing, fulfillment.       |
| `SAAS`       | Subscriptions, tenants, billing, quotas, feature gates.  |
| `HEALTHCARE` | Patients, appointments, clinical workflows, EHR/FHIR.   |

`CodingDomainProfileRegistry` is the sole registration point. No other component resolves `BusinessContext` for Coding purposes.

---

### CodingDomainProfile

Immutable dataclass (`frozen=True`) carrying context-specific generation assets.

| Field                  | Type               | Purpose                                                                 |
|------------------------|--------------------|-------------------------------------------------------------------------|
| `context_key`          | `BusinessContext`  | Registry identity key.                                                  |
| `context_summary`      | `str \| None`      | Mandatory framing block injected into the generation prompt. Controls narrative tone. `None` for GENERIC. |
| `vocabulary_hint`      | `tuple[str, ...]`  | Domain terms the LLM should incorporate naturally where appropriate.    |
| `entity_hint`          | `tuple[str, ...]`  | Domain entity names. **Not consumed by prompt builders.** Reserved for future use. |
| `scenario_anchor_pool` | `tuple[str, ...]`  | Pool of scenario anchors; one is sampled randomly per generation call.  |
| `test_scenario_hints`  | `tuple[str, ...]`  | Edge-case hints propagated to `TestPromptBuilder` for hidden test generation. |

> **`entity_hint` — known constraint**: This field is defined on the profile but is not injected into any prompt builder. It is available for future prompt strategies that require explicit entity grounding.

---

### CodingQuestionGenerator

**Responsibilities:**
- Accepts `RoleType`, `SeniorityLevel`, optional context signals (theme, JD, company description).
- Delegates prompt assembly to `CodingPromptBuilder`.
- Delegates LLM invocation and JSON parsing to `CodingResponseParser`.
- Returns `List[GeneratedCodingQuestion]` (generation mode) or `GeneratedCodingQuestion | None` (enrichment mode).

**Entry points:**
- `generate(role, level, n, ...)` — net-new question generation.
- `enrich_from_prompt(seed_prompt, role, level, ...)` — enriches a corpus-sourced seed into a full structured question.

---

### CodingPromptBuilder

**Responsibilities:**
- Loads generation and enrichment prompt templates via `PromptLoader`.
- Assembles template variables including domain-specific blocks from `CodingDomainProfile`.
- Owns the JSON output contract injected into every prompt.

**Injected blocks (feature-flag controlled):**

| Block                   | Feature Flag                        | Source                          |
|-------------------------|-------------------------------------|---------------------------------|
| `domain_framing_block`  | `coding_domain_profile_enabled`     | `profile.context_summary`       |
| `vocabulary_block`      | `coding_domain_vocabulary_enabled`  | `profile.vocabulary_hint`       |
| `scenario_block`        | `coding_scenario_anchor_enabled`    | `profile.scenario_anchor_pool`  |

All three blocks emit empty strings when their respective flags are disabled or the profile provides no content.

---

## Question Generation Flow

```
BusinessContext
      ↓
CodingDomainProfileRegistry.get(context)
      ↓
CodingDomainProfile
      ↓
CodingQuestionGenerator(llm, domain_profile)
      ↓
CodingPromptBuilder.build_generation_prompt(role, level, n, ...)
      ↓
LLM (structured JSON output)
      ↓
CodingResponseParser.invoke_and_parse(...)
      ↓
List[GeneratedCodingQuestion]  →  Question
```

---

## BusinessContext Integration

Three distinct prompt blocks carry `BusinessContext` influence into the LLM:

- **`domain_framing_block`** — mandatory narrative frame drawn from `context_summary`. Instructs the LLM to frame the problem in the target domain (e.g., "financial services context: payments, fraud detection").
- **`vocabulary_block`** — domain-specific terminology drawn from `vocabulary_hint`. Applied with the directive "incorporate where natural — do not force".
- **`scenario_block`** — a single randomly-sampled scenario anchor from `scenario_anchor_pool`. Provides a concrete algorithmic scenario (e.g., "fraud detection", "inventory restock").

**Influence hierarchy:**

1. `role` and `level` are **dominant signals**. They control difficulty, complexity, and expected solution sophistication.
2. `BusinessContext` modifies **narrative framing and vocabulary** only.
3. `BusinessContext` **does not modify difficulty**. A FINTECH question for a Junior engineer must remain Junior-calibrated.
4. `job_description` and `company_description`, when present, are treated as supplementary guidance with explicit prompt directives to not override domain or difficulty.

---

## Hidden Test Generation

```
Question (with CodingSpec)
      ↓
BusinessContext  →  CodingDomainProfileRegistry.get(context)
      ↓
CodingDomainProfile.test_scenario_hints
      ↓
AITestGenerator.generate_tests(question, num_tests, domain_profile)
      ↓
TestPromptBuilder.build(problem, spec, num_tests, domain_profile)
      ↓
LLM
      ↓
TestResponseParser.invoke_and_parse(...)
      ↓
List[CodingTestCase]  (hidden tests)
```

**`test_scenario_hints` semantics:**

These are edge-case orientations specific to the domain (e.g., FINTECH: `"zero balance"`, `"duplicate transaction"`). They are injected into the test generation prompt as preferred edge cases, not mandatory ones. The LLM incorporates them where applicable to the problem structure.

**Runtime propagation path:**

`AITestGenerator.generate_tests` accepts `domain_profile` as an optional argument. The caller (graph node or service orchestrator) is responsible for resolving and passing the profile. `TestPromptBuilder._domain_hints_block` constructs the prompt block from `domain_profile.test_scenario_hints`; it emits an empty string when `domain_profile` is `None` or `test_scenario_hints` is empty.

**Cache and diversity filtering:**

`AITestGenerator` applies a `TestCacheService` to avoid redundant LLM calls for identical question/count pairs, and a `TestDiversityFilter` to select a diverse subset from the over-generated pool.

**Fallback:**

If LLM generation fails after all retry attempts, `AITestGenerator` emits a minimal static test set derived from `CodingSpec.parameters` to guarantee executability.

---

## Execution Architecture

```
candidate code (str)
      ↓
ExecutionEngine.execute(question, user_answer)
      ↓
CodingExecutor.execute(question, user_code)
      ├── TestCaseAdapter  →  convert hidden_tests to CodingTestCase list
      ├── TestCaseRunner.build_harness(user_code, visible_tests, hidden_tests, function_name, coding_spec)
      └── ExecutionSandbox.execute(harness)
            ↓
      HarnessOutputParser.parse(question_id, raw)
            ↓
      ExecutionResult
```

**Separation of concerns:**

- `ExecutionEngine` is the entry point dispatcher; it delegates to `CodingExecutor` for `QuestionType.CODING` and to `SQLExecutor` for `QuestionType.DATABASE`.
- `CodingExecutor` is stateless and does not know about `BusinessContext`. Execution logic is context-independent.
- `ExecutionSandbox` runs the harness in a subprocess with timeout enforcement.
- `HarnessOutputParser` interprets `__RESULT__` sentinel lines in stdout to produce a structured `ExecutionResult` without coupling to sandbox internals.

**Status outcomes:**
- `TIMEOUT` — sandbox wall-clock limit exceeded.
- `RUNTIME_ERROR` — non-zero exit code before any `__RESULT__` sentinel.
- `PASS` / `FAIL` — derived from parsed harness output.

---

## Programming Language Strategy

**Current state:** Python only.

**Rationale:**

- **Execution reliability** — a single execution harness covers all question types. No multi-runtime orchestration is required.
- **Deterministic testing** — Python's `subprocess`-based sandbox is predictable and controllable.
- **Maintenance cost** — each supported language requires its own harness, validator, and test generator compatibility layer.

**Invariant:** All generated coding questions must be executable in Python. `CodingSpec.entrypoint` always refers to a Python-callable identifier.

---

## Future Language Expansion

JavaScript support (or any additional language) would require:

1. A dedicated execution harness for the target runtime.
2. A language-specific validator within `TestCaseRunner`.
3. Test generator compatibility in `AITestGenerator` (prompt and parser adaptation).
4. Evaluator compatibility in `HarnessOutputParser`.
5. Runtime isolation scoped to the new language.

No language expansion is approved or scheduled. This checklist documents the minimum extension surface.

---

## Adding a New BusinessContext

1. Define a new `CodingDomainProfile` with appropriate `context_summary`, `vocabulary_hint`, `scenario_anchor_pool`, and `test_scenario_hints`.
2. Register the profile in `_REGISTRY` in `coding_domain_profile_registry.py`.
3. Populate `vocabulary_hint` with domain-specific terms (≥ 8 terms recommended).
4. Populate `scenario_anchor_pool` with ≥ 5 concrete algorithmic scenarios.
5. Populate `test_scenario_hints` with ≥ 4 domain-relevant edge cases.
6. Add unit tests covering profile lookup, prompt block injection, and hint propagation.
7. Update `ARCHITECTURE-INDEX.md` and this document's supported-contexts table.

---

## Architectural Invariants

- `CodingDomainProfileRegistry` is the single source of truth for `BusinessContext` → `CodingDomainProfile` resolution.
- `BusinessContext` is resolved once per interview session before question generation begins.
- `RoleType` and `SeniorityLevel` are the dominant difficulty signals. `BusinessContext` does not modify calibration.
- `BusinessContext` affects narrative framing only; it does not influence grading criteria or pass/fail thresholds.
- Hidden tests must remain executable Python regardless of domain context.
- `ExecutionEngine` and `CodingExecutor` are context-independent. No `BusinessContext` reference enters the execution path.
- Python is the only supported execution language. Questions generating non-Python solutions are invalid.
- `entity_hint` is defined but not consumed. Do not rely on it in prompt builders without explicit architectural approval.

---

## Known Constraints

- **Python-only execution** — no multi-language support; adding a language requires a new harness and compatibility layer.
- **LLM-generated questions** — question quality is bounded by LLM capability and prompt specificity. No deterministic fallback exists for generation failure beyond empty output.
- **BusinessContext influences narrative only** — framing changes do not guarantee domain-accurate test structures; `test_scenario_hints` provides guidance, not constraints.
- **Hidden tests are generic execution artifacts** — they are structurally Python `(args, expected)` pairs and carry no domain metadata into the execution sandbox.
- **`entity_hint` is unused** — the field exists on `CodingDomainProfile` but is not injected into any prompt template.

---

## Related Documents

- [`question-intelligence.md`](question-intelligence.md) — overall question intelligence architecture covering all question types.
- [`business-context.md`](business-context.md) — `BusinessContext` contract, resolution, and influence model.
- [ADR-004](../decisions/adr-004-hybrid-question-intelligence.md) — hybrid question intelligence strategy.
- [ADR-006](../decisions/adr-006-business-context-profiles.md) — business context profiles design decision.
