# Question Intelligence Architecture

**Owner:** Services
**SSOT For:** Pipelines, registries, retrieval strategy, question generation
**Update Trigger:** Any change in `services/question_intelligence/` or `services/question_corpus/retrieval/`
**ADR:** ADR-004, ADR-005, ADR-006

---

## Purpose

Question Intelligence is responsible for:

- Selecting and delivering one `Question` per interview area per turn
- Choosing between corpus retrieval (Chroma), LLM enrichment, and pure LLM generation based on area and `BusinessContext`
- Enforcing deduplication, difficulty balance, session variety, and theme coherence across retrieved and generated questions
- Exposing a `BusinessContext`-aware generation path for SQL and Coding areas through domain-scoped registries

---

## High-Level Architecture

```
QuestionIntelligenceProvider          ← composition root; wires all dependencies
├── LazyAdaptiveInterviewService      ← per-turn lazy question generation
│   └── AreaQuestionBuilder           ← area → pipeline dispatch
│       ├── WrittenQuestionPipeline   ← HR + most TECH areas
│       ├── CodingQuestionPipeline    ← TECH_CODING (extends BaseLLMQuestionPipeline)
│       └── SQLQuestionPipeline       ← TECH_DATABASE (extends BaseLLMQuestionPipeline)
└── QuestionSetBuilder                ← batch full-interview generation (non-adaptive path)
    └── AreaQuestionBuilder           ← same builder, different consumer
```

`BaseLLMQuestionPipeline` is the shared scaffold for `CodingQuestionPipeline` and `SQLQuestionPipeline`. It owns the `retrieve → enrich → generate → memory-update` loop. Subclasses implement only retrieval, enrichment, generation, and labelling hooks.

---

## Pipeline Types

### WrittenQuestionPipeline

| Aspect | Detail |
|---|---|
| **Areas** | All `InterviewArea` values except `TECH_CODING` and `TECH_DATABASE` |
| **Retrieval** | `QuestionRetrievalService` → Chroma similarity search with strategy-resolved filters |
| **Generation** | `QuestionGenerator` (LLM) fills remaining slots after corpus exhaustion |
| **Enrichment** | None — bank items mapped directly via `WrittenQuestionMapper` |
| **Post-processing** | `WrittenDifficultyBalancer` selects final set from combined pool |
| **corpus_quota** | Caps corpus contribution; remaining slots forced to LLM generation |

### CodingQuestionPipeline

| Aspect | Detail |
|---|---|
| **Area** | `TECH_CODING` only |
| **Retrieval** | `CodingPipelineRetrievalHelper` — staged filter relaxation via `AdaptiveRetrievalPolicy`; min pool = 3 |
| **Actionability filter** | Skips items not matching `_ACTIONABLE_CODING_PATTERN` (implement / write function / algorithm / leetcode) |
| **Enrichment** | `CodingQuestionGenerator.enrich_from_prompt()` — LLM rewrites seed prompt into structured `GeneratedCodingQuestion` |
| **Generation** | `CodingQuestionGenerator.generate()` with retry; factory resolves domain-scoped generator per `BusinessContext` |
| **Alignment guard** | Validates `entrypoint` and all `parameters` appear in prompt; rejects on mismatch |
| **Output** | `Question(type=CODING)` with `coding_spec`, `visible_tests`, `function_name` |

### SQLQuestionPipeline

| Aspect | Detail |
|---|---|
| **Area** | `TECH_DATABASE` only |
| **Retrieval** | `SqlPipelineRetrievalHelper` — staged filter relaxation; fetch_k = target × 5; min pool = 3 |
| **Actionability filter** | Applied only for `GENERIC` context; skips items not matching `_ACTIONABLE_SQL_PATTERN` |
| **Enrichment (GENERIC)** | `SQLQuestionGenerator.enrich_from_prompt()` — LLM rewrites seed into SQL question with schema |
| **Enrichment (non-GENERIC)** | Metadata-only path: `domains`, `difficulty_label`, `scenario_anchor` passed to generator; seed text discarded |
| **Generation** | `SQLQuestionGenerator.generate()` with retry; factory resolves schema-scoped generator per `BusinessContext` |
| **Output** | `Question(type=SQL)` with `db_schema`, `db_seed_data` |

