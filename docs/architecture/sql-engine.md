# SQL Engine Architecture

## Purpose

The SQL subsystem is responsible for:

- **SQL question generation** — producing well-formed, executable SQL interview questions grounded in a specific business schema.
- **SQL schema management** — maintaining a registry of curated `SchemaDefinition` objects, one per supported `BusinessContext`.
- **SQL execution** — building temporary SQLite databases from question-embedded schema and seed data, then executing candidate SQL.
- **SQL evaluation** — comparing candidate execution results against expected results, independent of the originating business context.

Subsystem boundaries:

- The SQL subsystem owns schema definitions, question generation, execution, and evaluation.
- It does **not** own `BusinessContext` resolution — that is resolved upstream by the interview pipeline before SQL generation begins.
- It does **not** own candidate session state or scoring aggregation.

---

## High-Level Architecture

```
BusinessContext
      ↓
SchemaRegistry
      ↓
SchemaDefinition
      ↓
SQLDatabase
      ↓
SQLQuestionGenerator
      ↓
Question
      ↓
SQLExecutor
      ↓
SQLEvaluator
```

---

## Core Components

### SchemaRegistry

Responsibilities:

- Lookup a `SchemaDefinition` by `BusinessContext`.
- Map each supported context to its canonical schema.
- Return the `GENERIC` schema when context is unknown or unsupported (default fallback).

Supported contexts:

| Context      | Description                          |
|--------------|--------------------------------------|
| `GENERIC`    | Neutral multi-domain schema          |
| `FINTECH`    | Financial transactions, accounts     |
| `ECOMMERCE`  | Orders, products, customers          |
| `SAAS`       | Subscriptions, usage, tenants        |
| `HEALTHCARE` | Patients, appointments, records      |

`SchemaRegistry` is the single source of truth for all schema definitions.

---

### SchemaDefinition

A `SchemaDefinition` is the complete specification for a single business context schema.

| Field            | Type     | Purpose                                                                 |
|------------------|----------|-------------------------------------------------------------------------|
| `context_key`    | `str`    | Identifier matching the `BusinessContext` enum value.                   |
| `schema_sql`     | `str`    | DDL statements that create all tables for this context.                 |
| `seed_sql`       | `str`    | DML statements that populate tables with realistic sample data.         |
| `summary_hint`   | `str`    | Human-readable description of the schema, surfaced in prompts and UI.  |
| `domain_tags`    | `list`   | Keywords describing SQL topics covered (e.g. `joins`, `aggregations`). |
| `vocabulary_hint`| `str`    | Domain-specific terminology used in question phrasing.                  |

---

### SQLDatabase

Responsibilities:

- Build a temporary, in-memory SQLite database from `schema_sql` and `seed_sql`.
- Expose the raw `schema_sql` and `seed_sql` for stamping onto generated `Question` objects.
- Provide fresh execution connections to `SQLExecutor`.

`SQLDatabase` is composed, not inherited. It accepts a `SchemaDefinition` and produces a ready-to-query database handle.

---

## Question Generation Architecture

```
SQLQuestionPipeline
       ↓
SQLQuestionGenerator
       ↓
SQLPromptBuilder
       ↓
LLM
       ↓
SQLResponseParser
       ↓
Question (with db_schema, db_seed_data, expected_sql)
```

- `SQLQuestionPipeline` — orchestrates context resolution, schema lookup, and generation dispatch.
- `SQLQuestionGenerator` — selects generation strategy based on `BusinessContext`; delegates to prompt and parser.
- `SQLPromptBuilder` — constructs the LLM prompt from `SchemaDefinition` fields; strategy-dependent.
- `SQLResponseParser` — extracts and validates the structured question, expected SQL, and metadata from LLM output.

---

## Generation Strategies

### GENERIC Context

```
retrieval
    ↓
enrichment
    ↓
validation
    ↓
question
```

The GENERIC path performs **retrieval-augmented enrichment**: relevant SQL concepts are retrieved from the question corpus to diversify question phrasing and topic coverage. Enrichment is applied because GENERIC schemas have no domain anchor — corpus retrieval substitutes for domain specificity, improving question variety and depth.

---

### FINTECH / ECOMMERCE / SAAS / HEALTHCARE

```
retrieval
    ↓
metadata extraction
    ↓
generation
    ↓
validation
    ↓
question
```

Domain-specific contexts use **metadata-only generation**: the LLM is instructed using extracted metadata fields only, not corpus seed text. The following fields drive generation:

| Field              | Role                                                        |
|--------------------|-------------------------------------------------------------|
| `domains`          | Constrains which SQL topic areas the question must target.  |
| `difficulty_label` | Controls complexity of joins, subqueries, and aggregations. |
| `scenario_anchor`  | Pins the question narrative to a realistic business event.  |

Corpus seed text is intentionally excluded for domain-specific contexts to prevent cross-schema contamination — a `FINTECH` question must not carry vocabulary or table references from `ECOMMERCE` schemas encountered in retrieved corpus chunks.

---

## Schema Consistency Model

A single `SchemaDefinition` must be the sole source of truth across all phases. The following invariant applies:

| Phase                  | Source                          |
|------------------------|---------------------------------|
| Schema summary in UI   | `summary_hint`                  |
| Vocabulary in prompt   | `vocabulary_hint`               |
| Prompt generation      | `schema_sql` + `summary_hint`   |
| Executable validation  | `schema_sql` + `seed_sql`       |
| `db_schema` stamping   | `schema_sql`                    |
| `db_seed_data` stamping| `seed_sql`                      |

