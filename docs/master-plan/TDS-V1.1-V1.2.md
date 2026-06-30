# Technical Design Specification — AI Interview Simulator V1.1 / V1.2

**Version:** 1.1  
**Date:** 2026-06-30  
**Status:** V1.1 M1 Frozen — Architecture Baseline  
**Authors:** Engineering Team  
**Supersedes:** ADRs 001–015 (V1.0 era)

---

## Table of Contents

1. [Current Architecture Overview](#1-current-architecture-overview)
2. [Target Architecture (V1.2 End State)](#2-target-architecture-v12-end-state)
3. [New Components](#3-new-components)
4. [Architectural Patterns](#4-architectural-patterns)
5. [Security Design](#5-security-design)
6. [Hallucination Prevention](#6-hallucination-prevention)
7. [Cost Optimization](#7-cost-optimization)
8. [Coding Engine Evolution](#8-coding-engine-evolution)
9. [Follow-up Question Engine](#9-follow-up-question-engine)
10. [Knowledge Gap Engine](#10-knowledge-gap-engine)
11. [UI Evolution](#11-ui-evolution)
12. [Metrics](#12-metrics)
13. [Risk Register](#13-risk-register)
14. [Architecture Decision Records (V1.1/V1.2)](#14-architecture-decision-records-v11v12)
15. [Migration Plan](#15-migration-plan)
16. [Master Implementation Plan](#16-master-implementation-plan)

---

## 1. Current Architecture Overview

### 1.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        interface/                                    │
│                     CLI entry point                                  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                           app/                                       │
│   graph/          ui/            prompts/        sandbox/            │
│ (LangGraph 14)  (Gradio)     (centralized)   (AST-guarded Python)   │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                        services/ (~30 modules)                       │
│  QuestionService    EvaluationEngine    NarrativeAssembler           │
│  CodingExecutor     HintService         ExportService                │
│  SignalExtractor    FollowUpService     SQLExecutor                  │
│  AITestGenerator    SessionManager      ReportBuilder                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                       domain/                                        │
│   contracts/        policies/         events/                        │
│ (Pydantic models)  (business rules)  (domain events)                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                    infrastructure/                                   │
│  LLM adapters      settings/       ChromaDB        SQLite            │
│  (Default+         (config)        (vector store)  (in-memory SQL)   │
│   Observing)                                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Layer | Responsibility |
|-----------|-------|----------------|
| CLI | interface/ | Entry point; parses args; bootstraps graph |
| LangGraph (14 nodes) | app/graph | Orchestrates interview flow via state machine |
| Gradio UI | app/ui | State-driven candidate-facing interface |
| Prompt registry | app/prompts | Centralized prompt management (ADR-013) |
| AST Sandbox | app/sandbox | Safe Python execution via AST whitelist |
| QuestionService | services/ | Question retrieval, corpus selection, generation |
| EvaluationEngine | services/ | 7-step evaluation; scoring; dimension aggregation |
| NarrativeAssembler | services/ | LLM-driven coaching report text generation |
| CodingExecutor | services/ | Jinja harness, test runner, signal extraction |
| AITestGenerator | services/ | Hidden test generation per problem |
| SQLExecutor | services/ | In-memory SQLite, schema validation, result comparison |
| SignalExtractor | services/ | Signal Enrichment Strategy B output extraction |
| ExportService | services/ | PDF and JSON report serialization |
| DefaultLLMAdapter | infrastructure/ | OpenAI API calls with retry |
| ObservingLLMAdapter | infrastructure/ | Decorator: logging, latency, token tracking |
| ChromaDB | infrastructure/ | Embedding storage and semantic search |
| SQLite | infrastructure/ | In-memory SQL evaluation execution |

### 1.3 Key Data Flows

**Interview Session Flow:**
```
CLI → bootstrap graph → LangGraph node: session_init
  → node: intent_routing (ADR-001)
  → node: question_selection (ChromaDB + QuestionService)
  → node: question_presentation (Gradio)
  → node: answer_capture
  → node: evaluation_dispatch
      ├─ written_pipeline → EvaluationEngine → NarrativeAssembler
      ├─ coding_pipeline → CodingExecutor → AITestGenerator → SignalExtractor
      └─ sql_pipeline → SQLExecutor → EvaluationEngine
  → node: signal_enrichment (Strategy B)
  → node: follow_up_decision
  → node: report_assembly → ExportService
  → node: session_close
```

**LLM Call Chain:**
```
Service → ObservingLLMAdapter (log/trace)
        → DefaultLLMAdapter (retry + rate-limit)
        → OpenAI API (gpt-4o-mini)
        → Pydantic schema parse
        → output contract (ADR-002)
```

**Embedding Flow:**
```
Question text → text-embedding-3-small (OpenAI) → ChromaDB (ADR-015)
             → all-MiniLM-L6-v2 (local fallback) → ChromaDB (dual embedding, ADR-005)
```

---

## 2. Target Architecture (V1.2 End State)

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           interface/                                     │
│                    CLI     |    REST API (V1.2)                          │
└────────────────────────┬───┴────────────┬────────────────────────────────┘
                         │                │
┌────────────────────────▼────────────────▼────────────────────────────────┐
│                              app/                                         │
│  graph/         ui/            prompts/       sandbox/     replay/        │
│ (LangGraph 14) (Gradio +      (centralized + (AST + JSvm  (Replay Engine) │
│                dark mode)      sec. layer)    + TSvm)                     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                           security/  (NEW)                                │
│        PromptSecurityLayer   PromptValidationLayer   OutputValidationLayer│
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                        services/ (~45 modules)                            │
│  [V1.0 retained]                      [V1.1/V1.2 added]                  │
│  QuestionService    EvaluationEngine   InterviewReasoner                  │
│  CodingExecutor     NarrativeAssembler KnowledgeGapEngine                 │
│  HintService        SignalExtractor    CostOptimizer                      │
│  ExportService      AITestGenerator   ProgressTracker                    │
│  SQLExecutor        SessionManager    ResourceRecommendationEngine        │
│                                       LanguageAdapter (multi-lang)        │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                          domain/                                          │
│  contracts/       policies/        events/        gap_taxonomy/           │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                       infrastructure/                                     │
│  LLM adapters    settings/   ChromaDB    SQLite     ProgressStore         │
│  (+ cost router) (+ budgets) (vectors)  (SQL eval)  (SQLite persisted)   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 New Components Added in V1.1/V1.2

| Component | Milestone | Layer |
|-----------|-----------|-------|
| InterviewReasoner | M1-1 | services/ |
| KnowledgeGapEngine | M1-2 | services/ |
| PromptSecurityLayer | M1-1 | security/ |
| PromptValidationLayer | M1-1 | security/ |
| OutputValidationLayer | M1-2 | security/ |
| CostOptimizer | M1-3 | services/ |
| LanguageAdapter (JS/TS) | M2-1 | services/ |
| ResourceRecommendationEngine | M2-2 | services/ |
| ProgressTracker | M1-4 | services/ |
| ReplayEngine | M2-3 | app/replay/ |
| REST API layer | M2-4 | interface/ |

### 2.3 Unchanged Components

- LangGraph 14-node graph topology (state machine routing preserved)
- Gradio UI state-driver approach (ADR-003)
- Pydantic v2 output contracts (ADR-002)
- 7-step evaluation engine dimensions
- Signal Enrichment Strategy B
- PDF/JSON export pipeline
- AST-guarded Python sandbox
- Dual embedding approach (ADR-005)
- Prompt centralization registry (ADR-013)

### 2.4 Interactions and Boundaries

- **Security layer** wraps all LLM calls: input enters PromptSecurityLayer → PromptValidationLayer → LLM → OutputValidationLayer → consumer
- **CostOptimizer** sits between service layer and infrastructure adapters; intercepts pre-call decisions (route to cheaper model or cached response)
- **ProgressTracker** is write-through: every evaluation result is persisted to the SQLite progress store before being returned to the graph
- **ReplayEngine** is read-only at replay time; does not invoke LLM calls — it reconstructs from stored state snapshots
- **REST API** is a thin translation layer over existing services; does not embed business logic

---

## 3. New Components

### 3.1 Interview Reasoner

**Responsibilities:**
- Dynamically assess candidate trajectory during the interview session
- Decide whether to escalate, maintain, or de-escalate question difficulty
- Determine whether a follow-up question is warranted based on accumulated signals
- Emit difficulty-adjustment and follow-up recommendations as structured events

**Inputs:**
- `SessionState`: accumulated signal scores, question history, topic coverage map
- `EvaluationResult`: latest per-answer evaluation output
- `InterviewConfig`: target difficulty, topic weights, max follow-up percentage
- `BusinessContextProfile`: domain, seniority level, role expectations (ADR-006)

**Outputs:**
- `ReasonerDecision`: `{ next_action: escalate | maintain | de_escalate | follow_up | close, rationale: str, confidence: float }`
- `DifficultyAdjustmentEvent`: domain event emitted on difficulty change
- `FollowUpTrigger`: structured trigger forwarded to FollowUpService

**Dependencies:**
- `EvaluationEngine` (consumes EvaluationResult)
- `FollowUpService` (receives FollowUpTrigger)
- `domain/events` (emits DifficultyAdjustmentEvent)
- `domain/policies` (applies follow-up percentage cap policy)

**Interface Contract:**
```
ReasonerDecision = {
  session_id: UUID
  next_action: Literal["escalate","maintain","de_escalate","follow_up","close"]
  rationale: str
  confidence: float  # [0.0, 1.0]
  timestamp: datetime
}
```

---

### 3.2 Knowledge Gap Engine

**Responsibilities:**
- Analyze evaluation results across all completed answers to detect persistent knowledge gaps
- Classify gaps by topic domain using the gap taxonomy (Section 10)
- Score gap severity and detection confidence
- Generate a prioritized learning roadmap
- Interface with ResourceRecommendationEngine to hydrate the roadmap with resources

**Inputs:**
- `List[EvaluationResult]`: all per-answer evaluations from a completed session
- `CandidateProfile`: domain, seniority, declared competencies
- `GapTaxonomy`: canonical taxonomy loaded from domain/gap_taxonomy/

**Outputs:**
- `KnowledgeGapReport`: `{ gaps: List[Gap], severity_map: dict, learning_roadmap: List[RoadmapItem] }`
- `Gap`: `{ topic: str, taxonomy_node: str, severity: float, confidence: float, evidence: List[str] }`
- `RoadmapItem`: `{ topic: str, priority: int, resources: List[Resource] }`

**Dependencies:**
- `EvaluationEngine` (consumes scores)
- `ResourceRecommendationEngine` (resource hydration)
- `domain/gap_taxonomy/` (canonical taxonomy)

**Interface Contract:**
```
KnowledgeGapReport = {
  session_id: UUID
  candidate_id: str
  generated_at: datetime
  gaps: List[Gap]
  learning_roadmap: List[RoadmapItem]
  overall_gap_severity: float  # [0.0, 1.0]
}
```

---

### 3.3 Prompt Security Layer (Input Sanitization + Prompt Injection Defense)

**Responsibilities:**
- Sanitize all user-supplied text before it reaches any prompt template
- Detect and neutralize prompt injection attempts (direct and indirect)
- Detect and block visual prompt injection patterns (Unicode homoglyphs, invisible characters)
- Enforce content policy on user inputs
- Log all sanitization events for audit

**Inputs:**
- `RawUserInput`: raw string from candidate answer, job description, or any user-supplied field
- `InputContext`: metadata (`field_name`, `expected_type`, `max_length`, `allowed_patterns`)

**Outputs:**
- `SanitizedInput`: cleaned string, guaranteed safe for template interpolation
- `SanitizationEvent`: audit log entry with threat classification, severity, and action taken
- Raises `PromptInjectionDetectedError` (domain exception) if high-confidence injection detected

**Dependencies:**
- `domain/exceptions` (PromptInjectionDetectedError)
- `infrastructure/logging` (audit event emission)
- `PromptValidationLayer` (downstream consumer)

**Interface Contract:**
```
SanitizedInput = {
  original_hash: str         # SHA-256 of original input
  sanitized_text: str
  threats_detected: List[ThreatClassification]
  action_taken: Literal["allowed","sanitized","blocked"]
  confidence: float
}

ThreatClassification = {
  threat_type: Literal["direct_injection","indirect_injection","visual_injection","jailbreak","prompt_leakage"]
  severity: Literal["low","medium","high","critical"]
  pattern_matched: str
}
```

---

### 3.4 Prompt Validation Layer

**Responsibilities:**
- Validate assembled prompts before LLM dispatch: structural integrity, length bounds, forbidden token sequences
- Enforce per-prompt-type schema (question generation, evaluation, narrative, hint)
- Verify that sanitized user content is correctly escaped within template slots
- Block prompts that exceed model context window limits

**Inputs:**
- `AssembledPrompt`: fully rendered prompt string from prompt registry
- `PromptType`: enum identifying which template was used
- `ModelConfig`: target model, context window limit, reserved token budget

**Outputs:**
- `ValidatedPrompt`: approved prompt ready for LLM dispatch
- `PromptValidationResult`: `{ passed: bool, violations: List[str], token_count: int }`
- Raises `PromptValidationError` if hard violations detected

**Dependencies:**
- `app/prompts` (prompt registry, ADR-013)
- `infrastructure/settings` (model configs)
- `PromptSecurityLayer` (upstream)

---

### 3.5 Output Validation Layer

**Responsibilities:**
- Parse and validate every LLM response against its expected Pydantic output contract
- Detect hallucination markers: fabricated citations, impossible values, schema violations
- Enforce business-rule constraints on parsed output (e.g., score in [0,10], non-empty rationale)
- Implement retry-or-fallback policy on validation failure
- Emit `OutputValidationEvent` for observability

**Inputs:**
- `RawLLMResponse`: raw string from LLM API
- `OutputSchema`: Pydantic model class for the expected contract
- `ValidationPolicy`: max_retries, fallback_value, strict mode flag

**Outputs:**
- `ValidatedOutput`: typed Pydantic instance conforming to `OutputSchema`
- `OutputValidationEvent`: `{ passed: bool, violations: List[str], retry_count: int, fallback_used: bool }`
- Raises `OutputValidationError` after max retries exhausted

**Dependencies:**
- `domain/contracts` (Pydantic output schemas, ADR-002)
- `infrastructure/llm_adapters` (retry loop integration)
- `ObservingLLMAdapter` (event forwarding)

---

### 3.6 Cost Optimizer

**Responsibilities:**
- Intercept outgoing LLM calls and apply model routing decisions (Section 7)
- Maintain per-session token budget tracking
- Serve cached LLM responses when cache hit confidence exceeds threshold
- Apply prompt compression strategies (truncation, summarization) when budget is strained
- Emit `CostEvent` for billing KPI tracking

**Inputs:**
- `LLMCallRequest`: prompt, model hint, temperature, expected output schema
- `SessionBudget`: remaining token budget for the session
- `ResponseCache`: in-memory + disk-backed cache keyed on prompt hash
- `ModelRoutingPolicy`: rules mapping call type → cheapest acceptable model

**Outputs:**
- `RoutedLLMCallRequest`: modified request with final model selection
- `CostEvent`: `{ call_type: str, model_used: str, tokens_in: int, tokens_out: int, cache_hit: bool, cost_usd: float }`
- Returns cached `ValidatedOutput` on hit without LLM invocation

**Dependencies:**
- `infrastructure/llm_adapters` (downstream)
- `infrastructure/settings` (model pricing config)
- `domain/policies` (budget enforcement policy)

---

### 3.7 Language Adapter (Multi-language Coding)

**Responsibilities:**
- Abstract coding execution for Python, JavaScript, and TypeScript behind a unified interface
- Provide language-specific sandbox execution (Python: AST guard; JS/TS: isolated V8 vm)
- Generate hidden tests in the target language via the oracle generator
- Map language-specific execution results to the shared `ExecutionResult` contract
- Delegate signal extraction to language-agnostic `SignalExtractor`

**Inputs:**
- `CodingSubmission`: `{ code: str, language: Language, problem_id: str }`
- `HiddenTests`: generated by per-language OracleGenerator
- `ExecutionConfig`: timeout, memory limit, language-specific flags

**Outputs:**
- `ExecutionResult`: `{ passed: int, failed: int, errors: List[str], stdout: str, signal_metadata: dict }`

**Dependencies:**
- `PythonLanguageStrategy` (existing CodingExecutor, refactored)
- `JavaScriptLanguageStrategy` (new)
- `TypeScriptLanguageStrategy` (new, transpiles to JS before execution)
- `SignalExtractor` (shared, language-agnostic)
- `AITestGenerator` (extended to support multi-language oracle generation)

**Interface Contract:**
```
LanguageAdapterPort (abstract):
  execute(submission: CodingSubmission, tests: HiddenTests) → ExecutionResult
  generate_oracle(problem: Problem, language: Language) → HiddenTests
  validate_syntax(code: str) → SyntaxValidationResult
```

---

### 3.8 Resource Recommendation Engine

**Responsibilities:**
- Map knowledge gaps from KnowledgeGapEngine to curated learning resources
- Prioritize resources by gap severity, candidate seniority, and resource quality score
- Support multiple resource types: documentation, video, practice problem, book chapter
- Produce a ranked, deduplicated resource list per gap

**Inputs:**
- `List[Gap]`: from KnowledgeGapEngine
- `CandidateProfile`: seniority, preferred learning style
- `ResourceCatalog`: ChromaDB collection of curated resources with embeddings

**Outputs:**
- `List[ResourceRecommendation]`: ranked and annotated resource list per gap
- `ResourceRecommendation`: `{ gap_topic: str, resource_type: ResourceType, title: str, url: str, relevance_score: float, estimated_hours: float }`

**Dependencies:**
- `KnowledgeGapEngine` (upstream gap list)
- `ChromaDB` (resource catalog vector store)
- `infrastructure/settings` (catalog collection name)

---

### 3.9 Progress Tracker

**Responsibilities:**
- Persist session outcomes to a durable SQLite store (separate from in-memory SQL evaluation)
- Track per-candidate historical performance across sessions
- Provide trend data: improvement delta, topic mastery evolution, gap recurrence
- Expose a query interface for report assembly and replay

**Inputs:**
- `CompletedSession`: full session state including all EvaluationResults
- `CandidateId`: stable identifier across sessions
- `ProgressQuery`: filters for history retrieval (date range, topic, session count)

**Outputs:**
- `ProgressRecord`: persisted session summary
- `ProgressHistory`: `{ sessions: List[ProgressRecord], trends: TrendAnalysis }`
- `TrendAnalysis`: `{ improving_topics: List[str], regressing_topics: List[str], readiness_delta: float }`

**Dependencies:**
- `infrastructure/progress_store` (SQLite persistence, ADR-022)
- `EvaluationEngine` (input data source)
- `ReplayEngine` (consumer of stored records)

**Interface Contract:**
```
ProgressTrackerPort (abstract):
  record_session(session: CompletedSession) → ProgressRecord
  get_history(candidate_id: str, query: ProgressQuery) → ProgressHistory
  get_trend(candidate_id: str, topic: str) → TrendAnalysis
```

---

### 3.10 Replay Engine

**Responsibilities:**
- Reconstruct any past interview session from stored state snapshots without re-invoking LLMs
- Support selective replay: resume from any node, re-evaluate specific answers
- Provide diff view between original and re-evaluated results
- Enable debugging of evaluation inconsistencies and regression testing

**Inputs:**
- `SessionSnapshot`: serialized LangGraph state at each node transition (ADR-023)
- `ReplayConfig`: `{ session_id: UUID, start_node: str, mode: full | selective, target_answers: List[int] }`

**Outputs:**
- `ReplayResult`: reconstructed session with per-node state
- `ReplayDiff`: delta between original and replayed evaluation outcomes
- `ReplayEvent`: audit event per replayed node

**Dependencies:**
- `ProgressTracker` (snapshot retrieval)
- `infrastructure/progress_store` (ADR-022, ADR-023)
- `app/graph` (graph node definitions, used read-only)

---

## 4. Architectural Patterns

### 4.1 SOLID Principles

**Applied across:** all new services in V1.1/V1.2

- **SRP:** Each new component has one declared responsibility (e.g., `KnowledgeGapEngine` detects gaps; `ResourceRecommendationEngine` maps gaps to resources — they do not share a class).
- **OCP:** `LanguageAdapter` is open for extension via new `LanguageStrategy` implementations without modifying the adapter interface.
- **LSP:** All `LanguageStrategy` implementations (`PythonLanguageStrategy`, `JavaScriptLanguageStrategy`, `TypeScriptLanguageStrategy`) are substitutable through `LanguageAdapterPort`.
- **ISP:** `ProgressTrackerPort` exposes only three narrow methods; consumers depend only on the method they need.
- **DIP:** Services depend on abstract ports (`LanguageAdapterPort`, `ProgressTrackerPort`) not concrete implementations; infrastructure details are injected.

### 4.2 Strategy Pattern

**Applied in:**
- `LanguageAdapter`: `LanguageStrategy` interface + `PythonLanguageStrategy`, `JavaScriptLanguageStrategy`, `TypeScriptLanguageStrategy` concrete strategies. Selected at runtime based on `CodingSubmission.language`.
- `PromptSecurityLayer`: `SanitizationStrategy` interface with pluggable strategies (regex filter, ML-based injection classifier, unicode normalization). Strategies are chained, not mutually exclusive.
- `CostOptimizer`: `ModelRoutingStrategy` selects between gpt-4o-mini and cheaper alternatives per call type.

### 4.3 Factory Pattern

**Applied in:**
- `LanguageAdapterFactory`: instantiates the correct `LanguageStrategy` based on `Language` enum value; encapsulates sandbox bootstrap and VM lifecycle.
- `EvaluationPipelineFactory` (V1.0, retained): constructs written/coding/SQL pipeline variants. Extended in V1.1 to inject `OutputValidationLayer` into each pipeline.
- `SanitizationStrategyFactory`: constructs the sanitization chain based on `InputContext.expected_type`.

### 4.4 Pipeline Pattern

**Applied in:**
- The security layer forms a linear pipeline: `RawInput → PromptSecurityLayer → PromptValidationLayer → LLM → OutputValidationLayer → Consumer`. Each stage is a pure function with a defined input/output contract.
- Evaluation pipeline (V1.0, retained): signal extraction → dimension scoring → narrative assembly → export. V1.1 injects `OutputValidationLayer` between narrative assembly and export.
- `KnowledgeGapEngine` processes gaps through a pipeline: `EvaluationResults → gap_detection → gap_classification → severity_scoring → roadmap_generation`.

### 4.5 Builder Pattern

**Applied in:**
- `KnowledgeGapReport` construction: `KnowledgeGapReportBuilder` accumulates gaps, severity scores, and roadmap items incrementally as evaluation results are processed, then builds the final immutable report.
- `LearningRoadmap` assembly: `RoadmapBuilder` appends `RoadmapItem` entries in priority order, deduplicates, and finalizes.
- `ReplayResult` construction: `ReplayResultBuilder` accumulates per-node states and builds the final diff after all nodes are replayed.

### 4.6 Adapter Pattern

**Applied in:**
- `ObservingLLMAdapter` (V1.0, retained): wraps `DefaultLLMAdapter`, adds observability concerns without modifying the adaptee.
- `CostOptimizer` (V1.1): wraps the LLM adapter chain, intercepting calls without changing caller or callee contracts.
- `LanguageAdapterPort` (V1.1): adapts language-specific execution environments to the shared `ExecutionResult` contract used by `EvaluationEngine`.
- `ProgressStore` adapter: adapts raw SQLite row operations to the `ProgressTrackerPort` domain interface.

### 4.7 Validation Layer (Chain of Responsibility)

**Applied in:**
- `PromptSecurityLayer`: each sanitization strategy in the chain receives the input, may transform it, and passes it to the next strategy. Any strategy may halt the chain by raising `PromptInjectionDetectedError`.
- `OutputValidationLayer`: validation rules are applied in sequence (schema parse → business rule checks → hallucination marker detection). Each rule is independently testable.
- `PromptValidationLayer`: structural check → length check → forbidden sequence check → context window check, each as an independent validator.

### 4.8 Observer Pattern (Observability)

**Applied in:**
- `ObservingLLMAdapter` (V1.0, retained): observes LLM calls, emits `LLMCallEvent` to the logging infrastructure without modifying call semantics.
- `CostOptimizer`: emits `CostEvent` on every resolved LLM call.
- `PromptSecurityLayer`: emits `SanitizationEvent` on every processed input.
- `OutputValidationLayer`: emits `OutputValidationEvent` on every validated response.
- `ProgressTracker`: emits `ProgressRecordedEvent` on every persisted session.

All events follow the same `DomainEvent` base contract from `domain/events`, ensuring consistent observability plumbing.

---

## 5. Security Design

### 5.1 Threat Model

| Threat | Description | Vector |
|--------|-------------|--------|
| **Direct Prompt Injection** | Candidate embeds instructions in their answer that override system behavior | Answer text, follow-up text |
| **Indirect Prompt Injection** | Malicious content embedded in externally retrieved data (job descriptions, documents) | Business context profile input |
| **Visual Prompt Injection** | Unicode homoglyphs, zero-width characters, or invisible Unicode used to smuggle instructions | Any user-supplied text field |
| **Prompt Leakage** | LLM reveals system prompt or internal instructions in its response | LLM output |
| **Jailbreak** | Candidate attempts to bypass evaluation guardrails to receive inflated scores | Answer text |

### 5.2 Mitigations Per Threat

| Threat | Primary Mitigation | Secondary Mitigation |
|--------|-------------------|---------------------|
| Direct Injection | PromptSecurityLayer: regex + classifier | Prompt structure: role separation, delimiter escaping |
| Indirect Injection | Input field-type enforcement; external content treated as untrusted data, never as instructions | ContextSanitizationLayer on business profile fields |
| Visual Injection | Unicode normalization (NFKC) + invisible character strip in PromptSecurityLayer | Audit logging of character-level anomalies |
| Prompt Leakage | OutputValidationLayer: detect system prompt phrases in output | System prompt marked with unique sentinel; sentinel match triggers block |
| Jailbreak | PromptSecurityLayer: jailbreak pattern library; OutputValidationLayer: score range enforcement | Hard constraint: scores always validated against [0.0, 10.0] range |

### 5.3 Input Sanitization Design

**Pipeline (sequential, all stages execute):**

1. **Encoding normalization:** Convert to UTF-8; apply NFKC Unicode normalization.
2. **Invisible character removal:** Strip zero-width space, zero-width joiner, soft hyphen, and all Unicode Cf category characters.
3. **Length enforcement:** Reject inputs exceeding `MAX_INPUT_LENGTH` per field type (configurable in settings).
4. **Pattern matching:** Apply regex library for known injection patterns (`ignore previous instructions`, `system:`, `<|im_start|>`, etc.).
5. **ML-based injection classifier:** Light-weight local classifier (distilbert fine-tuned on injection dataset) returns injection confidence score.
6. **Action decision:** `confidence > 0.9` → block; `0.5–0.9` → sanitize + flag; `< 0.5` → allow with audit log.
7. **Escaping:** Wrap user content in structural delimiters (triple backtick + role label) within prompt templates to isolate from instruction tokens.

### 5.4 Output Validation Design

**Pipeline (sequential):**

1. **Schema parse:** Attempt Pydantic model parse of LLM JSON output.
2. **Type enforcement:** All fields validated against declared types.
3. **Range enforcement:** Numeric scores validated against domain-defined ranges.
4. **Non-null enforcement:** Required narrative fields must be non-empty strings.
5. **Hallucination marker detection:** Regex scan for known fabrication signals (`As an AI`, `I cannot verify`, suspicious citation patterns).
6. **Prompt leakage detection:** Scan for system prompt sentinel token.
7. **Business rule validation:** Score consistency (e.g., sum of dimension scores correlates with overall score within tolerance).
8. **Retry or fallback:** On failure, retry up to `MAX_RETRIES` (default: 2); on exhaustion, apply `fallback_value` or raise `OutputValidationError`.

### 5.5 Schema Validation Layer

- All inputs entering the service layer must pass through Pydantic v2 models before use.
- No raw string field reaches an LLM prompt without having been wrapped in a typed Pydantic field first.
- API route inputs (V1.2 REST layer) validated at the boundary with Pydantic request models before reaching services.

### 5.6 Context Sanitization

- Business context profiles (role, company, job description) are treated as **untrusted external data**.
- Applied to a `ContextSanitizationLayer` (subset of PromptSecurityLayer) before being interpolated into any prompt.
- Job description content is rendered as structured data fields (title, required_skills, experience_years) — never as freeform text injected into the instruction portion of a prompt.

### 5.7 Acceptance Criteria Per Mitigation

| Mitigation | Acceptance Criterion |
|-----------|---------------------|
| Direct injection blocking | 95%+ detection rate on a curated injection test set (100 samples); 0 false negatives on critical patterns |
| Indirect injection | Context fields interpolated only into designated data slots, never instruction slots — verified by prompt template audit |
| Visual injection | 100% NFKC normalization coverage; all Cf-category characters stripped — verified by unit test suite |
| Prompt leakage | Sentinel present in system prompt; OutputValidationLayer blocks any response containing sentinel — verified by integration test |
| Jailbreak | Score fields always in [0.0, 10.0]; OutputValidationLayer enforces this before any consumer sees the value |
| Input length | All fields have enforced MAX_INPUT_LENGTH; oversized inputs raise `InputTooLargeError` |

---

## 6. Hallucination Prevention

### 6.1 Classification of Hallucination Types

| Type | Description | Example |
|------|-------------|---------|
| **Factual hallucination** | LLM states incorrect facts as true | "This algorithm has O(log n) complexity" when it is O(n) |
| **Structural hallucination** | LLM output does not conform to declared schema | Missing required field; wrong type for a field |
| **Fabricated evidence** | LLM invents citations, test results, or code outputs | "Your solution passed all 5 tests" when no tests were run |
| **Evaluation inflation** | LLM assigns scores inconsistent with reasoning | Score 9/10 with reasoning identifying major errors |
| **Fabricated follow-up** | LLM generates a follow-up question unrelated to the candidate's answer | Generic question ignoring actual answer content |

### 6.2 Detection Strategies

- **Structural:** Pydantic schema parse failure is the primary detector. Any unparseable output is a structural hallucination signal.
- **Factual:** Cross-reference evaluation scores against signal extractor output; flag divergences exceeding a configurable tolerance (default ±2.0 points).
- **Fabricated evidence:** Output validation checks for test result claims in narrative output; cross-references against actual `ExecutionResult.passed` / `ExecutionResult.failed` counts.
- **Evaluation inflation:** Business rule validator checks score-reasoning consistency using a secondary lightweight LLM call (model: gpt-4o-mini with zero temperature, one-shot classification prompt).
- **Fabricated follow-up:** Follow-up questions are validated for lexical overlap with the candidate's actual answer using cosine similarity on embeddings; low overlap triggers regeneration.

### 6.3 Prevention Strategies

| Strategy | Application |
|----------|-------------|
| **Temperature control** | Evaluation calls: temperature=0.0. Generation calls: temperature=0.4 max. |
| **Structured output mode** | All LLM calls use OpenAI JSON mode + Pydantic schema enforcement. |
| **Schema enforcement** | `OutputValidationLayer` enforces Pydantic contracts on every response. |
| **Few-shot anchoring** | Evaluation prompts include 2 canonical examples with correct score-reasoning pairs. |
| **Grounding constraints** | Narrative assembly prompts are constrained to reference only fields present in `EvaluationResult`; no freeform factual claims. |
| **Explicit instruction** | System prompts include explicit instruction: "Do not invent test results. Do not cite external sources." |

### 6.4 Recovery Strategies

| Recovery | Trigger | Action |
|----------|---------|--------|
| **Retry with higher precision** | Schema parse failure | Re-invoke LLM with temperature reduced to 0.0; re-validate. |
| **Retry with simplified schema** | Repeated schema failure | Strip optional fields; retry with minimal required-only schema. |
| **Fallback to template** | Max retries exhausted on narrative | Use deterministic template-based narrative assembly (no LLM). |
| **Degraded mode** | OutputValidationError on evaluation | Return partial result with `confidence: low` flag; surface warning in UI. |
| **Score clamping** | Score out of range detected | Clamp to [0.0, 10.0]; log `ScoreClampedEvent`; do not retry. |

### 6.5 Validation Pipeline

```
LLM Response
  → JSON parse attempt
    ├─ FAIL → retry (up to MAX_RETRIES)
    └─ OK
        → Pydantic schema validation
          ├─ FAIL → retry with simplified schema
          └─ OK
              → Business rule validation (score ranges, non-empty fields)
                ├─ FAIL → score clamp / degraded mode
                └─ OK
                    → Hallucination marker scan
                      ├─ DETECTED → retry or fallback
                      └─ CLEAR → emit ValidatedOutput
```

### 6.6 Monitoring and Metrics

- `hallucination_detected_total` (counter, by type)
- `schema_parse_failure_rate` (gauge, per call type)
- `output_retry_rate` (gauge, per call type)
- `fallback_triggered_total` (counter, by call type)
- `score_clamped_total` (counter)
- All metrics emitted as `OutputValidationEvent` fields; collected by ObservingLLMAdapter.

---

## 7. Cost Optimization

### 7.1 Prompt Optimization Strategies

- **Few-shot trimming:** Reduce few-shot examples from 3 to 2 for evaluation calls where signal-to-token ratio is low. Retain 3 only for narrative generation where quality is user-visible.
- **Dynamic prompt truncation:** If candidate answer exceeds 1,000 tokens, apply extractive summarization (local, no LLM) before evaluation prompt construction.
- **Instruction compression:** Audit all prompts in registry for redundant instruction repetition; deduplicate into shared preamble loaded once.
- **Structured output enforcement:** JSON mode eliminates explanation preambles from LLM responses, reducing output tokens by 20–40%.

### 7.2 Token Budgeting Design

- Per-session token budget defined in `InterviewConfig.token_budget` (default: 80,000 tokens).
- `CostOptimizer` tracks `tokens_consumed` and `tokens_remaining` throughout the session.
- When `tokens_remaining < BUDGET_WARNING_THRESHOLD` (20%), optimizer applies aggressive truncation.
- When `tokens_remaining < BUDGET_CRITICAL_THRESHOLD` (10%), optimizer routes remaining calls to cheapest model regardless of call type.
- Budget exhaustion halts LLM calls; remaining pipeline steps use template-based fallback.

### 7.3 Response Caching Architecture

**Cache tiers:**

1. **In-memory LRU cache (L1):** Keyed on `SHA-256(prompt_text + model + temperature)`. TTL: session lifetime. Max size: 100 entries. Serves identical prompts within a session (e.g., repeated hint generation for same problem).
2. **Disk-backed cache (L2):** SQLite table `llm_cache` in the progress store. TTL: 7 days. Keyed on same hash. Serves across sessions for stable prompts (e.g., question generation for the same topic + difficulty).

**Cache invalidation:**
- L1: evicted on session close.
- L2: evicted on TTL expiry; force-invalidated on prompt template version change (detected by prompt registry version hash).

### 7.4 Model Routing (When to Use Cheaper Models)

| Call Type | Default Model | Routable to Cheaper? | Cheaper Model | Trigger |
|-----------|--------------|---------------------|---------------|---------|
| question_generation | gpt-4o-mini | No | — | Quality-critical |
| written_evaluation | gpt-4o-mini | Yes | gpt-4o-mini (lower temp) | Budget < 20% |
| hint_generation | gpt-4o-mini | Yes | gpt-3.5-turbo | Always eligible |
| narrative_generation | gpt-4o-mini | No | — | User-visible quality |
| testcase_explanation | gpt-4o-mini | Yes | gpt-3.5-turbo | Always eligible |
| answer_improvement | gpt-4o-mini | Yes | gpt-3.5-turbo | Always eligible |
| score_consistency_check | gpt-4o-mini | Yes | gpt-3.5-turbo | Micro-call by design |

### 7.5 Response Reuse Patterns

- **Hint reuse:** Hints generated for a given `(problem_id, hint_level)` pair are cached and reused for all candidates attempting the same problem.
- **Test case explanation reuse:** Explanations for hidden test cases are generated once per `problem_id` and cached to L2.
- **Question corpus:** Pre-generated questions are stored in ChromaDB and reused; LLM generation is a fallback only (ADR-014 sufficiency).

### 7.6 Early Stopping Design

- If a candidate answer receives a score ≥ 9.0 on all evaluation dimensions, skip hint generation and answer improvement calls.
- If `ExecutionResult.passed / total_tests ≥ 0.95`, skip detailed test case explanation; surface only a summary line.
- If `InterviewReasoner` emits `close` action, abort remaining question generation calls.

### 7.7 Batching Opportunities

- **Evaluation dimension scoring:** Currently 7 sequential LLM sub-calls. V1.1 target: consolidate into a single structured JSON call returning all 7 dimension scores in one response. Estimated saving: 6 API round-trips per answer.
- **Hint level generation:** Pre-generate all 3 hint levels in a single call if the problem is new (cache miss on all levels).

### 7.8 RAG Opportunities (Reduce LLM Calls)

- **Question selection:** ChromaDB retrieval already replaces LLM generation for 80%+ of questions (ADR-014). V1.1 target: raise corpus coverage to 95% by expanding corpus during session synthesis.
- **Follow-up question selection:** Build a follow-up corpus in ChromaDB; retrieve before falling back to generation. Estimated reduction: 40% of follow-up generation calls.
- **Resource recommendation:** All recommendations served from ChromaDB-indexed resource catalog; no LLM call needed for resource lookup.

### 7.9 Fine-tuning Feasibility Assessment

| Use Case | Feasibility | Rationale |
|----------|-------------|-----------|
| Evaluation scoring | Low | Score distributions shift with interview domain; fine-tuned model would require per-domain retraining |
| Narrative generation | Medium | Coaching narrative style is stable; fine-tuning on high-quality coaching examples could reduce token usage |
| Hint generation | High | Hint style is constrained and domain-independent; a fine-tuned model could serve hints at gpt-3.5 cost with gpt-4o quality |
| Question generation | Low | Question quality requires world knowledge; fine-tuning risks knowledge cutoff degradation |

**Recommendation for V1.2:** Proceed with hint generation fine-tuning feasibility study; defer others.

### 7.10 Expected Savings Estimates (Qualitative)

| Strategy | Estimated Saving |
|----------|-----------------|
| Evaluation dimension batching | ~40% reduction in evaluation API calls |
| Follow-up RAG | ~40% reduction in follow-up generation calls |
| hint/explanation model routing | ~30% cost reduction on routable call types |
| Response caching (L2) | ~15% cross-session savings on stable prompts |
| Prompt truncation | ~10–15% input token reduction |
| Early stopping | ~5–10% session-level savings on high-performing candidates |
| **Combined (non-compounding estimate)** | **~50–60% cost reduction vs. V1.0 baseline** |

### 7.11 Trade-offs

| Strategy | Trade-off |
|----------|-----------|
| Model routing to cheaper models | Quality risk on routable call types; must A/B test before rollout |
| Evaluation batching | Prompt becomes larger; may trigger context window limits on complex answers |
| Response caching | Stale hints/explanations if problem set changes; requires cache invalidation discipline |
| Early stopping | Missed coaching opportunity for high-performers; mitigation: always assemble narrative even if evaluation LLM calls are skipped |

---

## 8. Coding Engine Evolution

### 8.1 Current State

- **Languages:** Python only
- **Sandbox:** AST whitelist guard; forbidden node types block dangerous operations
- **Test generation:** `AITestGenerator` produces hidden tests via LLM; tests are Python pytest-compatible
- **Execution:** `CodingExecutor` with Jinja harness; runs test suite, captures stdout/stderr, maps to `ExecutionResult`
- **Signal extraction:** `SignalExtractor` (Strategy B) parses execution result for quality signals
- **Evaluation:** `EvaluationEngine` consumes signals + code for written evaluation

### 8.2 Target: Python + JavaScript + TypeScript

**V1.1 milestone:** Add JavaScript support  
**V1.2 milestone:** Add TypeScript support (transpile → JS execution)

### 8.3 Architecture Using Strategy Pattern

```
CodingSubmission → LanguageAdapterFactory.create(language)
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
    PythonStrategy  JSStrategy   TSStrategy
         │               │           │
   AST sandbox      V8 vm2 sandbox  tsc transpile
         │               │           → V8 vm2 sandbox
         └──────────┬────┘
                    ▼
             ExecutionResult
                    ▼
            SignalExtractor (shared)
                    ▼
            EvaluationEngine (shared)
```

### 8.4 Language Adapter Interface

```
LanguageAdapterPort:
  execute(submission: CodingSubmission, tests: HiddenTests, config: ExecutionConfig) → ExecutionResult
  generate_oracle(problem: Problem, language: Language) → HiddenTests
  validate_syntax(code: str, language: Language) → SyntaxValidationResult
  get_sandbox_type() → SandboxType
  get_supported_version() → str
```

### 8.5 Execution Sandbox Per Language

| Language | Sandbox | Mechanism | Constraints |
|----------|---------|-----------|-------------|
| Python | AST whitelist guard (existing) | Compile-time AST inspection; blocked nodes list | No subprocess, no file I/O, no network |
| JavaScript | Node.js `vm` module in restricted context | `vm.runInNewContext` with empty global | No require, no process, no fs |
| TypeScript | tsc transpile → Node.js vm | TypeScript compiler (bundled) → JS → vm | Same as JS + type errors fail fast |

**Sandbox contract:** All sandboxes enforce:
- Execution timeout (configurable, default: 5s)
- Memory limit (configurable, default: 256MB)
- No external I/O
- Captured stdout/stderr (not inherited from host)

### 8.6 Oracle Generation Per Language

- `AITestGenerator` extended with language parameter.
- LLM generates test cases as language-native assertions (Python: `assert expr`, JS: `console.assert(expr)`, TS: `expect(expr).toBe(val)`).
- Generated tests are validated for syntactic correctness by `validate_syntax` before storage.
- Test corpus is stored in ChromaDB with language tag for retrieval.

### 8.7 Hidden Test Generation Per Language

- Problem definitions are language-agnostic (input/output specification in natural language).
- `AITestGenerator` receives `(problem, language)` and generates language-native test harness.
- Generated tests are cached in L2 cache keyed on `(problem_id, language)`.

### 8.8 Evaluation Reuse Across Languages

- `SignalExtractor` (Strategy B) operates on `ExecutionResult` which is a language-agnostic contract. No changes required.
- `EvaluationEngine` dimensions (correctness, efficiency, readability, etc.) apply to all languages identically.
- Narrative assembly receives the same `EvaluationResult` regardless of language.

### 8.9 Migration Strategy from Python-Only

1. Refactor `CodingExecutor` → `PythonLanguageStrategy` (no behavior change, structural refactor).
2. Introduce `LanguageAdapterPort` and `LanguageAdapterFactory`.
3. Wire `PythonLanguageStrategy` through factory; verify all existing Python tests pass.
4. Implement `JavaScriptLanguageStrategy` with vm2 sandbox.
5. Extend `AITestGenerator` with JS oracle generation.
6. Integrate JS path end-to-end; add regression tests.
7. Implement `TypeScriptLanguageStrategy` (thin wrapper over JS strategy with tsc step).
8. Extend ChromaDB question corpus with JS/TS-specific coding problems.

### 8.10 Cost/Benefit Analysis

| Factor | Cost | Benefit |
|--------|------|---------|
| JS/TS sandbox implementation | Medium (vm2 integration + test suite) | Covers 60%+ of real-world frontend/full-stack interview scenarios |
| Extended oracle generation LLM calls | Low (cached per problem) | Unlocks JS/TS evaluation at no per-session marginal cost after first generation |
| TypeScript transpile step | Low (bundled tsc, no LLM) | Enables typed JS evaluation without significant runtime overhead |
| Corpus expansion | Medium (LLM-assisted seeding) | Reduces JS/TS generation fallback rate; improves quality |
| Regression test suite expansion | Medium (test engineering time) | Ensures Python quality unaffected by refactoring |

---

## 9. Follow-up Question Engine

> **Status: IMPLEMENTED — V1.1 M1 (Frozen 2026-06-30)**
> This section describes the **shipped implementation**. The original TDS §9 design (corpus-first, InterviewReasoner-gated, ChromaDB-backed) was revised during M1-1 Architecture Review. See ADR-019 (revised), ADR-024, ADR-025.

### 9.1 Runtime Pipeline

```
session start (start.py)
        │
        ▼
FollowUpSelector.select()
  → frozenset[int] stored in state.follow_up_eligible_indices (once only)
        │
        ▼
question_node (per WRITTEN question)
        │
   index in eligible_indices?
   supports_follow_up=True?
   follow_up_count < max?
        │
       YES
        ▼
_attempt_follow_up()
        │
        ▼
_build_follow_up_prompt_input()
        │
        ▼
HumanizerService.generate_follow_up()
        │
        ▼
FollowUpPromptBuilder → PromptLoader → follow_up_generation.txt → PromptRenderer
        │
        ▼
LLM.invoke()
        │
        ▼
FollowUpParser (STRICT)
  ← FollowUpParseError on any contract violation
        │
        ▼
FollowUpGuard.validate() — 17 deterministic rules
        │
  accepted?
  YES          NO
   │            │
   ▼            ▼
display     FollowUpSkippedEvent
follow-up   → fallback to V1.0 humanizer
follow-up-  → interview continues
TriggeredEvent
state update
```

### 9.2 Selector Design

- **Algorithm:** `FollowUpSelector.select(total_questions, planned_areas, settings)`
- **Quota:** `policy="percentage"` → `floor(total_questions × follow_up_percentage)`, capped at `max_follow_ups_per_interview`
- **Constraints:** index 0 excluded; last index excluded; no two consecutive indices
- **Determinism:** Pure function — same inputs always produce same `frozenset[int]`
- **Wiring:** Called once in `app/ui/state_handlers/start.py` after questions are built, before `run_interview_graph()`

### 9.3 Prompt Architecture

- **Prompt file:** `app/prompts/humanizer/follow_up_generation.txt` (Jinja2 template)
- **Loader:** `PromptLoader.load("humanizer/follow_up_generation.txt")`
- **Renderer:** `PromptRenderer` with `StrictUndefined` — fails fast on missing variables
- **11 template variables:** `question_area`, `previous_question`, `previous_answer`, `previous_feedback`, `candidate_level`, `role`, `seniority`, `job_description`, `company_description`, `business_context`, `follow_up_type`
- **No hardcoded prompt strings in Python code**

### 9.4 Parser Contract (STRICT — ADR-019)

- **Class:** `services/humanizer/follow_up/follow_up_parser.py`
- **Raises `FollowUpParseError` (always with `.raw`) on:** markdown fence, extra surrounding text, invalid JSON, non-object root, missing fields, unknown fields, schema violations
- **`FollowUpOutput` schema (frozen, extra=forbid):**
  ```json
  {
    "follow_up_question": "<string, contains '?'>",
    "reasoning": "<string>",
    "topic_anchor": "<string>",
    "confidence": <float 0.0..1.0>
  }
  ```
- Guard always called after successful parse

### 9.5 Guard Design (17 Deterministic Rules)

| ID | Rule |
|----|------|
| FG001 | min_length ≥ `settings.follow_up_min_length` |
| FG002 | max_length ≤ 2000 |
| FG003 | keyword_overlap ≥ `settings.follow_up_min_keyword_overlap` |
| FG004 | area_anchor token present in output |
| FG005 | not_duplicate (Levenshtein similarity < 0.70) |
| FG006 | not_json |
| FG007 | not_markdown |
| FG008 | no_placeholder (`{{...}}`) |
| FG009 | has_question_mark |
| FG010 | no_code_block |
| FG011 | no_html_xml |
| FG012 | no_prompt_injection |
| FG013 | no_role_override |
| FG014 | no_system_leakage |
| FG015 | no_sql_payload |
| FG016 | no_python_payload |
| FG017 | no_template_text |

- `accepted = len(failed_rules) == 0`
- `score` is diagnostic only; never influences `accepted`
- `failed_rules` use stable FG-prefixed codes

### 9.6 Failure Recovery

| Failure | Recovery |
|---------|----------|
| No `last_question_context` | `FollowUpSkippedEvent(reason="no_context")` → V1.0 fallback |
| `FollowUpParseError` | `FollowUpSkippedEvent(reason="parse_error")` → V1.0 fallback |
| Guard rejected | `FollowUpSkippedEvent(reason="guard_rejected", failed_rules=...)` → V1.0 fallback |
| Generic LLM exception | Logged `follow_up_generation_failed`; V1.0 fallback |
| `supports_follow_up=False` | V1.1 skipped silently; V1.0 runs |
| `follow_up_count >= max` | `_is_follow_up_eligible` returns False; V1.0 runs |

Interview is **never interrupted** by follow-up failures.

### 9.7 State Updates

| Field | When updated |
|-------|-------------|
| `follow_up_count` | +1 on V1.1 acceptance |
| `last_humanizer_follow_up` | `True` on V1.1 acceptance |
| `follow_up_eligible_indices` | Set once at session start; never modified |
| `events` | Appended with `FollowUpTriggeredEvent` or `FollowUpSkippedEvent` |

### 9.8 Configuration (Single Source of Truth: `settings.py`)

All 12 follow-up parameters live in `infrastructure/config/settings.py`:
`follow_up_score_threshold`, `max_follow_ups_per_interview`, `follow_up_percentage`, `follow_up_selector_policy`, `follow_up_min_length`, `follow_up_max_input_chars`, `follow_up_min_keyword_overlap`, `follow_up_allowed_areas`, `follow_up_allowed_types`, `follow_up_logging_enabled`, `follow_up_sanitize_input`, `humanizer_follow_up_enabled`.

`MAX_FOLLOW_UPS_PER_INTERVIEW` in `app/settings/constants.py` is a re-export from `settings.max_follow_ups_per_interview` for backward compatibility.

---

### 9.9 M2 Backlog (deferred from M1)

- Score gating on V1.1 path (ADR-E: intentionally omitted from M1)
- Guard retry (max 1 retry on guard failure) — ADR-F
- `humanizer_v2.txt` area anchoring slot
- Event field alignment with ARCH-REVIEW spec
- Batch-mode selector area filter refinement
- Distinct `reason="llm_fail"` event code

---

## 10. Knowledge Gap Engine

### 10.1 Gap Detection Algorithm

1. Collect all `EvaluationResult` objects from a completed session.
2. For each evaluation dimension across all answers, compute `mean_score` and `variance`.
3. Identify dimensions where `mean_score < GAP_THRESHOLD` (default: 6.5 / 10.0).
4. Cluster weak dimensions by taxonomy node using cosine similarity on dimension-topic embeddings.
5. For each cluster, compute `severity_score` and `confidence_score`.
6. Filter clusters where `confidence_score < CONFIDENCE_MINIMUM` (default: 0.6) — insufficient evidence.
7. Rank surviving clusters by severity descending.

### 10.2 Classification Taxonomy

```
KnowledgeGapTaxonomy
├── Computer Science Fundamentals
│   ├── Algorithms & Data Structures
│   │   ├── Sorting & Searching
│   │   ├── Graph Algorithms
│   │   ├── Dynamic Programming
│   │   └── Complexity Analysis
│   └── System Design
│       ├── Distributed Systems
│       ├── Database Design
│       ├── API Design
│       └── Caching & Scalability
├── Programming Languages
│   ├── Python
│   ├── JavaScript / TypeScript
│   └── SQL
├── Software Engineering Practices
│   ├── Testing & TDD
│   ├── Clean Code & SOLID
│   ├── Design Patterns
│   └── Code Review
├── Domain Knowledge
│   ├── Machine Learning
│   ├── Backend Engineering
│   ├── Frontend Engineering
│   └── DevOps & Infrastructure
└── Behavioral & Communication
    ├── Problem Decomposition
    ├── Technical Communication
    └── Trade-off Analysis
```

### 10.3 Severity Scoring

```
severity = (GAP_THRESHOLD - mean_score) / GAP_THRESHOLD
         × (1 + recurrence_weight × recurrence_count)
         × topic_importance_weight
```

- `recurrence_weight`: 0.2 per additional occurrence of the same gap across answers
- `topic_importance_weight`: configured per taxonomy leaf node based on role expectations

### 10.4 Confidence Scoring

```
confidence = min(evidence_count / MIN_EVIDENCE, 1.0)
           × (1 - score_variance / MAX_VARIANCE)
```

- `MIN_EVIDENCE`: 2 answers exhibiting the gap
- `MAX_VARIANCE`: 4.0 (high variance = inconsistent performance, lower confidence)

### 10.5 Learning Roadmap Generation

- Roadmap is assembled by `RoadmapBuilder` (Builder Pattern).
- Each gap maps to a `RoadmapItem` with:
  - `priority`: computed from severity (1 = highest)
  - `estimated_hours`: derived from taxonomy node metadata
  - `prerequisites`: taxonomy parent nodes not yet mastered
  - `resources`: hydrated by `ResourceRecommendationEngine`
- Roadmap is pruned to max 5 items for actionability.

### 10.6 Study Resource Recommendation Interface

```
ResourceRecommendationEngine.recommend(
  gap: Gap,
  candidate_profile: CandidateProfile,
  max_results: int = 3
) → List[ResourceRecommendation]
```

- Resource catalog stored in dedicated ChromaDB collection `resources`.
- Each resource embedding includes: title, topic tags, difficulty, resource type.
- Retrieval query embeds: `gap.taxonomy_node + " " + gap.topic + " " + candidate_profile.seniority`.
- Results filtered by `resource.difficulty` compatible with candidate seniority.

---

## 11. UI Evolution

### 11.1 Design System Specification

**Typography:**
- Display: Inter, 700 weight, sizes: 2xl (24px), xl (20px)
- Body: Inter, 400/500 weight, sizes: base (16px), sm (14px)
- Mono: JetBrains Mono, 400 weight — code blocks, SQL, output panels
- Line height: 1.6 for body, 1.2 for display

**Spacing scale:** 4px base unit. Scale: 4, 8, 12, 16, 24, 32, 48, 64px

**Color palette:**
```
Light mode:
  Background:    #FFFFFF / #F8F9FA
  Surface:       #FFFFFF with border #E5E7EB
  Primary:       #2563EB (brand blue)
  Primary hover: #1D4ED8
  Success:       #16A34A
  Warning:       #D97706
  Error:         #DC2626
  Text primary:  #111827
  Text secondary:#6B7280
  Code bg:       #F3F4F6

Dark mode:
  Background:    #0F172A
  Surface:       #1E293B with border #334155
  Primary:       #3B82F6
  Primary hover: #60A5FA
  Success:       #22C55E
  Warning:       #F59E0B
  Error:         #F87171
  Text primary:  #F1F5F9
  Text secondary:#94A3B8
  Code bg:       #0F172A
```

**Icons:** Lucide React icon set (consistent with Shadcn UI); 20px default size, 16px inline.

### 11.2 Accessibility Requirements (WCAG 2.1 AA)

- All text: contrast ratio ≥ 4.5:1 (normal text), ≥ 3:1 (large text)
- Interactive elements: focus ring always visible; minimum target size 44×44px
- ARIA roles for interview state changes (question presented, answer captured, evaluation displayed)
- Screen reader announcements for score reveals and coaching feedback
- Keyboard navigation for all primary interview interactions
- No color-only information (always paired with icon or text)
- Error messages surfaced as text, not toast-only

### 11.3 Dark Mode Design

- System preference detection via `prefers-color-scheme` media query.
- Manual toggle stored in `localStorage`; persists across sessions.
- All color tokens swap via CSS custom properties; no component-level conditional logic.
- Code editor background follows dark mode: `#0F172A` surface with syntax highlighting adapted.

### 11.4 Candidate Experience Flows

**Flow 1: New Session**
```
Welcome screen → Role/Domain selection → Difficulty selection
→ Session briefing (question count, format, timing)
→ Interview start confirmation
→ Question presentation → Answer input → Submission
→ Evaluation feedback (progressive reveal)
→ Optional hint request → Optional follow-up question
→ Next question or session close
→ Report and roadmap presentation → Export
```

**Flow 2: Progress Review**
```
Dashboard → Historical sessions list → Session detail
→ Score trends chart → Gap evolution → Roadmap progress
→ Start new session (pre-populated with weak areas)
```

**Flow 3: Replay Session**
```
Session list → Select session → Replay mode selection (full / selective)
→ Node-by-node reconstruction → Diff view (if re-evaluated)
→ Export diff report
```

### 11.5 Responsive Breakpoints

| Breakpoint | Min-width | Layout |
|------------|-----------|--------|
| Mobile | 0px | Single column; collapsible panels; bottom-fixed CTA |
| Tablet | 768px | Two-column: question left, answer/feedback right |
| Desktop | 1024px | Three-panel: sidebar + question + evaluation |
| Large desktop | 1440px | Full-width with max-content-width 1200px constraint |

### 11.6 Component Library Choices

- **Foundation:** Gradio (existing; retained for state-driven interview flow)
- **Custom UI components:** Tailwind CSS utility classes; no additional framework dependency
- **Code editor:** CodeMirror 6 (lightweight, framework-agnostic; replaces textarea for code input)
- **Chart/visualization:** Recharts (progress trends, score radar chart)
- **Icons:** Lucide (consistent, tree-shakable)
- **Transitions:** CSS transitions only; no heavy animation library

---

## 12. Metrics

### 12.1 Technical KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-end session completion rate | ≥ 95% | Sessions completed / sessions started |
| Graph node failure rate | < 1% | Failed node executions / total node executions |
| Evaluation pipeline latency (p95) | < 8s | Time from answer submission to evaluation display |
| LLM retry rate | < 5% | Retried calls / total calls |

### 12.2 Business KPIs

| Metric | Target |
|--------|--------|
| Candidate satisfaction score (post-session survey) | ≥ 4.2 / 5.0 |
| Coaching actionability score (roadmap follow-up) | ≥ 70% of candidates rate roadmap as actionable |
| Return session rate | ≥ 40% within 30 days |
| Knowledge gap detection precision | ≥ 80% (validated against human reviewer) |

### 12.3 LLM KPIs

| Metric | Target |
|--------|--------|
| Mean tokens per session | < 60,000 (V1.0 baseline: ~90,000) |
| p95 LLM call latency | < 5s |
| Cost per interview session (USD) | < $0.15 (V1.0 baseline: ~$0.30) |
| Cache hit rate (L1 + L2) | ≥ 30% of calls served from cache |
| Evaluation call batching ratio | ≥ 80% of evaluation calls batched |

### 12.4 Reliability KPIs

| Metric | Target |
|--------|--------|
| Session-level error rate | < 2% |
| OutputValidationError rate | < 1% |
| PromptInjectionDetected rate | Monitored; no target (threat intelligence) |
| Hallucination fallback trigger rate | < 0.5% of LLM calls |

### 12.5 Security KPIs

| Metric | Target |
|--------|--------|
| Injection detection rate on test corpus | ≥ 95% |
| False positive rate (legitimate input blocked) | < 0.5% |
| Prompt leakage incidents | 0 |
| Audit log coverage | 100% of LLM calls logged |

### 12.6 Cost KPIs

| Metric | Target |
|--------|--------|
| Monthly LLM spend vs. V1.0 baseline | ≥ 40% reduction |
| Token budget overrun rate | < 5% of sessions |
| L2 cache hit rate | ≥ 15% |

### 12.7 Coaching KPIs

| Metric | Target |
|--------|--------|
| Readiness delta (score improvement across sessions) | ≥ +0.5 points per dimension per session pair |
| Gap recurrence rate | < 30% of detected gaps recur after roadmap delivery |
| Roadmap completion rate (self-reported) | ≥ 50% within 60 days |

---

## 13. Risk Register

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| JavaScript vm2 sandbox escape | Medium | Critical | Pin vm2 version; apply seccomp at OS level; add integration tests for escape patterns; regular CVE monitoring |
| TypeScript tsc transpile failures on adversarial input | Medium | High | Run tsc in isolated subprocess with timeout; treat transpile error as submission failure; sandbox tsc itself |
| ChromaDB capacity limits with growing corpus | Low | Medium | Shard by domain; implement corpus pruning policy; monitor collection size |
| SQLite progress store corruption on crash | Low | High | WAL mode enabled; daily backup to flat file; integrity check on startup |
| LangGraph state schema migration breaks replay | Medium | High | Snapshot format versioned (ADR-023); migration scripts required before any state schema change |

### Product Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Knowledge gap taxonomy too coarse | Medium | Medium | Taxonomy is versioned and extensible; iterative refinement post-launch based on candidate feedback |
| Roadmap recommendations not actionable | Medium | High | A/B test resource catalog quality; collect post-roadmap feedback; curate catalog manually for top 20 gap types |
| Follow-up questions perceived as repetitive | Low | Medium | Enforce topic diversity check across session follow-ups; cap same-topic follow-ups to 1 |
| Multi-language coding questions unevenly distributed | Medium | Medium | Seed JS/TS corpus with ≥50 problems before enabling multi-language sessions |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OpenAI API rate limits exceeded | Medium | High | Retry with exponential backoff (existing); add per-session rate limit governor in CostOptimizer |
| Token budget consistently exceeded in long sessions | Medium | Medium | Adjust default budget after V1.1 telemetry; add real-time budget warning in UI |
| Progress store SQLite file growth | Low | Low | Implement session archival policy; compress snapshots after 90 days |

### Security Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Prompt injection bypasses sanitization layer | Low | Critical | Defense-in-depth: sanitization + structural prompt design + output validation; no single point of failure |
| ML injection classifier adversarial evasion | Medium | High | Combine classifier with regex (complementary signals); regular classifier retraining on new patterns |
| Cached prompt response served to wrong session | Very Low | High | Cache key includes session_id for L1; L2 cache keyed on content hash only (prompt-level, not session-level) |

### LLM Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| gpt-4o-mini model deprecation | Medium | High | Adapter pattern isolates model identity; model swap requires config change only (ADR-013 prompt registry versioned) |
| LLM evaluation quality degrades with cheaper models | Medium | Medium | A/B test model routing thresholds; maintain quality gate (OutputValidationLayer score consistency check) |
| Hallucinated test results in narrative | Low | High | OutputValidationLayer cross-references actual ExecutionResult; fabricated claims are caught before display |
| Evaluation score drift across model versions | Medium | Medium | Pin model version in settings; run evaluation benchmark on model upgrade |

---

## 14. Architecture Decision Records (V1.1/V1.2)

### ADR-016: Multi-language Coding Engine Strategy

**Context:** The V1.0 coding engine is Python-only. Frontend and full-stack interview scenarios require JavaScript and TypeScript support. Extending the existing `CodingExecutor` directly would violate OCP and increase coupling.

**Decision:** Adopt the Strategy Pattern. Refactor `CodingExecutor` into `PythonLanguageStrategy` implementing `LanguageAdapterPort`. Add `JavaScriptLanguageStrategy` and `TypeScriptLanguageStrategy` as independent implementations. Introduce `LanguageAdapterFactory` for runtime selection.

**Rationale:**
- Strategy Pattern isolates language-specific execution from shared evaluation logic.
- `EvaluationEngine` and `SignalExtractor` require no changes.
- New languages are added by implementing `LanguageAdapterPort` without modifying existing strategies.
- Python regression risk is minimal: `PythonLanguageStrategy` is a structural rename, not a behavioral change.

**Alternatives Rejected:**
- *Extend CodingExecutor with language flags:* Violates OCP; creates a multi-responsibility class.
- *Separate service per language:* Duplicates evaluation logic; increases maintenance surface.
- *Subprocess-based execution for all languages:* Security risk without per-language sandboxing.

**Consequences:**
- Introduces `LanguageAdapterFactory`; dependency injection required in graph nodes.
- JS/TS corpus seeding required before go-live; follow-up generation must support multi-language.
- Test suite must cover all three strategies independently.

---

### ADR-017: Prompt Security Layer Architecture

**Context:** V1.0 has no prompt injection defense. Candidate answer text and business context fields are interpolated into prompts without sanitization. Direct and indirect injection are realistic attack vectors.

**Decision:** Introduce a dedicated `PromptSecurityLayer` as a pipeline of pluggable `SanitizationStrategy` implementations, positioned between user input ingestion and prompt template rendering. The layer is mandatory for all user-supplied inputs; it cannot be bypassed by individual services.

**Rationale:**
- Centralizing sanitization in one layer ensures consistent coverage across all LLM call types.
- Strategy Pattern allows adding new detection methods (e.g., ML classifier) without changing the pipeline.
- Chain of Responsibility ensures each strategy is independently testable.
- Audit logging in the layer provides complete coverage of all sanitization events.

**Alternatives Rejected:**
- *Per-service sanitization:* Inconsistent coverage; high risk of omission.
- *Sanitization in prompt templates:* Templates are not appropriate for security logic; mixing concerns.
- *Single monolithic sanitizer:* Difficult to extend; cannot apply different strategies per field type.

**Consequences:**
- All existing LLM call paths must be audited and updated to pass input through the security layer.
- `SanitizationStrategyFactory` must be integrated into application bootstrap.
- False positive risk (legitimate inputs blocked) must be monitored and calibrated.

---

### ADR-018: Output Validation Layer Position in Pipeline

**Context:** V1.0 validates LLM outputs via Pydantic schema parse only. Business rule violations (out-of-range scores, empty narratives), hallucination markers, and prompt leakage are not detected.

**Decision:** Position the `OutputValidationLayer` immediately after every LLM call response, before the response is returned to any service. The layer is integrated into `ObservingLLMAdapter` as a post-call hook, ensuring no service ever receives an unvalidated LLM output.

**Rationale:**
- Placing validation in the adapter means all LLM call types (evaluation, narrative, hints, follow-ups) are covered without per-service changes.
- ObservingLLMAdapter already wraps all calls; adding the validation hook preserves the existing decorator pattern.
- Defense-in-depth: schema validation (Pydantic) + business rules + hallucination detection in sequence.

**Alternatives Rejected:**
- *Per-service output validation:* Duplicates validation logic; inconsistent coverage.
- *Validation in graph nodes:* Mixes orchestration and validation concerns; graph nodes become bloated.
- *Pre-consumer validation middleware:* Harder to retrofit into existing call chain without architectural disruption.

**Consequences:**
- `ObservingLLMAdapter` gains a validation hook dependency; must receive `OutputSchema` and `ValidationPolicy` per call.
- All existing LLM call sites must pass the expected output schema.
- Retry logic now lives in the adapter layer; services become simpler.

---

### ADR-019: Follow-up Question Engine Design (Revised — V1.1 M1)

**Context:** V1.0 has a `HumanizerPolicyEngine` that can emit a `FOLLOW_UP` decision for V1.0 humanizer sessions. The original TDS §9 designed a corpus-first, `InterviewReasoner`-gated, ChromaDB-backed follow-up engine. During M1-1 Architecture Review, this design was revised to a dedicated Humanizer subsystem pipeline that does not require `InterviewReasoner`, ChromaDB corpus, or a separate `FollowUpService`.

**Decision (V1.1 M1 Shipped):**
1. `FollowUpSelector` pre-selects eligible indices once at session start (slot-based, deterministic).
2. A dedicated V1.1 pipeline (`FollowUpPromptBuilder` → `follow_up_generation.txt` → LLM → `FollowUpParser` → `FollowUpGuard`) runs in `QuestionNode` at eligible slots.
3. The V1.0 Humanizer path is retained as-is; V1.1 pipeline is additive and non-destructive.
4. Graceful fallback to V1.0 on any V1.1 failure.
5. `settings.py` is the single source of truth for all follow-up configuration.
6. Score gating intentionally omitted from V1.1 (see ADR-E below).

**Rationale:**
- Avoids introducing `InterviewReasoner`, ChromaDB follow-up corpus, and embedding calls in M1.
- Dedicated pipeline (SRP) maintains independence from V1.0 humanizer.
- Slot-based selection is fully deterministic and testable without real LLM.
- All 17 guard rules are deterministic; no embeddings required in V1.1.

**Alternatives Rejected:**
- *Corpus-first (original TDS §9 design):* Requires ChromaDB seeding; deferred to V1.2.
- *InterviewReasoner gating:* Out of scope for M1; deferred to M2.
- *Retry on guard failure:* Risk of compounding latency in happy path; deferred to V1.2 (ADR-F).

**Consequences:**
- Follow-up triggering is slot-based (pre-selected at session start), not score-based.
- Follow-up corpus strategy deferred to V1.2.
- `FollowUpSkippedEvent` replaces `FollowUpCapExceededEvent` (H7 — naming simplified).

---

### ADR-024: Follow-up Selector Independence from Score Gating (ADR-E)

**Status: Accepted**

**Context:** The M1-3 Acceptance Criteria defined a FOLLOW_UP_SCORE_THRESHOLD gating mechanism that would condition V1.1 pipeline entry on `last_answer_score >= threshold`. During M1-5D/M1-6 implementation, this was intentionally removed.

**Decision:** V1.1 does not gate follow-up generation on answer quality scores. Slot-based selection (pre-determined at session start) is the only gating mechanism for V1.1.

**Rationale:** Score propagation across the LangGraph node sequence introduces ordering dependencies. Slot-based approach is deterministic and avoids coupling to the evaluation subsystem. Score gating can be added in M2 as an additional filter inside `_is_follow_up_eligible`.

**Consequences:** Follow-up may be attempted for any quality answer at an eligible slot. The `FollowUpGuard` answer-relevance rule (FG003) provides a content-based quality gate.

---

### ADR-025: Guard Retry Deferred to V1.2 (ADR-F)

**Status: Accepted**

**Context:** The original ARCH-REVIEW-M1-1 proposed optional retry on guard rejection (max 1 retry). Not implemented in M1.

**Decision:** Guard retry not implemented in V1.1 M1. A single guard rejection immediately emits `FollowUpSkippedEvent` and falls back to V1.0.

**Rationale:** Retry doubles worst-case LLM call latency. V1.1 baseline establishes guard accuracy data; retry strategy should be informed by real rejection rates before implementation.

**Consequences:** Guard rejections result in V1.0 fallback. `FollowUpSkippedEvent(reason="guard_rejected")` carries `failed_rules` for analysis.

---

### ADR-026: Dedicated Follow-up Prompt File (ADR-C)

**Status: Accepted**

**Context:** TDS originally implied a `humanizer_v2.txt` prompt. Implementation uses a dedicated `follow_up_generation.txt`.

**Decision:** Follow-up generation uses `app/prompts/humanizer/follow_up_generation.txt`, loaded via `PromptLoader`. Not a modification of existing `humanizer_v1.txt` or a `humanizer_v2.txt`.

**Rationale:** Separation of concerns (SRP). The V1.0 humanizer prompt and follow-up prompt serve different purposes. Sharing a prompt creates coupling and reduces clarity.

**Consequences:** Any changes to follow-up LLM behavior are isolated to `follow_up_generation.txt` without risk of affecting V1.0 humanizer.

---

### ADR-027: FollowUpSelector Determinism (ADR-D)

**Status: Accepted**

**Context:** M1-3 required deterministic slot selection.

**Decision:** `FollowUpSelector.select()` is a pure function. Same `(total_questions, planned_areas, settings_snapshot)` always produces same `frozenset[int]`. No random seed, no mutable state.

**Rationale:** Determinism enables reproducible testing without mocking random; simplifies debugging of session behavior.

**Consequences:** Distribution algorithm uses fixed center-offset logic, not random sampling.

---

---

### ADR-020: Knowledge Gap Engine Classification Approach

**Context:** V1.0 produces evaluation scores per answer but no cross-session synthesis or gap classification. Candidates receive no structured learning guidance beyond the coaching narrative.

**Decision:** Implement a dedicated `KnowledgeGapEngine` using a canonical `GapTaxonomy` (hierarchical, stored in `domain/gap_taxonomy/`). Gap detection uses score thresholding + embedding-based clustering. Taxonomy is versioned and extensible. Severity and confidence scores are separately computed.

**Rationale:**
- Separating taxonomy definition from detection logic allows independent evolution of both.
- Embedding-based clustering groups related weak areas even when named differently across evaluation dimensions.
- Confidence scoring prevents low-evidence gaps from appearing in the roadmap (false positives harm trust).
- Versioned taxonomy supports A/B testing of classification granularity.

**Alternatives Rejected:**
- *Rule-based keyword matching:* Brittle; vocabulary-dependent; fails on paraphrased topics.
- *Single flat gap list (no taxonomy):* No prioritization structure; roadmap assembly becomes arbitrary.
- *LLM-based gap classification per answer:* High cost; inconsistent classification across sessions.

**Consequences:**
- `GapTaxonomy` must be defined and reviewed before V1.2 launch.
- `ResourceRecommendationEngine` must map to taxonomy leaf nodes; resource catalog must be tagged.
- Taxonomy version changes require re-running gap detection on historical sessions (migration script).

---

### ADR-021: Cost Optimization and Model Routing Strategy

**Context:** V1.0 routes all LLM calls to gpt-4o-mini regardless of quality requirements. No caching, no batching, no budget governance. Estimated cost per session is ~$0.30.

**Decision:** Introduce `CostOptimizer` as an interceptor between the service layer and LLM adapters. Implement: (1) per-call model routing based on `ModelRoutingPolicy`, (2) two-tier response caching (L1 in-memory, L2 SQLite), (3) evaluation dimension batching (7 dimensions → 1 call), (4) token budget per session with graduated degradation.

**Rationale:**
- Interceptor pattern allows cost optimization without changing service or adapter code.
- Evaluation batching delivers the highest single token savings (~40% of evaluation calls).
- Two-tier caching serves hints and explanations from cache; no LLM call after first generation.
- Token budget governance prevents runaway costs on adversarially long sessions.

**Alternatives Rejected:**
- *Fine-tuned model for all calls:* High upfront cost; knowledge cutoff risk; maintenance burden.
- *Per-service caching:* Inconsistent coverage; no cross-service deduplication.
- *Static model assignment:* No adaptability to budget pressure; suboptimal on routable call types.

**Consequences:**
- `CostOptimizer` must receive per-call `OutputSchema` to correctly route and cache typed responses.
- L2 cache invalidation policy must be defined and enforced on every prompt template change.
- Evaluation batching increases prompt size; context window limits must be monitored.

---

### ADR-022: Progress Tracking Persistence Backend

**Context:** V1.0 is entirely stateless between sessions. No cross-session persistence exists. Progress Tracker requires durable storage with query capability.

**Decision:** Use a dedicated SQLite file (separate from the in-memory SQLite used for SQL evaluation). Persist to `~/.ai_interview_simulator/progress.db`. Schema: `sessions`, `evaluation_results`, `knowledge_gaps`, `snapshots`. WAL mode enabled. Accessed only through `ProgressStore` adapter.

**Rationale:**
- SQLite is already a project dependency (in-memory SQL evaluation); no new infrastructure dependency.
- File-based SQLite provides durability without requiring a server process.
- WAL mode supports concurrent read access by ReplayEngine while ProgressTracker is writing.
- `ProgressStore` adapter isolates SQL from domain logic; schema migration is contained.

**Alternatives Rejected:**
- *PostgreSQL:* Requires server; overkill for single-user deployment; adds operational burden.
- *JSON flat files per session:* No query capability; poor performance for trend analysis.
- *Shared in-memory SQLite:* Not durable; wiped on process exit.

**Consequences:**
- `infrastructure/progress_store/` must implement schema migration tooling.
- Progress DB path must be configurable (for testing: temp directory; for production: user home).
- Backup strategy required: WAL checkpointing on session close; optional export to JSON.

---

### ADR-023: Replay Engine Storage Format

**Context:** ReplayEngine requires access to historical LangGraph state snapshots. States must be reproducible without re-invoking LLMs.

**Decision:** Serialize LangGraph state at every node transition as JSON. Store in `snapshots` table of progress.db with columns: `session_id`, `node_name`, `sequence_number`, `state_json`, `timestamp`, `schema_version`. State JSON is Pydantic-serialized. Schema version is stored per snapshot for forward-compatible migration.

**Rationale:**
- JSON serialization is human-readable, debuggable, and portable.
- Pydantic serialization ensures all state fields are typed and validated before storage.
- Schema version per snapshot enables targeted migration of old snapshots without full replay failure.
- Storing at every node transition (not just session end) enables mid-session replay and debugging.

**Alternatives Rejected:**
- *Python pickle:* Security risk (arbitrary code execution on deserialization); not forward-compatible.
- *MessagePack:* Not human-readable; harder to debug without tooling.
- *Store only session summary (not per-node state):* Insufficient for selective replay and node-level debugging.

**Consequences:**
- Snapshot table will grow; archival policy needed (compress after 90 days; delete after 365 days).
- Any LangGraph state schema change requires a migration script before deployment.
- `ReplayEngine` must handle schema version mismatches gracefully (skip incompatible nodes with warning).

---

## 15. Migration Plan

### V1.0 → V1.1

**Principles:**
- All migrations are backward-compatible within a session (no data loss).
- Regression checkpoints validate that V1.0 behavior is preserved after each step.
- Steps are ordered by dependency: security layer before any LLM call changes; CostOptimizer after security layer.

**Step 1: Security Layer Integration**
- Introduce `security/` package with `PromptSecurityLayer`, `PromptValidationLayer`.
- Audit all 6 LLM call sites; route inputs through `PromptSecurityLayer`.
- Deploy with `SECURITY_MODE=monitor` (log-only, no blocking) for 24h.
- Regression checkpoint: all existing evaluation tests pass; zero false positives in monitor logs.
- Switch to `SECURITY_MODE=enforce`.

**Step 2: Output Validation Layer**
- Implement `OutputValidationLayer`; integrate as post-call hook in `ObservingLLMAdapter`.
- Deploy with `VALIDATION_MODE=monitor` for 24h; collect schema failure baseline.
- Regression checkpoint: schema failure rate < 0.5% on 100 test sessions.
- Switch to `VALIDATION_MODE=enforce`.

**Step 3: Interview Reasoner**
- Implement `InterviewReasoner`; integrate into LangGraph follow-up decision node.
- Regression checkpoint: follow-up trigger rate remains within 10% of V1.0 baseline.
- A/B test: 50% of sessions use Reasoner; compare session completion rate.

**Step 4: Cost Optimizer — Batching and Caching**
- Implement evaluation dimension batching; deploy to 10% of sessions.
- Regression checkpoint: evaluation score distributions statistically equivalent before/after batching.
- Implement L1 cache; measure hit rate after 1 week.
- Implement L2 cache; measure cross-session hit rate after 2 weeks.

**Step 5: Knowledge Gap Engine (partial)**
- Implement gap detection and classification; store gap reports in progress.db.
- Do not surface to UI yet (internal only).
- Regression checkpoint: gap detection runs without error on all completed sessions.

**Step 6: Progress Tracker**
- Create `progress.db` schema; implement `ProgressStore` adapter.
- Instrument all session completions to write `ProgressRecord`.
- Regression checkpoint: all sessions write successfully; no performance degradation on session close.

**Step 7: V1.1 Smoke Test**
- Run 50 end-to-end sessions across all pipelines (written, coding, SQL).
- Verify: cost per session ≤ target, no security regressions, all exports valid.

---

### V1.1 → V1.2

**Step 1: Multi-language Coding Engine**
- Refactor `CodingExecutor` → `PythonLanguageStrategy` (no behavior change).
- Introduce `LanguageAdapterPort` and `LanguageAdapterFactory`.
- Wire Python through factory; run full Python regression suite.
- Implement `JavaScriptLanguageStrategy`; seed JS corpus (≥50 problems).
- Integration test: JS coding sessions end-to-end.
- Implement `TypeScriptLanguageStrategy`; run TS integration tests.

**Step 2: Knowledge Gap Engine — Full Integration**
- Implement `ResourceRecommendationEngine`; build resource ChromaDB collection.
- Surface gap report and learning roadmap in Gradio UI.
- Regression checkpoint: gap report generation adds < 2s to session close.

**Step 3: Replay Engine**
- Implement snapshot serialization in `ProgressTracker` (all node transitions).
- Implement `ReplayEngine`; expose via CLI.
- Integration test: replay 10 historical sessions; verify diff accuracy.

**Step 4: UI Evolution**
- Implement dark mode (CSS custom properties; system preference detection).
- Implement progress dashboard (score trends, gap evolution).
- Implement replay UI flow.
- Implement CodeMirror 6 code editor.
- Accessibility audit: automated (axe-core) + manual keyboard navigation test.

**Step 5: REST API Layer (V1.2)**
- Design OpenAPI spec for core session endpoints.
- Implement thin FastAPI translation layer over existing services.
- No business logic in API layer; all calls delegate to service layer.
- Integration test: API endpoints cover session init, answer submission, evaluation retrieval, report export.

**Step 6: V1.2 Smoke Test**
- Run 100 end-to-end sessions: Python + JS + TS.
- Verify: all KPI targets met; no regressions from V1.1.

---

## 16. Master Implementation Plan

> **V1.1 M1 STATUS: FROZEN (2026-06-30)**
> The TDS §16 plan below reflects the original pre-implementation plan for reference.
> The follow-up engine (originally called M1-2) was implemented in the single M1 milestone.
> M2 starts from the M1 frozen baseline. See §9.9 for M2 backlog items.

### V1.1 Implementation Roadmap

#### Milestone M1: Follow-up Question Engine — COMPLETED (Frozen 2026-06-30)

**Status: FROZEN**

**Delivered:**
- `FollowUpSelector` (deterministic slot selection, ADR-027)
- `FollowUpPromptBuilder` + `follow_up_generation.txt` (ADR-026)
- STRICT `FollowUpParser` + `FollowUpParseError`
- `FollowUpGuard` (17 deterministic rules FG001–FG017)
- `HumanizerService.generate_follow_up()`
- `QuestionNode` V1.1 integration with graceful V1.0 fallback
- `FollowUpTriggeredEvent`, `FollowUpSkippedEvent`
- `settings.py` as single configuration source
- 44/44 Acceptance Gates PASS; 186 dedicated tests; 1,760 total tests

**M2 Baseline:** All future follow-up improvements build on this frozen baseline.

---

#### Milestone M1-1 (Original Plan): Security Foundation

**Audit (before starting):**
- Review all 6 LLM call sites; document input field types and origins.
- Review `app/prompts` registry; identify all template slots that accept user input.
- Assess existing Pydantic models for completeness of type coverage.

**Acceptance Criteria:**
- `PromptSecurityLayer` blocks 100% of patterns in injection test corpus.
- `PromptValidationLayer` rejects prompts exceeding context window.
- `OutputValidationLayer` catches all schema violations in test dataset.
- Zero false positives on 50 legitimate session test runs.
- All LLM call sites instrumented with `SanitizationEvent` and `OutputValidationEvent` audit logs.

**Implementation Steps (ordered):**
1. Define `SanitizationStrategy` interface and `SanitizationEvent` domain event.
2. Implement `UnicodeNormalizationStrategy` and `InvisibleCharacterRemovalStrategy`.
3. Implement `InjectionPatternMatchStrategy` (regex library).
4. Implement `MLInjectionClassifierStrategy` (local distilbert; load on startup).
5. Implement `PromptSecurityLayer` pipeline; `SanitizationStrategyFactory`.
6. Implement `PromptValidationLayer` (structural + length + context window checks).
7. Implement `OutputValidationLayer`; integrate as hook in `ObservingLLMAdapter`.
8. Define `PromptInjectionDetectedError`, `PromptValidationError`, `OutputValidationError` domain exceptions.
9. Audit and update all 6 LLM call sites.
10. Deploy in monitor mode; collect baseline.
11. Switch to enforce mode.

**Validation:**
- Unit tests: each strategy independently; ≥20 injection samples per strategy.
- Integration test: full session with injected inputs; verify block and audit log.
- Performance test: sanitization adds < 50ms per call.

**Regression Checkpoints:**
- All V1.0 evaluation tests pass.
- Session completion rate unchanged from V1.0 baseline.

**Documentation Updates:**
- Update ADR-017, ADR-018 with implementation decisions.
- Update security section of operations runbook.

---

#### Milestone M1-2 (Original Plan — SUPERSEDED): Interview Reasoner and Follow-up Engine

> **SUPERSEDED:** The follow-up engine was implemented in M1 without `InterviewReasoner`, `FollowUpService`, or ChromaDB corpus (see TDS §9 revised, ADR-019 revised). This original plan is retained for historical reference only.

**Audit (before starting):**
- Review V1.0 follow-up decision logic in LangGraph node; document current trigger conditions.
- Measure current follow-up rate across 20 test sessions.
- Review `domain/policies` for existing policy patterns.

**Acceptance Criteria:**
- `InterviewReasoner` emits correct `ReasonerDecision` for all 5 action types across test cases.
- Follow-up cap enforced: no session exceeds 25% follow-up rate.
- Corpus-first selection achieves ≥60% hit rate on seeded corpus.
- Follow-up quality score (human-evaluated, 10 sample questions) ≥ 4.0 / 5.0.

**Implementation Steps (ordered):**
1. Implement `InterviewReasoner` with trajectory assessment logic.
2. Define `FollowUpTrigger`, `DifficultyAdjustmentEvent`, `ReasonerDecision` contracts.
3. Define follow-up cap policy in `domain/policies`.
4. Seed ChromaDB follow-up corpus (≥50 entries per top 5 topic domains).
5. Implement corpus-first selection algorithm in `FollowUpService`.
6. Implement corpus self-growth (validated follow-ups added back).
7. Integrate `InterviewReasoner` into LangGraph follow-up decision node.
8. Implement `FollowUpSkippedEvent` and `FollowUpCapExceededEvent` domain events.

**Validation:**
- Unit tests: `InterviewReasoner` decision logic; 30 scenario test cases.
- Integration test: session with 10 questions; verify cap enforcement.
- Corpus hit rate measured over 50 simulated sessions.

**Regression Checkpoints:**
- Follow-up trigger rate within 10% of V1.0 baseline on equivalent sessions.
- No change to written/SQL pipeline behavior.

**Documentation Updates:**
- Update ADR-019 with implementation decisions.
- Document corpus seeding process and quality gate.

---

#### Milestone M1-3: Cost Optimizer

**Audit (before starting):**
- Baseline token usage per call type across 20 sessions; document in cost dashboard.
- Review all prompt templates for redundancy and compression opportunities.
- Assess evaluation dimension prompt structure for batching feasibility.

**Acceptance Criteria:**
- Evaluation dimension batching consolidates 7 calls into 1; score distributions statistically equivalent (KS test p > 0.05).
- L1 cache achieves ≥20% hit rate within a session on hint-heavy sessions.
- L2 cache achieves ≥15% hit rate across sessions after 1 week.
- Token budget governance: no session exceeds budget without triggering degraded mode.
- Mean cost per session reduced by ≥30% from M1-2 baseline.

**Implementation Steps (ordered):**
1. Implement `CostOptimizer` interceptor class.
2. Implement `ModelRoutingPolicy`; configure routing table in `infrastructure/settings`.
3. Implement L1 in-memory LRU cache; integrate into `CostOptimizer`.
4. Implement evaluation dimension batching; refactor evaluation call in `EvaluationEngine`.
5. Implement L2 SQLite cache in `infrastructure/llm_cache/`.
6. Implement token budget tracking; wire to `SessionState`.
7. Implement budget degradation modes (warning → aggressive truncation → template fallback).
8. Implement `CostEvent` emission; integrate with `ObservingLLMAdapter`.
9. Implement early stopping rules.

**Validation:**
- Unit tests: routing policy logic; 20 call-type test cases.
- Integration test: session with budget set to 50% of default; verify degradation triggers correctly.
- A/B test: 100 sessions with optimizer enabled vs. 100 without; compare cost and quality metrics.

**Regression Checkpoints:**
- Evaluation quality metrics (score distributions) unchanged within statistical tolerance.
- Narrative quality (human spot-check, 10 samples) unchanged.

**Documentation Updates:**
- Update ADR-021 with implementation decisions.
- Update cost monitoring runbook.

---

#### Milestone M1-4: Progress Tracker and Knowledge Gap Engine (Internal)

**Audit (before starting):**
- Review all data written at session close; identify persistence candidates.
- Assess SQLite WAL mode performance under concurrent read/write.
- Review `domain/contracts` for completeness of session summary models.

**Acceptance Criteria:**
- Every completed session writes a `ProgressRecord` to `progress.db` within 500ms of session close.
- `KnowledgeGapEngine` produces a `KnowledgeGapReport` for every completed session.
- Gap detection precision ≥ 75% on 20 manually annotated test sessions.
- No performance degradation on session close (< 500ms added latency).
- Progress history query returns correct trend data for ≥10 historical sessions.

**Implementation Steps (ordered):**
1. Define `progress.db` schema; implement migration framework in `infrastructure/progress_store/`.
2. Implement `ProgressStore` SQLite adapter; test WAL mode concurrency.
3. Implement `ProgressTracker` service; wire to session close in LangGraph node.
4. Implement `ProgressTrackerPort` (abstract); inject concrete adapter.
5. Define `GapTaxonomy` in `domain/gap_taxonomy/`; validate against 50 real session topics.
6. Implement gap detection algorithm (score threshold + embedding clustering).
7. Implement severity and confidence scoring.
8. Implement `KnowledgeGapReportBuilder`.
9. Store gap reports in `progress.db`.
10. Implement `ProgressHistory` query with trend analysis.

**Validation:**
- Unit tests: gap detection on synthetic evaluation results; 30 test cases.
- Integration test: 20 end-to-end sessions; verify progress records and gap reports.
- Query performance test: history query over 100 sessions < 200ms.

**Regression Checkpoints:**
- Session close latency within 500ms of M1-3 baseline.
- All V1.0 export (PDF/JSON) tests pass.

**Documentation Updates:**
- Update ADR-020, ADR-022 with implementation decisions.
- Document `GapTaxonomy` versioning policy.

---

### V1.2 Implementation Roadmap

#### Milestone M2-1: Multi-language Coding Engine

**Audit (before starting):**
- Review `CodingExecutor` for all Python-specific assumptions; document dependency surface.
- Assess `AITestGenerator` prompt templates for Python-specific constructs.
- Review ChromaDB coding problem collection; assess coverage gaps for JS/TS.

**Acceptance Criteria:**
- `PythonLanguageStrategy` is a drop-in replacement for `CodingExecutor`; all Python tests pass.
- `JavaScriptLanguageStrategy` executes JS submissions in isolated vm2 sandbox; sandbox escape tests fail as expected.
- `TypeScriptLanguageStrategy` transpiles and executes TS submissions; type errors are caught and reported.
- JS/TS corpus contains ≥50 problems across algorithm, data structure, and domain-specific categories.
- Evaluation scores for JS/TS sessions are within expected range for seeded problems.

**Implementation Steps (ordered):**
1. Define `LanguageAdapterPort` interface; define `Language` enum (Python, JavaScript, TypeScript).
2. Refactor `CodingExecutor` → `PythonLanguageStrategy`; verify all Python tests pass.
3. Implement `LanguageAdapterFactory`.
4. Implement `JavaScriptLanguageStrategy` with vm2 sandbox; add sandbox escape integration tests.
5. Extend `AITestGenerator` with JS oracle generation; seed JS test corpus.
6. Implement `TypeScriptLanguageStrategy` (tsc transpile → JS execution).
7. Extend `AITestGenerator` with TS oracle generation.
8. Seed ChromaDB with JS/TS coding problems; tag with `language` metadata.
9. Update LangGraph coding node to route through `LanguageAdapterFactory`.
10. Update `InterviewConfig` to accept `supported_languages` list.

**Validation:**
- Unit tests: each strategy; ≥10 problems each.
- Integration test: end-to-end coding session for each language.
- Sandbox security tests: ≥20 escape patterns per language.
- Performance test: JS/TS execution within 5s timeout.

**Regression Checkpoints:**
- All V1.1 Python coding session tests pass.
- Signal extraction and evaluation dimensions unchanged.

**Documentation Updates:**
- Update ADR-016 with implementation decisions.
- Document sandbox security model per language.

---

#### Milestone M2-2: Knowledge Gap Engine — Full UI Integration and Resource Recommendation

**Audit (before starting):**
- Review M1-4 gap reports from 4 weeks of V1.1 sessions; assess taxonomy accuracy.
- Curate initial resource catalog (≥100 resources across top 20 gap types).
- Review Gradio UI extension points for new panels.

**Acceptance Criteria:**
- `ResourceRecommendationEngine` returns ≥2 relevant resources per gap (relevance score ≥ 0.70).
- Learning roadmap displayed in Gradio UI after session close; max 5 items shown.
- Roadmap actionability score ≥ 4.0 / 5.0 (user survey, 20 participants).
- Resource catalog embedded in ChromaDB; retrieval latency < 500ms.
- Gap report included in JSON and PDF exports.

**Implementation Steps (ordered):**
1. Build resource catalog (100+ entries); embed with `text-embedding-3-small`; load into ChromaDB `resources` collection.
2. Implement `ResourceRecommendationEngine`; integrate with `KnowledgeGapEngine`.
3. Implement `RoadmapBuilder`; wire to `KnowledgeGapEngine` output.
4. Integrate roadmap into `NarrativeAssembler` output contracts.
5. Extend `ExportService` to include gap report in PDF and JSON outputs.
6. Implement Gradio roadmap panel (collapsible; per-gap accordion with resources).
7. Implement progress dashboard (score trends chart, gap evolution).

**Validation:**
- Unit tests: `ResourceRecommendationEngine` with 20 gap test cases.
- Integration test: full session → gap report → roadmap → export.
- User acceptance test: 20 participants rate roadmap actionability.

**Regression Checkpoints:**
- Session close latency within 500ms of M2-1 baseline.
- All existing export tests pass.

**Documentation Updates:**
- Update ADR-020 with taxonomy refinements.
- Document resource catalog curation and quality gate process.

---

#### Milestone M2-3: Replay Engine

**Audit (before starting):**
- Review M1-4 snapshot storage; assess completeness and schema stability.
- Identify any LangGraph state fields that are non-serializable; document remediation.
- Assess volume of snapshots after 4 weeks; verify storage within projections.

**Acceptance Criteria:**
- Full replay of any V1.1+ session produces output consistent with original (score delta < 0.1 on deterministic evaluations).
- Selective replay (from specified node) executes correctly without preceding node state.
- Replay diff view correctly identifies and displays evaluation delta.
- CLI replay command available: `interview-simulator replay --session-id <id>`.
- Schema version mismatch handled gracefully (skip incompatible nodes with warning, not error).

**Implementation Steps (ordered):**
1. Verify snapshot completeness in `progress.db` from M1-4; add any missing node transitions.
2. Implement `ReplayEngine.reconstruct(session_id, config)`.
3. Implement `ReplayResultBuilder` and `ReplayDiff` computation.
4. Implement `ReplayEvent` domain event emission.
5. Implement schema version migration handler.
6. Expose `replay` subcommand in CLI.
7. Implement replay UI flow in Gradio (node-by-node view; diff panel).

**Validation:**
- Integration test: replay 20 historical sessions; verify score consistency.
- Edge case test: schema version mismatch; incomplete session snapshot.
- Performance test: full session replay (14 nodes) < 30s.

**Regression Checkpoints:**
- No changes to live interview flow; replay is read-only.
- Progress DB integrity preserved.

**Documentation Updates:**
- Update ADR-023 with implementation decisions.
- Document snapshot archival policy.

---

#### Milestone M2-4: REST API Layer

**Audit (before starting):**
- Review all service interfaces for API-readiness; identify services requiring request/response model wrappers.
- Assess authentication requirements; determine if auth layer is in scope for V1.2.
- Review FastAPI compatibility with existing Pydantic v2 models.

**Acceptance Criteria:**
- REST API exposes: session init, question retrieval, answer submission, evaluation retrieval, report export, progress history.
- All inputs validated by Pydantic request models before service delegation.
- OpenAPI spec generated automatically by FastAPI; all endpoints documented.
- API response time p95 < 10s (bounded by LLM call latency).
- No business logic in API layer; all logic in existing services.

**Implementation Steps (ordered):**
1. Define OpenAPI spec for all V1.2 endpoints.
2. Implement Pydantic request/response models for each endpoint.
3. Implement FastAPI router; wire to service layer.
4. Integrate `PromptSecurityLayer` at API boundary for all user-supplied fields.
5. Implement error handling middleware (service errors → structured HTTP error responses).
6. Generate and validate OpenAPI documentation.
7. Integration test: all endpoints against 10 session scenarios.
8. Add API endpoint monitoring (request rate, latency, error rate) to observability layer.

**Validation:**
- Integration test: API-driven end-to-end session (all endpoints exercised).
- Contract test: OpenAPI spec validated against live responses.
- Security test: injection via API inputs (sanitization layer must block).

**Regression Checkpoints:**
- CLI mode unaffected by API layer addition.
- All V1.1 service-layer tests pass.

**Documentation Updates:**
- Publish OpenAPI spec to `docs/api/`.
- Update ADRs with API layer architectural decisions.

---

### Critical Path

```
M1-1 (Security) → M1-3 (Cost Optimizer) → M2-1 (Multi-lang Coding)
     ↓
M1-2 (Reasoner + Follow-up)
     ↓
M1-4 (Progress Tracker + Gap Engine) → M2-2 (Gap UI + Resources) → M2-3 (Replay)
                                                                          ↓
                                                                    M2-4 (REST API)
```

**Critical path bottlenecks:**
1. **M1-1 (Security Layer):** All subsequent LLM call site changes depend on security integration being stable. Any delay here blocks all milestones.
2. **M1-4 (Progress Tracker):** M2-2 and M2-3 both depend on `progress.db` being populated with at least 4 weeks of data. M1-4 must ship early in V1.1.
3. **M2-1 (Multi-language):** Must complete before M2-2 can test full multi-language gap reports.

---

### Dependency Matrix

| Milestone | Depends On | Blocks |
|-----------|-----------|--------|
| M1-1 (Security) | None | M1-2, M1-3, M1-4, all M2.x |
| M1-2 (Reasoner) | M1-1 | M1-4 (follow-up signals feed gap engine) |
| M1-3 (Cost Optimizer) | M1-1 | M2-1 (batching must support multi-lang calls) |
| M1-4 (Progress Tracker) | M1-2, M1-3 | M2-2, M2-3 |
| M2-1 (Multi-lang) | M1-3 | M2-2 (JS/TS gaps need multi-lang sessions) |
| M2-2 (Gap UI + Resources) | M1-4, M2-1 | M2-3 (roadmap in replay), M2-4 (report endpoint) |
| M2-3 (Replay) | M1-4, M2-2 | M2-4 (replay endpoint) |
| M2-4 (REST API) | M2-2, M2-3 | None |

---

*End of Technical Design Specification — AI Interview Simulator V1.1 / V1.2*