---

## Retrieval Layer

### AdaptiveRetrievalService

- Used by `WrittenQuestionPipeline` (via `QuestionRetrievalService`) and indirectly by the pipeline retrieval helpers
- Executes staged filter relaxation: strict filters first, progressively relaxed until `min_pool_size` is met
- Applies `CoveragePenaltyEngine` → `WeakDomainBoostEngine` → `PerformanceResponsiveCandidateSelector` in sequence
- `technical_background` area on fresh-start session requires `min_pool_size = 5`

### QuestionBankItem

Corpus record returned from Chroma. Key fields consumed by pipelines:

| Field | Used By |
|---|---|
| `text` | Actionability filter + enrichment seed (GENERIC SQL/Coding only) |
| `domains` | `WrittenQuestionMapper`, SQL metadata-only generation |
| `difficulty` | `map_corpus_difficulty()` → `Question.difficulty` |
| `expected_topics` | SQL enrichment |
| `provenance` | `_build_enrichment_provenance()` in base pipeline |
| `ingestion_metadata` | Fallback provenance fields |

### Retrieval Filters & Relaxation

`AdaptiveRetrievalPolicy.build_relaxation_stages()` generates a list of filter dictionaries. The retrieval helper iterates them, merging unique candidates until the pool threshold is met. Stages progressively drop constraints (level, interview_type, area) to avoid empty results.

### Difficulty Handling

`map_corpus_difficulty(int | None) → DifficultyLevel` translates raw Chroma integer difficulty into the domain enum. Used by all three pipelines for provenance and question construction.

### Domain Handling (TD-006)

`domains=[area.value]` is a temporary mapper pattern: area value is used as domain label. This conflates `InterviewArea` with domain taxonomy. See `technical-debt-register.md` TD-006.

---

## BusinessContext Integration

`BusinessContext` is resolved once at interview start and passed through the entire pipeline chain as an optional parameter.

| Context | SQL Generator | Coding Generator |
|---|---|---|
| `GENERIC` | Default `SQLQuestionGenerator` (no schema override) | Default `CodingQuestionGenerator` (no profile) |
| `FINTECH` | Schema-scoped generator from `SchemaRegistry.get(FINTECH)` | Profile-scoped generator from `CodingDomainProfileRegistry.get(FINTECH)` |
| `ECOMMERCE` | Schema-scoped from `SchemaRegistry.get(ECOMMERCE)` | Profile-scoped from `CodingDomainProfileRegistry.get(ECOMMERCE)` |
| `SAAS` | Schema-scoped from `SchemaRegistry.get(SAAS)` | Profile-scoped from `CodingDomainProfileRegistry.get(SAAS)` |
| `HEALTHCARE` | Schema-scoped from `SchemaRegistry.get(HEALTHCARE)` | Profile-scoped from `CodingDomainProfileRegistry.get(HEALTHCARE)` |

### CodingDomainProfileRegistry

- `services/question_intelligence/coding_domain_profile_registry.py`
- Returns a `CodingDomainProfile` frozen dataclass for a given `BusinessContext`
- Falls back to `_GENERIC_PROFILE` for unregistered contexts
- Generators are cached by `BusinessContext` after first construction in `_build_coding_generator_factory()`

`CodingDomainProfile` fields:

| Field | Effect |
|---|---|
| `context_summary` | Injected into prompt as domain framing |
| `vocabulary_hint` | Domain-specific technical terms for prompt enrichment |
| `entity_hint` | Domain entities (account, patient, cart…) used in problem framing |
| `scenario_anchor_pool` | Pool of scenario types; one picked per question |
| `test_scenario_hints` | Hints for hidden-test generation |