All phases read from the same `SchemaDefinition` instance. Divergence between prompt schema and execution schema is a hard invariant violation.

---

## Runtime Execution

Generated `Question` objects carry two schema fields:

- `db_schema` — the full DDL (`schema_sql`) of the originating `SchemaDefinition`.
- `db_seed_data` — the full DML (`seed_sql`) of the originating `SchemaDefinition`.

**`SQLExecutor` must build its execution database exclusively from `Question.db_schema` and `Question.db_seed_data`.**

`SQLExecutor` has no dependency on `SchemaRegistry` at execution time. This design ensures:

- Questions are portable and self-contained.
- Execution is reproducible regardless of registry state.
- Schema can be evolved without breaking previously generated questions.

---

## Evaluation Flow

```
candidate SQL
     ↓
SQLExecutor (builds db from Question.db_schema + Question.db_seed_data)
     ↓
execution result (rows, columns, error)
     ↓
SQLEvaluator (compares against expected result)
     ↓
EvaluationResult
```

`SQLEvaluator` receives only the execution result and the expected result derived from `Question.expected_sql`. It has no dependency on `BusinessContext` or `SchemaRegistry`. Evaluation correctness is determined entirely by result set equivalence, independent of domain.

---

## Candidate Experience

| Element          | Visibility | Source                  |
|------------------|------------|-------------------------|
| Schema (DDL)     | Visible    | `Question.db_schema`    |
| Seed data (DML)  | Hidden     | `Question.db_seed_data` |
| Question prompt  | Visible    | `Question.question_text`|

Rationale:

- The candidate must understand the table structure to write correct SQL — `db_schema` is always rendered in the UI.
- Seed data is hidden to prevent candidates from reverse-engineering the expected result by reading the data rows directly.
- The candidate works exclusively against the schema embedded in the question — no external schema reference is required or permitted.

---

## Adding a New SQL Context

1. **Create `SchemaDefinition`** — define `context_key`, `schema_sql`, `seed_sql`, `summary_hint`, `domain_tags`, `vocabulary_hint`.
2. **Add seed data** — populate `seed_sql` with realistic, domain-appropriate rows covering all expected query patterns.
3. **Register in `SchemaRegistry`** — map the new `BusinessContext` enum value to the new `SchemaDefinition`.
4. **Add vocabulary hints** — populate `vocabulary_hint` with domain-specific terms used in question phrasing.
5. **Add domain tags** — populate `domain_tags` with SQL topic labels appropriate for the context.
6. **Add tests** — required test categories:
   - Schema DDL executes without errors.
   - Seed DML executes without errors.
   - Registry lookup returns the correct `SchemaDefinition`.
   - Question generation produces valid SQL for the new context.
   - `SQLExecutor` executes candidate SQL against the new schema.
   - `SQLEvaluator` correctly scores correct and incorrect answers.
7. **Add documentation** — update `SchemaRegistry` reference table in this document.

---

## Architectural Invariants

- `SchemaRegistry` is the single source of truth for all schema definitions.
- A `GENERIC` schema must always exist; it is the fallback for unknown contexts.
- Unknown or unsupported `BusinessContext` values resolve to `GENERIC` — they never raise errors at registry lookup.
- `SQLExecutor` never reads `SchemaRegistry`; it reads only from the `Question` object.
- Every `Question` carries its full runtime schema (`db_schema`, `db_seed_data`).
- Prompt generation and execution must derive from the same `SchemaDefinition` instance.
- Candidate-visible schema (`db_schema`) must exactly match the schema used during execution.
- `BusinessContext` is resolved before SQL generation begins; it must not be resolved lazily inside the SQL subsystem.
- Divergence between prompt schema and execution schema is a hard invariant violation that must be caught in tests.

---

## Known Constraints

- **SQLite execution engine** — all execution and validation uses SQLite. SQL dialects specific to PostgreSQL, MySQL, or BigQuery are not supported in execution.
- **Single schema per question** — each question is generated and executed against exactly one `SchemaDefinition`; multi-schema joins across contexts are not supported.
- **Limited number of curated schemas** — the registry contains a small, fixed set of well-tested schemas rather than a large dynamic library.
- **Schema quality over quantity** — the platform deliberately maintains a small number of schemas. This keeps validation, execution, evaluation, and maintenance predictable, and ensures each schema is thoroughly tested before use in production question generation.

---

## Future Extensions

- Additional `BusinessContext` schemas may be added by following the checklist in [Adding a New SQL Context](#adding-a-new-sql-context).
- Schema enrichment improvements — richer `vocabulary_hint` and `domain_tags` to improve LLM prompt specificity.
- JavaScript execution support is **out of scope** for the SQL subsystem.

---

## Related Documents

- [`docs/architecture/question-intelligence.md`](question-intelligence.md) — question generation pipeline architecture.
- [`docs/architecture/business-context.md`](business-context.md) — `BusinessContext` resolution and profile system.
- [`docs/decisions/adr-004-hybrid-question-intelligence.md`](../decisions/adr-004-hybrid-question-intelligence.md) — ADR-004: Hybrid Question Intelligence.
- [`docs/decisions/adr-006-business-context-profiles.md`](../decisions/adr-006-business-context-profiles.md) — ADR-006: Business Context Profiles.