### SchemaRegistry

- `services/sql_engine/schema_registry.py`
- Returns full SQL schema definition string for a given `BusinessContext`
- Injected into `SQLQuestionGenerator` constructor; schema appears in all generated questions as `db_schema` and `db_seed_data`

---

## SQL Path

### GENERIC context

```
Retrieval (Chroma)
  → actionability filter (_ACTIONABLE_SQL_PATTERN)
  → enrich_from_prompt(seed_text, domains, difficulty_label, expected_topics)
  → Question(db_schema=default_schema, db_seed_data=default_seed)
```

Fallback if no corpus hit or enrichment fails:

```
SQLQuestionGenerator.generate(role, level, n)
  → Question(db_schema=default_schema, db_seed_data=default_seed)
```

### Non-GENERIC contexts (FINTECH, ECOMMERCE, SAAS, HEALTHCARE)

```
Retrieval (Chroma) — metadata only consumed
  → extract: domains, difficulty_label
  → pick: scenario_anchor from ScenarioAnchor enum
  → generator.generate(domains, difficulty_label, scenario_anchor, ...)
  → Question(db_schema=context_schema, db_seed_data=context_seed)
```

**Why seed text is not used for non-GENERIC:** Generic corpus questions reference generic schema (employees, orders). Non-GENERIC business contexts require schema-coherent questions. The corpus seed would produce schema-incoherent SQL. Metadata (difficulty, domain tags) carries reusable signal without the wrong schema dependency.

**Key generation parameters:**

| Parameter | Source |
|---|---|
| `domains` | `item.domains` from retrieved `QuestionBankItem` |
| `difficulty_label` | `map_corpus_difficulty(item.difficulty).value` |
| `scenario_anchor` | Random pick from `ScenarioAnchor` enum |

---

## Coding Path

### Retrieval → Enrichment flow

```
Retrieval (Chroma, TECH_CODING area)
  → actionability filter (implement / write function / algorithm / leetcode)
  → enrich_from_prompt(seed_prompt, role, level, theme_guidance, job_description, company_description)
  → alignment validation (entrypoint + all parameters must appear in prompt)
  → Question(type=CODING, coding_spec, visible_tests, function_name)
```

### BusinessContext influence on Coding

The `CodingDomainProfile` is injected into `CodingQuestionGenerator` at construction time. It injects:

- `context_summary` into the generation prompt as domain framing text
- `vocabulary_hint` to steer generated algorithm topics
- `entity_hint` to steer generated data structures
- `scenario_anchor_pool` to provide a domain-appropriate problem scenario
- `test_scenario_hints` to guide hidden-test generation

### Hidden-test integration

Visible tests (`visible_tests`) are part of the generated `GeneratedCodingQuestion`. The execution engine (`services/coding_engine/`) generates hidden tests at runtime using `Question.coding_spec`. `test_scenario_hints` from the profile indirectly influence hidden-test diversity.

---

## Runtime Flow

```
1. Area selection
   LazyAdaptiveInterviewService.resolve_planned_areas(interview_type)
   → order_areas_by_derived_difficulty(interview_type.get_areas())
   → returns ordered [InterviewArea]

2. Theme anchor
   InterviewThemeSelector.select_anchor(role, level, first_area)
   → stored in InterviewRetrievalMemory

3. Retrieval query
   RetrievalQueryBuilder.build(role, level, area, theme_anchor, memory)
   → string query for Chroma similarity search

4. Retrieval strategy
   RetrievalStrategyResolver.resolve(area, level, questions_per_area)
   → RetrievalStrategy with filters and scan_k

5. Pipeline dispatch (AreaQuestionBuilder.build)
   TECH_CODING  → CodingQuestionPipeline.build()
   TECH_DATABASE → SQLQuestionPipeline.build()
   else          → WrittenQuestionPipeline.build()

6. Pipeline execution (BaseLLMQuestionPipeline or WrittenQuestionPipeline)
   retrieve_candidates()
   for each item:
     enrich_item() → Question or None
   generate_with_retry(remaining_slots)
   balancer/selection → final Question list

7. Memory update
   InterviewMemoryUpdater.record_bank_item_selection(memory, bank_item)
   → prevents repetition in subsequent areas

8. Return
   (List[Question], InterviewRetrievalMemory)
   → consumed by LangGraph question_node
```

---

## Extension Points

### Adding a new BusinessContext

1. Add value to `domain/contracts/interview/business_context.py` (`BusinessContext` enum)
2. Add SQL schema: `services/sql_engine/schema_registry.py` — add `SchemaRegistry.get(NEW_CONTEXT)` branch
3. Add coding profile: `services/question_intelligence/coding_domain_profile_registry.py` — define `_NEW_PROFILE` and add to `_REGISTRY`
4. No changes needed in pipelines — factory pattern handles routing automatically

### Adding a new SQL schema

- Edit `services/sql_engine/schema_registry.py`
- `SchemaRegistry.get(context)` must return a schema definition string consumable by `SQLQuestionGenerator`

### Adding a new CodingDomainProfile

- Edit `services/question_intelligence/coding_domain_profile_registry.py`
- Instantiate `CodingDomainProfile(context_key=NEW_CONTEXT, ...)` and register in `_REGISTRY`

### Adding a new QuestionPipeline

1. Create `services/question_intelligence/pipelines/<name>_question_pipeline.py`
2. Subclass `BaseLLMQuestionPipeline`
3. Implement all abstract methods: `_pipeline_label`, `_candidate_scan_k`, `_retrieve_candidates`, `_enrich_item`, `_generate_with_retry`, `_build_provenance_model_tag`
4. Add dispatch branch in `AreaQuestionBuilder.build()` keyed on `InterviewArea`
5. Wire generator and retrieval helper in `QuestionIntelligenceProvider.__init__()`
6. Add `InterviewArea` value if a new area is introduced

---

## Architectural Invariants

- `Question` is the sole runtime contract between QI and the graph. No pipeline-internal type crosses the boundary.
- SQL execution consumes only `Question.db_schema` and `Question.db_seed_data`. Pipelines are responsible for populating these fields correctly before returning.
- `BusinessContext` is resolved once at interview start by the graph entry node. Pipelines receive it as a parameter and must not re-resolve it.
- `CodingDomainProfileRegistry` and `SchemaRegistry` are the single sources of truth for business-context-specific generation parameters. No hardcoded context logic belongs in pipeline code.
- Pipelines own generation strategy selection. The caller (`AreaQuestionBuilder`) dispatches by area only; it does not inspect question content.
- `InterviewRetrievalMemory` is immutable across calls — every update returns a new instance. Pipelines must propagate the returned memory, not mutate the input.
- Corpus retrieval always precedes generation. Generation fills remaining slots only. A pipeline must never bypass retrieval unless the corpus is empty.
- Enrichment failures are silent at item level (`None` returned). The pipeline continues to next candidate. Generation is the final fallback.

---

## Related Documents

- `docs/architecture/ingestion.md` — upstream corpus build and adapter pipeline
- `docs/decisions/adr-004-hybrid-question-intelligence.md` — rationale for hybrid QI approach
- `docs/decisions/adr-005-dual-embedding-strategy.md` — embedding model split
- `docs/decisions/adr-006-business-context-profiles.md` — parallel registry rationale
- `docs/decisions/adr-009-adaptive-interview-path.md` — lazy adaptive service rationale
- `docs/technical-debt-register.md` — TD-001, TD-002, TD-005, TD-006, TD-007
- `services/sql_engine/` — SQL execution engine (consumes `Question.db_schema`)
- `services/coding_engine/` — coding execution engine (consumes `Question.coding_spec`)
