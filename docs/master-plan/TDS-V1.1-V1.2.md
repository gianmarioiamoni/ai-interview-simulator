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

---

## 17. EPIC-04 Architecture — Interview Reasoner (V1.1 M2)

> This section documents the complete architecture for EPIC-04 as approved in the M2 Architecture Review and Final Contract Freeze (2026-06-30). It is the authoritative design reference for implementation.

### 17.1 Domain Contract Package

All contracts below live in `domain/contracts/reasoning/` and must be frozen before implementation begins.

```
domain/contracts/reasoning/
  __init__.py
  trend.py                       Trend enum
  data_sufficiency.py            DataSufficiency enum
  evidence_type.py               EvidenceType enum
  evidence_signal.py             EvidenceSignal DTO
  profile_dimension.py           ProfileDimension enum
  profile_signal.py              ProfileSignal enum
  dimension_trace.py             DimensionTrace DTO
  signal_trace.py                SignalTrace DTO (+ SignalObservation)
  candidate_profile.py           CandidateProfile DTO
  evidence_store.py              EvidenceStore DTO
  coverage_state.py              CoverageState DTO
  reasoning_history.py           ReasoningHistory DTO + ReasoningEntry
  session_metrics.py             SessionMetrics DTO
  interview_memory.py            InterviewMemory DTO (composed of the above)
  reasoning_confidence.py        ReasoningConfidence DTO
  reasoning_basis.py             ReasoningBasis DTO
  follow_up_recommendation.py    FollowUpRecommendation DTO
  navigation_recommendation.py   NavigationRecommendation DTO
  reasoner_decision.py           ReasonerDecision DTO
  reasoner_input.py              ReasonerInput DTO
```

### 17.2 Frozen Contract Schemas

#### Trend
```
Trend: IMPROVING | STABLE | DECLINING | INSUFFICIENT_DATA
```

#### DataSufficiency
```
DataSufficiency: INSUFFICIENT | TENTATIVE | CONFIDENT | STRONG
```

#### ProfileDimension
```
ProfileDimension (extends PerformanceDimensionType):
  TECHNICAL_DEPTH         (existing)
  PROBLEM_SOLVING         (existing)
  COMMUNICATION           (existing)
  SYSTEM_DESIGN           (existing)
  ENGINEERING_JUDGMENT    (NEW — replaces TRADE_OFF_AWARENESS; see ADR-040)
```

#### ProfileSignal
```
ProfileSignal:
  CONFIDENCE
  CONSISTENCY
  EVIDENCE_QUALITY
  REASONING_DEPTH
```

#### EvidenceType
```
EvidenceType:
  # Positive
  REPEATED_STRENGTH
  RECOVERED_WEAKNESS
  DEMONSTRATED_DEPTH
  ENGINEERING_JUDGMENT_ARTICULATED

  # Negative
  REPEATED_WEAKNESS
  KNOWLEDGE_GAP
  COMMUNICATION_GAP
  REASONING_GAP
  CONFIDENCE_DROP
  MISSING_EVIDENCE
  SHALLOW_ANSWER
  CONTRADICTORY_ANSWER
```

#### EvidenceSource
```
EvidenceSource:
  EVALUATION       ← from EvaluationNode / WrittenEvaluationNode scores
  FEEDBACK         ← from FeedbackBundle dimension signals
  PATTERN_DETECTOR ← from PatternDetectionPipeline detectors
  DERIVED          ← reserved V1.2: cross-source combined signals
```

#### EvidenceSignal
```
EvidenceSignal (frozen, extra=forbid):
  id: str                         ← uuid4, assigned at creation
  question_index: int
  question_area: str
  dimension: ProfileDimension
  polarity: EvidencePolarity      ← POSITIVE | NEGATIVE
  signal_type: EvidenceType
  strength: float                 ← [0.0..1.0]
  source: EvidenceSource
  schema_version: str = "1.0"
  timestamp_question_index: int   ← redundant with question_index; retained for replay ordering
```

#### DimensionTrace
```
DimensionTrace (frozen, extra=forbid):
  average_score: float            ← rolling mean of all observed scores for this dimension
  last_score: float | None        ← score at most recent observation
  trend: Trend
  confidence: float               ← evidence_count / questions_answered (capped at 1.0)
  evidence_count: int             ← number of questions contributing evidence
  last_updated_question: int      ← question_index of most recent update
```
> NOTE: Historical raw scores are NOT stored here. They exist in `state.results_by_question[q_id].evaluation`. DimensionTrace stores only derived aggregates to avoid state duplication.

#### SignalObservation
```
SignalObservation (frozen, extra=forbid):
  question_index: int
  polarity: EvidencePolarity
  evidence: str                   ← Reasoner-generated label; NEVER interpolates candidate text
```

#### SignalTrace
```
SignalTrace (frozen, extra=forbid):
  observations: list[SignalObservation]   ← capped at 20
  trend: Trend
```

#### CandidateProfile
```
CandidateProfile (frozen, extra=forbid):
  dimension_scores: dict[ProfileDimension, DimensionTrace]
  signals: dict[ProfileSignal, SignalTrace]
  questions_answered: int
  areas_covered: list[str]
  last_updated_at_question_index: int
```

#### EvidenceStore
```
EvidenceStore (frozen, extra=forbid):
  signals: list[EvidenceSignal]   ← append-only; capped at 200 entries
  # Query helpers (computed properties, not stored):
  #   positive() → list[EvidenceSignal]
  #   negative() → list[EvidenceSignal]
  #   by_dimension(dim) → list[EvidenceSignal]
  #   by_type(type) → list[EvidenceSignal]
  #   strength_above(threshold) → list[EvidenceSignal]
```

#### CoverageState
```
CoverageState (frozen, extra=forbid):
  covered_areas: list[str]
  coverage_depth: dict[str, int]         ← area → question count
  follow_up_history: list[str]           ← question_ids that triggered follow-up
  repeated_topics: list[str]             ← topics appearing more than once
```

#### ReasoningEntry
```
ReasoningEntry (frozen, extra=forbid):
  question_index: int
  dominant_dimension: ProfileDimension | None
  detected_patterns: list[EvidenceType]
  follow_up_recommended: bool
  navigation_recommended: bool
  reasoning_confidence: float
  schema_version: str = "1.0"
```

#### ReasoningHistory
```
ReasoningHistory (frozen, extra=forbid):
  entries: list[ReasoningEntry]          ← capped at 20
```

#### SessionMetrics
```
SessionMetrics (frozen, extra=forbid):
  questions_answered: int
  follow_up_count: int
  total_evidence_signals: int
  positive_evidence_count: int
  negative_evidence_count: int
  last_reasoning_at_question_index: int | None
```

#### InterviewMemory
```
InterviewMemory (frozen, extra=forbid):
  candidate_profile: CandidateProfile
  evidence_store: EvidenceStore
  coverage_state: CoverageState
  reasoning_history: ReasoningHistory
  session_metrics: SessionMetrics
  schema_version: str = "1.0"
```

#### ReasoningConfidence
```
ReasoningConfidence (frozen, extra=forbid):
  reasoning_confidence: float          ← [0.0..1.0]; based on questions_answered
  evidence_strength: float             ← [0.0..1.0]; weighted mean of signal strengths
  data_sufficiency: DataSufficiency
```

#### ReasoningBasis
```
ReasoningBasis (frozen, extra=forbid):
  detected_patterns: list[EvidenceType]
  dominant_dimension: ProfileDimension | None
  session_quality_trend: Trend
  follow_up_triggers: list[EvidenceType]
  navigation_triggers: list[EvidenceType]
  reasoning_confidence: ReasoningConfidence
```

#### FollowUpRecommendation
```
FollowUpRecommendation (frozen, extra=forbid):
  recommended: bool
  target_dimension: ProfileDimension | None
  trigger_types: list[EvidenceType]
  priority: int                          ← 1 (high) to 3 (low)
```

#### NavigationRecommendation
```
NavigationRecommendation (frozen, extra=forbid):
  suggested_area: str | None
  deepen_current: bool
  skip_area: str | None
  trigger_types: list[EvidenceType]
```

#### ReasonerDecision
```
ReasonerDecision (frozen, extra=forbid):
  session_id: str
  question_index: int
  schema_version: str = "1.0"
  follow_up_recommendation: FollowUpRecommendation | None
  navigation_recommendation: NavigationRecommendation | None
  new_evidence: list[EvidenceSignal]
  candidate_profile_snapshot: CandidateProfile
  reasoning_basis: ReasoningBasis
  skip: bool = False
```

#### ReasonerInput
```
ReasonerInput (frozen, extra=forbid):
  # Session identity
  session_id: str
  question_index: int

  # Accumulated intelligence (read-only view)
  interview_memory: InterviewMemory

  # Current cycle inputs
  current_question_area: str | None
  current_question_type: str              ← QuestionType.value
  current_answer_content: str | None      ← sanitized; max 2000 chars
  current_evaluation: QuestionEvaluation | None
  current_feedback_quality: str | None    ← Quality.value
  current_dimension_signals: dict[str, float]

  # Full result history (read-only reference)
  results_by_question: dict[str, QuestionResult]

  # Settings snapshot (frozen at input construction time)
  max_follow_ups: int
  follow_up_count: int
  follow_up_eligible_indices: frozenset[int]
  questions_remaining: int

  # Interview metadata
  role: str
  seniority: str
  interview_type: str
```
> NOTE: `ReasonerInput` is built ONLY by `ReasoningContextBuilder`. No other component constructs it directly.

### 17.3 PatternDetector Registry Architecture

```
PatternDetectorRegistry
  registered_detectors: list[PatternDetector]    ← ordered; populated at service init
  active_flags: dict[str, bool]                  ← optional feature-flag gate per detector

PatternDetector (protocol):
  name: str
  def detect(context: ReasonerInput) -> list[EvidenceSignal]

Active detectors (V1.1 M2):
  ReasoningDepthDetector      → SHALLOW_ANSWER, REASONING_GAP
  KnowledgeConsistencyDetector → REPEATED_WEAKNESS, KNOWLEDGE_GAP, REPEATED_STRENGTH, RECOVERED_WEAKNESS
  ContradictionDetector        → CONTRADICTORY_ANSWER
  EvidenceQualityDetector      → DEMONSTRATED_DEPTH, MISSING_EVIDENCE
  TradeOffDetector             → ENGINEERING_JUDGMENT_ARTICULATED, REASONING_GAP

Reserved (V1.2):
  ConfidenceTrendDetector      → CONFIDENCE_DROP (uses DERIVED source)
  BehavioralPatternDetector    → future HR/behavioral interviews
```

Lifecycle:
1. `InterviewReasoner.__init__()` constructs `PatternDetectorRegistry` with all active detectors.
2. `PatternDetectionPipeline.run(context)` queries registry for active detectors.
3. Pipeline calls `detect()` on each; merges `list[EvidenceSignal]` outputs.
4. New detectors are added to registry only — pipeline code is never modified (OCP).
5. Feature flags in registry allow disabling individual detectors without code change.

### 17.4 Graph Position and State Changes

**New graph edge:** `feedback → reasoner → decision`

**New InterviewState fields:**
```
interview_memory: InterviewMemory = Field(default_factory=InterviewMemory)
current_reasoning_decision: ReasonerDecision | None = None
```

**Deprecated InterviewState field (M2 — removal in M3):**
```
interview_memory_context: InterviewMemoryContext    ← deprecated; still populated by AdaptiveInterviewMemoryBridge for M2 backward compat
```

### 17.5 Downstream Consumption Map

```
interview_memory.evidence_store.signals
  ├── KnowledgeGapEngine.detect()            ← EPIC-05; filters polarity=NEGATIVE
  ├── ReportNarrativeAssembler               ← EPIC-07; all evidence
  ├── CoachingRoadmapBuilder                 ← V1.2; negative evidence ordered by strength
  └── ExecutiveSummaryGenerator              ← EPIC-08; structured input

interview_memory.candidate_profile
  ├── AdaptiveNavigationNode                 ← soft area hint
  ├── NarrativeService (structured input)    ← EPIC-07
  └── ContradictionDetector (reads history)  ← internal Reasoner

current_reasoning_decision.follow_up_recommendation
  └── question_node._is_follow_up_eligible   ← M2 runtime score gate (ADR-024)

current_reasoning_decision.navigation_recommendation
  └── AdaptiveNavigationNode                 ← soft hint
```

---

### ADR-028: Interview Reasoner Is a Deterministic Service (No LLM)

**Status: Accepted — V1.1 M2**

**Decision:** `InterviewReasoner` contains zero LLM calls. All pattern detection is rule-based, deterministic. No LLM may be called from within `services/interview_reasoner/` or any of its sub-components in V1.1 M2.

**Rationale:** 20 questions × LLM call = 20–100s added session latency. Rule-based detection is <5ms, testable, reproducible.

**Consequences:** Reasoning quality is bounded by rule expressiveness. Semantic contradiction detection deferred to M3+ as async/background LLM step.

---

### ADR-029: Reasoner Node Position — After Feedback, Before Decision

**Status: Accepted — V1.1 M2**

**Decision:** `reasoner_node` is inserted between `feedback_node` and `decision_node` in the interview graph.

**Rationale:** Only at this point are evaluation result, feedback bundle, and dimension signals all available. Decision has not yet been committed.

**Consequences:** `reasoner_node` must handle `last_feedback_bundle=None` gracefully: return `ReasonerDecision(skip=True)`.

---

### ADR-030: Reasoner Outputs Are Advisory Only

**Status: Accepted — V1.1 M2**

**Decision:** No node is required to follow Reasoner recommendations. `question_node` and `AdaptiveNavigationNode` read `current_reasoning_decision` as optional hints and retain full authority.

**Rationale:** A Reasoner bug cannot break interview flow; degrades gracefully to M1 baseline.

---

### ADR-031: ReasonerDecision Is Stored Transiently; ReasoningHistory Is Persistent

**Status: Accepted — V1.1 M2**

**Decision:** `current_reasoning_decision` holds only the last cycle's decision. `InterviewMemory.reasoning_history` is capped at 20 entries and contains `ReasoningEntry` (compact summary only).

---

### ADR-032: InterviewMemory as Session-Scoped Accumulated Intelligence

**Status: Accepted — V1.1 M2**

**Decision:** `InterviewMemory` is introduced as the canonical accumulation contract on `InterviewState`. Single-writer: only `InterviewReasoner` writes to it. All downstream consumers read it. Supersedes `InterviewMemoryContext`.

**Consequences:** `InterviewMemoryContext` deprecated in M2; removed in M3.

---

### ADR-033: EvidenceSignal as Universal Signal Abstraction

**Status: Accepted — V1.1 M2**

**Decision:** `EvidenceSignal` replaces the originally proposed `GapSignal`. Captures both positive and negative evidence with polarity, type, strength, source, dimension, id, and schema_version.

**Rationale:** Coaching-first platform requires positive evidence for "went well" coaching. Gap-only abstraction structurally biases output toward deficit reporting.

---

### ADR-034: PatternDetector Decomposed into Registry-Backed Pipeline

**Status: Accepted — V1.1 M2**

**Decision:** `PatternDetector` (single component) is replaced by `PatternDetectorRegistry` + `PatternDetectionPipeline` with five independent stateless detectors in V1.1 M2.

**Rationale:** OCP compliance; new detectors plug in via registry without pipeline modification.

---

### ADR-035: ReasonerDecision Is Fully Structured — No Free Text

**Status: Accepted — V1.1 M2**

**Decision:** `ReasonerDecision` contains no free-text fields. All output is structured data. `NarrativeGenerator` is solely responsible for natural language.

**Rationale:** Free text in `ReasonerDecision` creates prompt injection surface and violates SRP.

---

### ADR-036: Two-Tier Confidence Model (ReasoningConfidence)

**Status: Accepted — V1.1 M2**

**Decision:** Flat `confidence: float` replaced by `ReasoningConfidence { reasoning_confidence, evidence_strength, data_sufficiency }`.

**Rationale:** Two independent dimensions: how many questions has Reasoner seen (reasoning_confidence) vs. how strong are the signals this cycle (evidence_strength).

---

### ADR-037: CandidateProfile as Evolving Derived Structure Inside InterviewMemory

**Status: Accepted — V1.1 M2**

**Decision:** `CandidateProfile` lives inside `InterviewMemory`. Single-writer: `InterviewReasoner`. Historical raw scores are NOT stored in `DimensionTrace` (they exist in `results_by_question`).

---

### ADR-038: InterviewMemory Internal Composition

**Status: Accepted — V1.1 M2**

**Context:** A monolithic `InterviewMemory` DTO would create coupling between unrelated concerns (profile, evidence, coverage, history, metrics) and make future independent evolution difficult.

**Decision:** `InterviewMemory` is composed of five independent immutable substructures:

| Substructure | Responsibility |
|---|---|
| `CandidateProfile` | Current profile state: dimension traces, signal traces, areas covered |
| `EvidenceStore` | Canonical append-only list of `EvidenceSignal`; capped at 200; exposes query helpers |
| `CoverageState` | Interview area coverage: depth per area, follow-up history, repeated topics |
| `ReasoningHistory` | Compact per-cycle `ReasoningEntry` log; capped at 20; supports debugging and replay |
| `SessionMetrics` | Aggregate counters: questions answered, follow-up count, evidence statistics |

Each substructure is independently frozen (immutable). `InterviewReasoner` creates a new `InterviewMemory` each cycle by replacing only the substructures that changed.

**Rationale:**
- Each substructure has a single clear responsibility (SRP).
- Future EPIC-05, EPIC-07, V1.2 consumers import only the substructure they need.
- Independent evolution: `EvidenceStore` capacity rules can change without touching `CandidateProfile`.
- Testability: each substructure can be unit-tested independently.

**Consequences:**
- `InterviewMemory` has no direct fields; all data is accessed through named substructures.
- `ReasonerContextBuilder` must provide each substructure to the Reasoner input (`ReasonerInput.interview_memory` carries the full `InterviewMemory`).

---

### ADR-039: Evidence Freshness — Architectural Reservation

**Status: Accepted (Deferred to V1.2)**

**Context:** A candidate who struggles early but recovers mid-session should not be penalized equally to one who consistently struggles. Flat evidence accumulation treats all signals equally regardless of when they occurred.

**Decision:** The architecture reserves the `DERIVED` `EvidenceSource` value and the `ReasoningHistory` structure for a future evidence freshness weighting mechanism. In V1.1 M2, all evidence is weighted equally.

**V1.2 Implementation Requirement (not designed here):**
- A weighting strategy will be defined and implemented in V1.2.
- The strategy must use only `EvidenceSignal.question_index` and `SessionMetrics.questions_answered` to compute recency weight.
- The weighting algorithm is explicitly out of scope for V1.1 M2.
- No formula, no implementation, no alpha parameter is defined here.

**Rationale:** Recovery from early mistakes is realistic interview behaviour. Flat weighting penalises early errors that the candidate has demonstrably overcome. Deferring ensures V1.1 M2 is not blocked on an algorithm design decision.

**Consequences:**
- `EvidenceSource.DERIVED` is defined but never emitted in V1.1 M2.
- Any component that filters by `EvidenceSource` must not assume `DERIVED` is absent.
- V1.2 may introduce a `FreshnessWeightedEvidenceStore` wrapper without changing `EvidenceStore` schema.

---

### ADR-040: ProfileDimension Naming — ENGINEERING_JUDGMENT

**Status: Accepted — V1.1 M2**

**Context:** Two candidate names were evaluated: `TRADE_OFF_AWARENESS` vs `ENGINEERING_JUDGMENT`.

**Evaluation:**

| Criterion | TRADE_OFF_AWARENESS | ENGINEERING_JUDGMENT |
|---|---|---|
| Clarity | Narrow: implies only trade-off analysis | Broad: covers trade-offs, prioritization, failure mode reasoning, operational decisions |
| Future extensibility | Locked to "trade-off" framing | Extensible to any engineering decision context |
| Behavioral interview alignment | Weak | Strong: engineering judgment maps to standard SWE interview rubrics |
| Seniority signal | Partial | Strong: senior engineers are assessed on judgment, not just awareness |
| Coaching language | "You lacked trade-off awareness" | "Your engineering judgment showed..." |

**Decision:** `ENGINEERING_JUDGMENT` is adopted as the fifth `ProfileDimension`.

**All references to `TRADE_OFF_AWARENESS` in this TDS and all architecture documents are superseded by `ENGINEERING_JUDGMENT`.**

**Corresponding EvidenceType:** `ENGINEERING_JUDGMENT_ARTICULATED` (positive) replaces `TRADE_OFF_ARTICULATED`.

**Corresponding Detector:** `TradeOffDetector` is renamed `EngineeringJudgmentDetector` at implementation time.

---


### ADR-041: Reasoner Explainability — Internal Audit Trail

**Status: Accepted — Architecture only; implementation deferred to V1.1 M2 final**

**Context:** The Reasoner is fully deterministic and has no LLM calls. However, as pattern detection rules grow in number and complexity, tracing *why* a particular `ReasonerDecision` was produced becomes difficult without structured internal metadata.

**Decision:** A lightweight `ReasoningTrace` contract is introduced as an internal audit trail. It captures per-step metadata for each component involved in producing a `ReasonerDecision`.

**Scope — INTERNAL ONLY:**
- Never exposed to candidates.
- Never rendered in UI or coaching reports.
- Never sent to `NarrativeGenerator` or any LLM prompt.
- Never persisted outside `InterviewMemory.reasoning_history`.
- Contains only Reasoner-generated metadata — never candidate text, answers, or prompts.

**Schema:**
```
ReasoningTrace (frozen, extra=forbid):
  steps: list[ReasoningTraceStep]

ReasoningTraceStep (frozen, extra=forbid):
  step_id: str
  component: str          ← e.g. "ReasoningDepthDetector", "KnowledgeConsistencyDetector"
  rule_name: str          ← e.g. "shallow_answer_check", "dimension_consistency"
  confidence_delta: float ← how much this step shifted reasoning_confidence
  execution_time_ms: float
  summary: str            ← Reasoner-generated label; NEVER interpolates candidate text
```

**Use cases:**
- Unit testing: verify specific rules fired for a given input
- Architecture audits: trace decision provenance
- Future replay: reconstruct session decision logic from stored trace
- Debugging production issues without exposing candidate data

**Consequences:**
- `ReasoningTrace` is passed through `ReasonerDecision` but stored compactly (only last N=5 traces in `ReasoningHistory`).
- `ReasoningTraceStep.summary` must be a Reasoner-generated string — never an interpolation of candidate-supplied text (security constraint, consistent with ADR-035).

---


---

### ADR-042: CandidateProfile Internal Composition (Future-Proofing)

**Status: Accepted — Architecture direction; implementation reserved for V1.2+**

**Context:** `CandidateProfile` currently holds a flat `dict[ProfileDimension, DimensionTrace]` and `dict[ProfileSignal, SignalTrace]`. As the Reasoner evolves across V1.2 and beyond, different consumers will need different slices (e.g., Knowledge Gap Engine needs knowledge signals; NarrativeGenerator needs communication signals). A flat profile will become a God Object.

**Decision:** `CandidateProfile` is designated as the **Aggregate Root** of candidate assessment. In a future iteration it may be internally composed of independent sub-profiles:

| Sub-profile | Responsibility |
|---|---|
| `DimensionProfile` | Aggregated dimension traces and trends |
| `KnowledgeProfile` | Knowledge-specific dimension signals (TECHNICAL_DEPTH, ENGINEERING_JUDGMENT) |
| `BehaviourProfile` | Consistency and confidence signal traces |
| `CommunicationProfile` | COMMUNICATION dimension traces and EVIDENCE_QUALITY signals |
| `EngineeringProfile` | SYSTEM_DESIGN, ENGINEERING_JUDGMENT, REASONING_DEPTH traces |
| `OverallProfile` | Cross-dimension aggregates, session-level quality trend |

Each sub-profile is independently frozen and independently queryable. `CandidateProfile` exposes all sub-profiles as named attributes.

**Constraints:**
- The current `CandidateProfile` contract (M2-1 frozen) is NOT changed.
- Sub-profile decomposition is deferred to V1.2.
- External consumers always access profile data through `CandidateProfile` — never by constructing sub-profiles directly.
- `CandidateProfile` remains the single-writer boundary for `InterviewReasoner`.

**Rationale:** Decomposing now prevents the flat dict from accumulating mixed concerns. Designating `CandidateProfile` as Aggregate Root ensures the boundary is clear before V1.2 adds more signals.

---

### ADR-043: ReasonerDecision Composition (Future-Proofing)

**Status: Accepted — Architecture direction; implementation reserved for V1.2+**

**Context:** `ReasonerDecision` currently contains `follow_up_recommendation`, `navigation_recommendation`, `new_evidence`, `candidate_profile_snapshot`, and `reasoning_basis`. As V1.2 adds coaching, coverage analysis, and confidence assessment, these will grow to ~10 fields if not structured.

**Decision:** `ReasonerDecision` is designated a **Composed Decision** rather than a monolithic DTO. In a future iteration it may be composed of independent decisions:

| Decision | Responsibility |
|---|---|
| `FollowUpDecision` | Should a follow-up be attempted? Which dimension? Why? |
| `NavigationDecision` | Should next area change? Deepen or skip? |
| `CoachingDecision` | What coaching signal should the session emit at this point? |
| `CoverageDecision` | Is area coverage balanced? Any area at risk of over/under-representation? |
| `ConfidenceAssessment` | What is the Reasoner's confidence in its own outputs this cycle? |

**Constraints:**
- The current `ReasonerDecision` contract (M2-1 frozen) is NOT changed.
- The composed-decision model is deferred to V1.2.
- `ReasonerDecision` continues to hold `skip: bool` as the top-level guard regardless of future composition.

**Rationale:** Prevents `ReasonerDecision` from accumulating fields from unrelated concerns. Each composed decision can be independently consumed (e.g., `AdaptiveNavigationNode` reads only `NavigationDecision`).

---

### ADR-044: Recommendation Hierarchy (Future-Proofing)

**Status: Accepted — Architecture direction; implementation reserved for V1.2+**

**Context:** V1.1 M2 has two recommendation types: `FollowUpRecommendation` and `NavigationRecommendation`. V1.2 plans add coaching, study, and practice recommendations. Without a common base type, consuming code must handle each independently.

**Decision:** A future `Recommendation` base protocol/contract is reserved. All recommendation types must be derivable from it:

```
Recommendation (base — future)
  recommended: bool
  trigger_types: list[EvidenceType]
  priority: int  ← 1 (high) to 3 (low)
  confidence: float

Derived:
  FollowUpRecommendation     ← current M2-1 contract; will gain base fields in V1.2
  NavigationRecommendation   ← current M2-1 contract; will gain base fields in V1.2
  KnowledgeRecommendation    ← V1.2: recommend specific knowledge area study
  StudyRecommendation        ← V1.2: concrete study material recommendation (feeds Coaching Roadmap)
  PracticeRecommendation     ← V1.2: recommend targeted practice question type
```

**Constraints:**
- `FollowUpRecommendation` and `NavigationRecommendation` contracts (M2-1) are NOT changed.
- The `Recommendation` base is NOT introduced as a Python type in M2.
- When V1.2 introduces `KnowledgeRecommendation`, it must share the same field names for `recommended`, `trigger_types`, and `priority` to allow unified consumption.

**Rationale:** Establishes a stable recommendation vocabulary before proliferation makes unification expensive.

---

### ADR-045: PatternDetector Metadata Model (Future-Proofing)

**Status: Accepted — Architecture direction; implementation reserved for M2-2**

**Context:** `PatternDetectorRegistry` is planned as the single registry of active detectors (ADR-034). Without a structured metadata model, the registry devolves into a list of callables with no introspection capability.

**Decision:** Each `PatternDetector` registered in `PatternDetectorRegistry` must expose a **metadata descriptor**:

```
DetectorMetadata (frozen):
  name: str          ← unique identifier; used in ReasoningTraceStep.component
  version: str       ← semver string (e.g. "1.0.0")
  priority: int      ← execution order within pipeline (lower = earlier)
  enabled: bool      ← registry checks this before calling detect()
  dependencies: list[str]  ← names of detectors that must run before this one
```

`PatternDetectionPipeline` uses `DetectorMetadata.enabled` and `DetectorMetadata.dependencies` instead of any hardcoded if/else logic. Registry ordering is derived from `priority` + topological sort of `dependencies`.

**Constraints:**
- `DetectorMetadata` contract is NOT implemented in M2-1.
- All five M2 detectors must be retrofittable to expose `DetectorMetadata` without changing their `detect()` signature.
- Feature flags map to `DetectorMetadata.enabled`; no `if feature_flag_X` in pipeline code.

**Rationale:** Metadata-driven registry satisfies OCP: adding a detector is a registry registration, not a code change. Dependency declaration prevents ordering bugs silently.

---

### ADR-046: EvidenceStore Responsibilities

**Status: Accepted — Architecture direction; partially implemented in M2-1**

**Context:** `EvidenceStore` in M2-1 is a Pydantic frozen model with a `signals: list[EvidenceSignal]` field and helper methods on the model. As usage grows, query patterns will diversify and the model will accumulate query methods.

**Decision:** `EvidenceStore` is designated the **single point of access** for all `EvidenceSignal` queries in the session. Its responsibility contract is frozen:

| Method | Behaviour |
|---|---|
| `append(signal)` | Returns new `EvidenceStore` with signal appended (immutable; factory method) |
| `by_dimension(dim)` | Filter by `ProfileDimension` |
| `by_question(index)` | Filter by `question_index` |
| `positive()` | Filter by `EvidencePolarity.POSITIVE` |
| `negative()` | Filter by `EvidencePolarity.NEGATIVE` |
| `recent(n)` | Last N signals by `timestamp_question_index` |
| `statistics()` | Returns `EvidenceStoreStatistics` DTO (counts, mean strength per dimension, polarity ratio) |

**Current state:** `by_dimension`, `positive`, `negative`, `by_type`, `by_source`, `strength_above` are implemented as model methods in M2-1. `append`, `by_question`, `recent`, `statistics` are deferred to M2-2.

**Constraints:**
- M2-1 `EvidenceStore` contract is NOT changed.
- `append()` must be implemented as a factory method returning a new `EvidenceStore` (preserves immutability).
- `EvidenceStoreStatistics` DTO is deferred to M2-2.
- No code outside `EvidenceStore` iterates `signals` directly — all access goes through the above methods.

**Rationale:** Centralising queries prevents scattered list comprehensions across the codebase. The `append` factory method preserves the frozen/immutable contract.

---

### ADR-047: ReasoningTrace Audit Metadata Extension (Future-Proofing)

**Status: Accepted — Architecture direction; implementation reserved for V1.2**

**Context:** `ReasoningTraceStep` in M2-1 captures `step_id`, `component`, `rule_name`, `confidence_delta`, `execution_time_ms`, and `summary`. For future replay and audit scenarios, it is necessary to verify that a trace step's inputs and outputs match without storing the full input/output (which could contain sensitive or large data).

**Decision:** Future versions of `ReasoningTraceStep` may include:

```
input_hash: str | None   ← SHA-256 of the serialized detector input for this step
output_hash: str | None  ← SHA-256 of the serialized EvidenceSignal list produced
```

**Constraints:**
- `input_hash` and `output_hash` are hashes only — never the full input or output.
- Full input (candidate answer, evaluation scores) is NEVER stored in `ReasoningTrace` (ADR-041 security constraint).
- The hash is deterministic: same input → same hash → same output verifiable without re-running.
- `input_hash` / `output_hash` fields are NOT added in M2-1 or M2-2.
- When added in V1.2, they must be optional (`None` for historical entries) to preserve backward compatibility.

**Rationale:** Hash-based audit trail enables verifying deterministic replay without storing sensitive data. Optional fields ensure zero migration cost for existing entries.

---

## §18 — Advanced Detector Architecture (M2-7A Freeze)

> **Status: Frozen 2026-07-01 | Milestone: M2-7A**
> This section is the authoritative contract for all detectors implemented from M2-7B onward.
> Zero production code is modified by this section — it is documentation only.

---

### §18.1 — ProfileFeature Abstraction (V1.2 Reserved)

#### Motivation

The current `CandidateProfile` contains `dimension_scores: dict[ProfileDimension, DimensionTrace]`.  
This model captures *what* a candidate knows but not *how* they demonstrate it (reasoning quality, communication style, leadership signals, etc.).

A `ProfileFeature` is a named, versioned, computed characteristic that extends the profile beyond raw dimension scores — without requiring any change to the `CandidateProfile` schema.

#### Definition

```
ProfileFeature
├── name: str                       # stable identifier, e.g. "reasoning_depth"
├── version: str                    # semver, for future migration
├── value: float | None             # normalized [0.0, 1.0] or None (insufficient data)
├── confidence: float               # [0.0, 1.0], grows with evidence
├── evidence_count: int             # how many signals contributed
├── last_updated_question_index: int
└── metadata: dict                  # free-form, extensible tags
```

#### Lifecycle

```
PatternDetector (M2-7+)
       ↓ produces EvidenceSignal + PatternMatch
CandidateProfileEngine (M2-6C)
       ↓ calls ProfileFeatureUpdater (V1.2)
ProfileFeature stored in CandidateProfile.features
       ↓ read by
NarrativeGenerator (M2-8) + ReportBuilder (M2-9)
```

#### Ownership

Single-writer: `CandidateProfileEngine`.  
No detector, graph node, or external component writes directly to `ProfileFeature`.

#### Update Strategy

Incremental, O(new_signals). Never recomputes from full EvidenceStore.

#### M2 Current State

The M2-6C `CandidateProfileEngine` updates `DimensionTrace` only.  
`ProfileFeatures` are **not yet present** in `CandidateProfile`.  
They will be added in V1.2 as an optional `features: dict[str, ProfileFeature]` field with `default_factory=dict`.

#### Migration Path

```
V1.1  CandidateProfile.dimension_scores only
V1.2  CandidateProfile.features added (optional, backward-compatible)
V1.3+ ProfileFeatures become primary profile signal for Narrative and Report
```

See **ADR-048** for the full decision record.

---

### §18.2 — Advanced Detector Catalog

All detectors below comply with the `PatternDetector` contract (§17.3).  
Execution order is defined by the `priority` field in `DetectorMetadata`.

---

#### DET-01: EvaluationSignalDetector (Successor of EvaluationBridgeDetector)

| Field | Value |
|---|---|
| **Priority** | 5 |
| **Status** | Active — replaces `EvaluationBridgeDetector` in M2-7B |
| **Dependencies** | None |
| **Complexity** | O(n) in EvidenceStore signals |

**Purpose:** Bridge evaluation-origin signals into the PatternDetection pipeline. Succeeds `EvaluationBridgeDetector` with a richer output model including signal freshness weighting.

**Input:** `ReasonerInput.interview_memory.evidence_store` (read-only)

**Produced PatternMatch types:**
- `KNOWLEDGE_GAP` — one match per dimension with fresh knowledge gap signals
- `SHALLOW_ANSWER` — one match per dimension with fresh shallow answer signals
- `REASONING_GAP` — one match per dimension with fresh reasoning gap signals

**Produced EvidenceSignal types:** One derived `PATTERN_DETECTOR`-source signal per (type, dimension) — subject to idempotency guard.

**Future ProfileFeatures affected:** `ReasoningDepthFeature`, `KnowledgeDensityFeature`

**Acceptance Criteria:**
- Bridges only signals from the current or previous `N` questions (configurable sliding window, default 3)
- Does not re-bridge signals older than the window
- Idempotency guard prevents duplicate derived signals
- Deterministic; no LLM

---

#### DET-02: CoverageDetector (Existing)

| Field | Value |
|---|---|
| **Priority** | 10 |
| **Status** | Active — M2-3, updated M2-6A |
| **Dependencies** | None |
| **Complexity** | O(d) where d = len(ProfileDimension) |

**Purpose:** Detect uncovered or under-covered profile dimensions.

**Produced PatternMatch types:** `MISSING_EVIDENCE`, `REPEATED_WEAKNESS`

**Produced EvidenceSignal types:** `MISSING_EVIDENCE`, `REPEATED_WEAKNESS`

**Future ProfileFeatures affected:** `CoverageFeature`

---

#### DET-03: ConsistencyDetector (Existing)

| Field | Value |
|---|---|
| **Priority** | 20 |
| **Status** | Active — M2-3, updated M2-6A |
| **Dependencies** | `CoverageDetector` |
| **Complexity** | O(n) |

**Purpose:** Detect duplicate signals, contradictions, confidence drops.

**Produced PatternMatch types:** `REPEATED_WEAKNESS`, `CONTRADICTORY_ANSWER`, `CONFIDENCE_DROP`

**Future ProfileFeatures affected:** `ConsistencyFeature`

---

#### DET-04: TrendDetector (Existing)

| Field | Value |
|---|---|
| **Priority** | 30 |
| **Status** | Active — M2-3, updated M2-6A |
| **Dependencies** | `ConsistencyDetector` |
| **Complexity** | O(d × h) where h = reasoning history length |

**Purpose:** Detect score and confidence trends per dimension.

**Produced PatternMatch types:** `IMPROVING`, `STABLE`, `DECLINING` (via polarity)

**Future ProfileFeatures affected:** `TrendFeature`

---

#### DET-05: ReasoningDepthDetector

| Field | Value |
|---|---|
| **Priority** | 40 |
| **Milestone** | M2-7B |
| **Dependencies** | `TrendDetector` |
| **Complexity** | O(n) |

**Purpose:** Assess the depth of reasoning demonstrated by the candidate by analysing the distribution and density of `REASONING_GAP` vs. `DEMONSTRATED_DEPTH` signals per dimension. Distinguishes surface-level correct answers from deep principled reasoning.

**Input:**
- `ReasonerInput.interview_memory.evidence_store` — signals with `signal_type ∈ {REASONING_GAP, DEMONSTRATED_DEPTH, SHALLOW_ANSWER}`
- `ReasonerInput.interview_memory.candidate_profile.dimension_scores`

**Produced PatternMatch types:**
- `REASONING_GAP` — when reasoning signals show low depth ratio
- `DEMONSTRATED_DEPTH` — when depth ratio is high across multiple dimensions

**Produced EvidenceSignal types:**
- `REASONING_GAP` (strength weighted by breadth of shallow answers)
- `DEMONSTRATED_DEPTH` (strength weighted by depth ratio)

**Acceptance Criteria:**
- Depth ratio computed as `demonstrated_depth_count / (demonstrated_depth_count + reasoning_gap_count)`
- Emits `DEMONSTRATED_DEPTH` only when ratio ≥ 0.6 and evidence_count ≥ 3
- Emits `REASONING_GAP` only when ratio ≤ 0.3 and evidence_count ≥ 2
- Silent otherwise

**Future ProfileFeatures affected:** `ReasoningDepthFeature`

---

#### DET-06: EngineeringJudgmentDetector

| Field | Value |
|---|---|
| **Priority** | 50 |
| **Milestone** | M2-7C |
| **Dependencies** | `ReasoningDepthDetector` |
| **Complexity** | O(n) |

**Purpose:** Detect whether the candidate demonstrates trade-off awareness, prioritisation skill, and operational reasoning — the `ENGINEERING_JUDGMENT` dimension. Uses `ENGINEERING_JUDGMENT_ARTICULATED` signals as positive evidence.

**Input:**
- Signals with `dimension = ENGINEERING_JUDGMENT` or `signal_type = ENGINEERING_JUDGMENT_ARTICULATED`
- `DimensionTrace` for `ENGINEERING_JUDGMENT`

**Produced PatternMatch types:**
- `ENGINEERING_JUDGMENT_ARTICULATED` — positive match on trade-off/priority articulation
- `SHALLOW_ANSWER` — when judgment questions yield shallow responses
- `KNOWLEDGE_GAP` — when judgment dimension has zero evidence after threshold

**Produced EvidenceSignal types:**
- `ENGINEERING_JUDGMENT_ARTICULATED` (positive)
- `KNOWLEDGE_GAP` (negative, when dimension absent)

**Acceptance Criteria:**
- Only fires after `reasoner_coverage_min_questions` threshold
- Does not create phantom signals for unaddressed judgment questions
- `ENGINEERING_JUDGMENT` dimension must have at least 1 evaluation-origin signal before firing

**Future ProfileFeatures affected:** `EngineeringJudgmentFeature`

---

#### DET-07: CommunicationDetector

| Field | Value |
|---|---|
| **Priority** | 60 |
| **Milestone** | M2-7D |
| **Dependencies** | `ConsistencyDetector` |
| **Complexity** | O(n) |

**Purpose:** Specifically assess the `COMMUNICATION` dimension by analysing signal ratios, pattern regularity, and consistency of communication evidence across the session. Separates technical communication gaps from content gaps.

**Input:**
- Signals with `dimension = COMMUNICATION`
- `DimensionTrace` for `COMMUNICATION`

**Produced PatternMatch types:**
- `COMMUNICATION_GAP` — persistent communication weakness
- `REPEATED_STRENGTH` (positive) — consistent communication quality
- `CONTRADICTORY_ANSWER` — inconsistent communication signals

**Produced EvidenceSignal types:**
- `COMMUNICATION_GAP` (negative, on sustained weakness)
- `REPEATED_STRENGTH` (positive, on sustained strength)

**Acceptance Criteria:**
- Fires only when `COMMUNICATION` dimension has ≥ 2 evidence signals
- Does not confuse content gaps with communication gaps (uses source + polarity)
- Silent if communication dimension has no evidence

**Future ProfileFeatures affected:** `CommunicationFeature`

---

#### DET-08: BehavioralPatternDetector

| Field | Value |
|---|---|
| **Priority** | 70 |
| **Milestone** | M2-7E |
| **Dependencies** | `TrendDetector` |
| **Complexity** | O(n × d) |

**Purpose:** Detect session-level behavioral patterns that span multiple dimensions: hesitation sequences (sustained SHALLOW_ANSWER across dims), rebound patterns (DECLINING followed by IMPROVING), and plateau patterns (STABLE across all dims for ≥ 3 consecutive questions).

**Input:**
- Full `ReasoningHistory` entries
- Cross-dimension DimensionTrace map

**Produced PatternMatch types:**
- Custom `BEHAVIORAL_PATTERN` labels: `HESITATION_SEQUENCE`, `REBOUND_PATTERN`, `PLATEAU_PATTERN`
- (uses `EvidenceType.REPEATED_WEAKNESS` with extended label field)

**Produced EvidenceSignal types:**
- None — produces PatternMatch only (no new EvidenceSignals to avoid inflation)

**Acceptance Criteria:**
- Requires ≥ 4 reasoning history entries before firing
- Produces at most one PatternMatch per behavioral type per cycle
- Each match carries a `confidence` derived from the number of confirming history entries
- Deterministic

**Future ProfileFeatures affected:** `BehavioralPatternFeature` (V1.2)

---

#### DET-09: ConsistencyAcrossInterviewDetector

| Field | Value |
|---|---|
| **Priority** | 80 |
| **Milestone** | M2-7F |
| **Dependencies** | `ConsistencyDetector`, `TrendDetector` |
| **Complexity** | O(n²) worst case; expected O(n log n) with dimension grouping |

**Purpose:** Cross-interview consistency analysis — detects when the candidate's answers to semantically related question areas show contradictory trends. Example: strong in "concurrency" but weak in "distributed locking" (sub-areas of TECHNICAL_DEPTH).

**Input:**
- `EvidenceStore` signals grouped by `question_area`
- `DimensionTrace` map

**Produced PatternMatch types:**
- `CONTRADICTORY_ANSWER` with cross-area label
- `REPEATED_STRENGTH` for consistent cross-area performance

**Produced EvidenceSignal types:**
- `CONTRADICTORY_ANSWER` (when cross-area contradiction exceeds threshold)

**Performance constraint:** Must complete in < 5ms for sessions up to 10 questions. If projected to exceed budget, return empty result with warning.

**Acceptance Criteria:**
- Only fires when ≥ 2 distinct question areas exist for the same dimension
- Contradiction threshold: opposite polarity ratio ≥ 0.4
- Deterministic

**Future ProfileFeatures affected:** `CrossDomainConsistencyFeature` (V1.2)

---

#### DET-10: ConfidenceCalibrationDetector

| Field | Value |
|---|---|
| **Priority** | 90 |
| **Milestone** | M2-7G |
| **Dependencies** | `ConsistencyAcrossInterviewDetector` |
| **Complexity** | O(h) where h = reasoning history length |

**Purpose:** Detect whether the candidate's self-assessment (confidence signals in `SignalTrace`) calibrates with actual performance (DimensionTrace scores). Identifies overconfidence (high claimed confidence, low score) and underconfidence (low claimed confidence, high score).

**Input:**
- `CandidateProfile.signals` (CONFIDENCE ProfileSignal observations)
- `CandidateProfile.dimension_scores`

**Produced PatternMatch types:**
- `CONFIDENCE_DROP` — overconfidence detected (confidence claims > actual score by threshold)
- Custom: `UNDERCONFIDENCE_PATTERN` (expressed as `REPEATED_WEAKNESS` with label)

**Produced EvidenceSignal types:**
- `CONFIDENCE_DROP` (on overconfidence)

**Acceptance Criteria:**
- Requires ≥ 3 confidence signal observations
- Overconfidence threshold: confidence_claim > actual_score + 20 points
- Underconfidence threshold: confidence_claim < actual_score - 20 points
- Silent when insufficient SignalTrace data

**Future ProfileFeatures affected:** `ConfidenceCalibrationFeature` (V1.2)

---

#### DET-11: LeadershipDetector (Reserved)

| Field | Value |
|---|---|
| **Priority** | 100 |
| **Milestone** | V1.2 |
| **Dependencies** | `BehavioralPatternDetector` |
| **Status** | Reserved — not implemented in V1.1 |

**Purpose:** Detect leadership signals from behavioral questions: decision ownership, team facilitation references, escalation patterns. Requires behavioral interview type.

**Gate:** Only enabled when `interview_type = "behavioral"` or `"leadership"`.

**Future ProfileFeatures affected:** `LeadershipFeature` (V1.2)

---

#### DET-12: CollaborationDetector (Reserved)

| Field | Value |
|---|---|
| **Priority** | 110 |
| **Milestone** | V1.2 |
| **Dependencies** | `LeadershipDetector` |
| **Status** | Reserved — not implemented in V1.1 |

**Purpose:** Detect collaboration and cross-functional signals: references to working with PMs, designers, other engineers. Requires behavioral interview data.

**Future ProfileFeatures affected:** `CollaborationFeature` (V1.2)

---

#### DET-13: AdaptabilityDetector (Reserved)

| Field | Value |
|---|---|
| **Priority** | 120 |
| **Milestone** | V1.2 |
| **Dependencies** | `BehavioralPatternDetector` |
| **Status** | Reserved — not implemented in V1.1 |

**Purpose:** Detect adaptability signals: response to novel/ambiguous problem framing, willingness to revise initial answers, recovery from incorrect paths.

**Future ProfileFeatures affected:** `AdaptabilityFeature` (V1.2)

---

### §18.3 — Detector Pipeline (Frozen Execution Order)

```
Evaluation Pipeline (upstream)
        ↓ writes EvidenceSignals to EvidenceStore
─────────────────────────────────────────────────────
 Priority │ Detector                       │ Milestone
──────────┼────────────────────────────────┼──────────
    5     │ EvaluationSignalDetector       │ M2-7B (replaces EvaluationBridgeDetector)
   10     │ CoverageDetector               │ Active (M2-3)
   20     │ ConsistencyDetector            │ Active (M2-3)
   30     │ TrendDetector                  │ Active (M2-3)
   40     │ ReasoningDepthDetector         │ M2-7B
   50     │ EngineeringJudgmentDetector    │ M2-7C
   60     │ CommunicationDetector          │ M2-7D
   70     │ BehavioralPatternDetector      │ M2-7E
   80     │ ConsistencyAcrossInterview     │ M2-7F
   90     │ ConfidenceCalibrationDetector  │ M2-7G
  100     │ LeadershipDetector             │ V1.2
  110     │ CollaborationDetector          │ V1.2
  120     │ AdaptabilityDetector           │ V1.2
─────────────────────────────────────────────────────
        ↓
ReasonerService.aggregate()
        ↓
CandidateProfileEngine.update()
        ↓
ReasonerDecision
```

**Performance Budget per Detector:**

| Tier | Target | Hard Limit |
|---|---|---|
| Foundation (priority ≤ 30) | < 1ms | 5ms |
| Core analytic (priority 40–90) | < 3ms | 10ms |
| Reserved (priority ≥ 100) | < 5ms | 20ms |
| Total pipeline | < 20ms | 50ms |

**Detector Dependency Graph:**

```
None ──→ EvaluationSignalDetector (5)
None ──→ CoverageDetector (10)
Coverage ──→ Consistency (20)
Consistency ──→ Trend (30)
Trend ──→ ReasoningDepth (40)
ReasoningDepth ──→ EngineeringJudgment (50)
Consistency ──→ Communication (60)
Trend ──→ BehavioralPattern (70)
Consistency + Trend ──→ ConsistencyAcrossInterview (80)
ConsistencyAcrossInterview ──→ ConfidenceCalibration (90)
BehavioralPattern ──→ Leadership (100)
Leadership ──→ Collaboration (110)
BehavioralPattern ──→ Adaptability (120)
```

---

### §18.4 — Detector / ProfileFeature / Consumer Matrix

| Detector | ProfileFeature | Dimension | NarrativeGenerator | ReportBuilder | CoachingEngine |
|---|---|---|---|---|---|
| EvaluationSignalDetector | KnowledgeDensityFeature | All | ✓ (M2-8) | ✓ (M2-9) | — |
| CoverageDetector | CoverageFeature | All | ✓ | ✓ | ✓ |
| ConsistencyDetector | ConsistencyFeature | All | ✓ | ✓ | — |
| TrendDetector | TrendFeature | All | ✓ | ✓ | ✓ |
| ReasoningDepthDetector | ReasoningDepthFeature | TECHNICAL_DEPTH, PROBLEM_SOLVING | ✓ | ✓ | ✓ |
| EngineeringJudgmentDetector | EngineeringJudgmentFeature | ENGINEERING_JUDGMENT | ✓ | ✓ | ✓ |
| CommunicationDetector | CommunicationFeature | COMMUNICATION | ✓ | ✓ | — |
| BehavioralPatternDetector | BehavioralPatternFeature | All | ✓ | — | ✓ |
| ConsistencyAcrossInterview | CrossDomainConsistencyFeature | All | — | ✓ | — |
| ConfidenceCalibrationDetector | ConfidenceCalibrationFeature | All | ✓ | — | ✓ |
| LeadershipDetector | LeadershipFeature | — | ✓ | ✓ | ✓ |
| CollaborationDetector | CollaborationFeature | — | — | ✓ | ✓ |
| AdaptabilityDetector | AdaptabilityFeature | — | ✓ | — | ✓ |

> **NarrativeGenerator (M2-8):** Consumes ProfileFeatures, NOT raw detector outputs. Detectors are invisible to the narrative layer. This is enforced by ADR-051.

---

### §18.5 — Detector Extensibility Rules

Every detector added to the system **MUST** comply with all of the following:

#### Mandatory Contracts

1. **Implements `PatternDetector`** — abstract base at `services/interview_reasoner/pattern_detection/base_detector.py`
2. **Declares `DetectorMetadata`** — name (unique), version (semver), priority (integer), enabled, dependencies
3. **Declares dependencies explicitly** — names of all detectors that must precede it in execution order; validated by `PatternDetectorRegistry`
4. **Deterministic** — identical inputs always produce identical outputs; no random state
5. **Stateless** — no instance-level mutable state; all state flows through `ReasonerInput`
6. **Never mutates `InterviewMemory`** — `ReasonerInput` is a read-only snapshot
7. **Never calls LLM** — no `openai`, `anthropic`, `langchain` imports
8. **Never performs prompt engineering** — no string formatting for model consumption
9. **Returns immutable `DetectorResult`** — all fields are frozen Pydantic models
10. **Supports registry auto-discovery** — registered via `build_default_registry()` factory; no detector self-registers

#### Idempotency Rule

Every detector that emits `EvidenceSignal`s **MUST** call `filter_new_signals(candidates, store)` from `signal_idempotency.py` before returning, to prevent evidence inflation on re-runs.

#### Performance Contract

Detectors **MUST** complete within the tier budget defined in §18.3. Detectors exceeding the hard limit must return an empty result with a warning rather than blocking the pipeline.

#### Design Guidelines

- **SRP**: One detector, one responsibility. If a detector's `detect()` method exceeds ~60 lines of logic, split into helpers.
- **OCP**: Detectors are never modified for new functionality. New requirements = new detector.
- **DIP**: Detectors depend on abstract contracts (`ReasonerInput`, `EvidenceSignal`), never on concrete service classes.
- **Naming**: `<Purpose>Detector`, e.g. `ReasoningDepthDetector`. Never `Util`, `Helper`, `Manager`.
- **Testing**: Each detector requires tests for: empty input, single signal, multi-cycle idempotency, dependency boundary, and performance budget.
- **File location**: `services/interview_reasoner/pattern_detection/detectors/<snake_name>.py`
- **Registration**: Added to `build_default_registry()` in `detectors/default_registry.py` with a comment referencing the milestone.

#### Detector Compatibility Policy (ADR-053)

A registered detector **MUST NOT** be removed or have its priority changed without a new ADR.  
Version bumps in `DetectorMetadata.version` are allowed for bug fixes.  
Dependency additions require a new ADR if they break existing execution order.

---

### §18.6 — ADRs (M2-7A)

---

#### ADR-048: ProfileFeature Abstraction — V1.2 Extension Point

**Status: Accepted — Architecture direction; implementation reserved for V1.2**

**Context:** `CandidateProfile` in M2-6C contains only `dimension_scores: dict[ProfileDimension, DimensionTrace]`. Future detectors (M2-7B+) produce signals that describe *qualitative* candidate characteristics not expressible as dimension scores — reasoning depth, communication style, leadership signals, confidence calibration.

**Decision:** A `ProfileFeature` abstraction is reserved in the architecture. `CandidateProfile` will gain a `features: dict[str, ProfileFeature]` field in V1.2 with `default_factory=dict`. All V1.1 code operates on `dimension_scores` only. V1.2 detectors write to `features` via the `CandidateProfileEngine`.

**Constraints:**
- `ProfileFeature` is NOT added to any V1.1 file.
- The field addition in V1.2 must be backward-compatible (optional, default empty).
- `CandidateProfileEngine.update()` signature does not change — the engine internally dispatches to a new `ProfileFeatureUpdater` in V1.2.

**Rationale:** Separating DimensionTrace (quantitative scoring) from ProfileFeatures (qualitative characteristics) prevents the profile from becoming a god object. Future features can be added without modifying existing updaters.

---

#### ADR-049: Advanced Detector Layering

**Status: Accepted — M2-7A**

**Context:** The M2-6C pipeline has 4 detectors at priorities 5, 10, 20, 30. M2-7+ will add 9 more. Without a frozen layering contract, priority conflicts and dependency cycles will emerge.

**Decision:** Detectors are organised into four tiers:

| Tier | Priority Range | Purpose |
|---|---|---|
| Foundation | 1–30 | Core signal bridging, coverage, consistency, trend |
| Analytic | 31–90 | Deep pattern analysis requiring foundation data |
| Behavioral | 91–120 | Long-context session analysis |
| Reserved | 121+ | Future V1.2+ detectors |

New detectors MUST declare the tier in their `DetectorMetadata` description field. Tier boundaries are frozen — no detector can be inserted into a lower tier without a new ADR.

**Constraints:** Priority slots 5, 10, 20, 30 are frozen for existing detectors. New detectors cannot claim these priorities.

---

#### ADR-050: NarrativeGenerator Consumes ProfileFeatures, Not Detector Outputs

**Status: Accepted — Architecture direction; NarrativeGenerator deferred to M2-8**

**Context:** A naive implementation of `NarrativeGenerator` (M2-8) would directly read detector outputs from `ReasonerDecision.reasoning_basis.detected_patterns`. This creates tight coupling between narrative and detection logic.

**Decision:** `NarrativeGenerator` consumes only `CandidateProfile` (including future `ProfileFeatures`). It never reads `ReasoningBasis`, `PatternMatch`, or `DetectorResult` directly.

**Enforcement:** `NarrativeGenerator` receives `CandidateProfile` as its sole profile input. Access to `ReasonerDecision` is limited to `follow_up_recommendation` and `navigation_recommendation`.

**Rationale:** Decouples the display layer from detection internals. Adding or removing a detector does not require `NarrativeGenerator` changes.

---

#### ADR-051: Detector Extensibility Contract (Plugin Architecture)

**Status: Accepted — M2-7A**

**Context:** As the detector ecosystem grows to 13+ detectors, ad-hoc additions risk inconsistent quality, missing idempotency guards, and performance regressions.

**Decision:** Every new detector is gated by a checklist enforced in code review. The checklist items are documented in §18.5. `PatternDetectorRegistry` validates priority uniqueness and dependency existence at registration time. Performance is validated in the detector's unit tests.

**Enforcement mechanism:** A `test_detector_contract.py` shared fixture validates all registered detectors against the contract at test time. Any detector failing the contract causes a test failure.

---

#### ADR-052: Evidence Freshness — Sliding Window for EvaluationSignalDetector

**Status: Accepted — M2-7B**

**Context:** The current `EvaluationBridgeDetector` bridges ALL historical evaluation signals every cycle. This was identified in M2-6B as a P2 calibration issue: a single `SHALLOW_ANSWER` from Q1 permanently dominates patterns even after 7 consecutive strong answers.

**Decision:** `EvaluationSignalDetector` (successor) implements a configurable sliding window: only signals from the last `N` questions are bridged (default N=3, configurable via `settings.reasoner_bridge_lookback_window`). Signals older than the window still exist in `EvidenceStore` (they are never deleted) but are not re-surfaced as active patterns.

**Migration:** `EvaluationBridgeDetector` remains registered until `EvaluationSignalDetector` is fully implemented and validated in M2-7B. After M2-7B, `EvaluationBridgeDetector` is unregistered and removed.

**Rationale:** Addresses M2-6B P2 calibration finding. Ensures pattern surface reflects recent session state, not entire session history.

---

#### ADR-053: Detector Compatibility Policy

**Status: Accepted — M2-7A**

**Context:** As the detector catalog grows, there must be a policy for versioning, deprecation, and removal.

**Decision:**
- **Addition**: Any new detector may be added by registering in `build_default_registry()` with an appropriate priority. A new ADR is required only if it modifies an existing dependency graph.
- **Priority change**: Requires a new ADR. Cannot be done unilaterally.
- **Removal**: Requires a new ADR and a deprecation period of at least one milestone.
- **Bug fix**: Version bump in `DetectorMetadata.version` (e.g. `1.0.0 → 1.0.1`). No ADR required.
- **Behavioral change**: Minor version bump (`1.0.0 → 1.1.0`). ADR required if it changes produced signal types.

---

#### ADR-055: Observation Abstraction — Reserved for V1.2

**Status: Proposed — M2-7C (documentation only; no production code)**

**Context:** M2-7B introduced ReasoningDepthDetector with three collaborators: Analyzer, Scorer, SignalFactory. M2-7C introduces EngineeringJudgmentDetector and CommunicationDetector with the same decomposition. As the detector count grows to 10+, a recurring pattern emerges: each Analyzer produces raw classification statistics, and each detector individually decides which of those statistics constitute a meaningful observation worthy of a PatternMatch or EvidenceSignal. There is no shared vocabulary for the explanation layer between the detection step and the signal emission step. The future Coaching Engine (V1.2) will need to explain *why* a signal was produced — not just *that* it was produced.

**Proposed Abstraction (V1.2):**

```
Evaluation (upstream)
      ↓
EvidenceStore (raw signals)
      ↓
Observation  ←─── NEW (V1.2)
      │  Captures: what the detector saw, in human-readable terms.
      │  Fields: observation_type, dimension, strength, description, supporting_signal_ids
      ↓
EvidenceSignal
      ↓
PatternMatch
```

An `Observation` is the intermediate explanation layer:
- Produced by the Analyzer/Scorer collaborator
- Carries a `description: str` field (short, non-candidate-facing explanation)
- Consumed by SignalFactory to build `EvidenceSignal`
- Consumed by CoachingEngine (V1.2) to generate human-readable coaching

**Why not now (M2-7C):** The Observation abstraction requires a stable `CoachingEngine` contract. Without a consumer, the abstraction would be speculative. All V1.1 Analyzers produce raw dataclasses (`JudgmentStats`, `CommunicationStats`, `DimensionDepthStats`) that can be upgraded to Observations in V1.2 without changing the detector external contract.

**V1.2 Migration Plan:**
- `JudgmentStats` → `JudgmentObservation(Observation)`
- `CommunicationStats` → `CommunicationObservation(Observation)`
- `DimensionDepthStats` → `DepthObservation(Observation)`
- `Observation` base class added to `domain/contracts/reasoning/observation.py`
- No changes to `PatternDetector` ABC or `DetectorResult` contract

**Constraints:**
- V1.1 code MUST NOT introduce `Observation` class or import it
- Analyzer return types remain plain dataclasses in V1.1
- The field `description` is reserved in collaborator docstrings

---

#### ADR-054: Detector Performance Budget

**Status: Accepted — M2-7A**

**Context:** The total Reasoner pipeline must not introduce latency perceptible to the interview experience. M2-7G adds 7 new detectors.

**Decision:** Each detector tier has a hard execution limit enforced at test time:

| Tier | Soft Target | Hard Limit |
|---|---|---|
| Foundation (≤ 30) | 1ms | 5ms |
| Analytic (31–90) | 3ms | 10ms |
| Behavioral (91–120) | 5ms | 20ms |
| Total pipeline | 20ms | 50ms |

Unit tests for each detector MUST include a `test_perf_within_budget` case asserting execution time ≤ hard limit with a realistic input (5 questions, 20 signals per dimension).

**Measurement:** `time.perf_counter()` wrapping `detector.detect()`. Budget applies to the pure computation, not imports or warmup.

---

### §18.7 — Implementation Roadmap

| Milestone | Deliverable | Detectors | Key New Capability |
|---|---|---|---|
| **M2-7A** | Architecture freeze | — | This document |
| **M2-7B** | EvaluationSignalDetector + ReasoningDepthDetector | DET-01 (v2), DET-05 | Sliding window bridging; reasoning depth scoring |
| **M2-7C** | EngineeringJudgmentDetector + CommunicationDetector | DET-06, DET-07 | Judgment + communication dimensions assessed; Observation ADR reserved (ADR-055) |
| **M2-7D** | BehavioralPatternDetector + ConsistencyAcrossInterviewDetector | DET-08, DET-09 | Behavioral + cross-area consistency detection |
| **M2-7E** | Framework Consolidation (DDS + ADRs) | — | Detector Development Standard frozen |
| **M2-7F** | ConfidenceCalibrationDetector | DET-10 | Self-assessment calibration |
| **M2-8** | NarrativeGenerator | — | Reads CandidateProfile; produces coaching text |
| **M2-9** | ReportBuilder | — | Structured session report from ProfileFeatures |
| **V1.2** | ProfileFeatures activation + Leadership/Collaboration/Adaptability | DET-11–13 | Full qualitative profile |
| **V1.2** | CoachingEngine | — | Actionable improvement recommendations |


---

## §19 — Detector Development Standard (DDS) — M2-7E Freeze

> **Status: Frozen — M2-7E**
> This section is the single authoritative reference for implementing, testing, registering, and evolving any Pattern Detector in this project. It supersedes any informal conventions established in M2-3 through M2-7D. All future detectors (M2-7F onward) must comply with this standard.

---

### §19.1 — Detector Taxonomy (Layer Model)

Detectors are organised into four layers. Layer membership is determined by the **nature of input consumed**, not by the signals produced.

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Foundation Detectors  (priority 1–30)              │
│  Input: Raw EvidenceStore signals from Evaluation pipeline   │
│  Purpose: Surface and normalise evaluation evidence          │
│  Examples: EvaluationSignalDetector, CoverageDetector,       │
│            ConsistencyDetector, TrendDetector                │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Analytical Detectors  (priority 31–69)             │
│  Input: Enriched EvidenceStore (after Foundation pass)       │
│  Purpose: Dimension-specific deep analysis                   │
│  Examples: ReasoningDepthDetector, EngineeringJudgmentDet.,  │
│            CommunicationDetector                             │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Behavioral Detectors  (priority 70–99)             │
│  Input: ReasoningHistory + full EvidenceStore                │
│  Purpose: Session-level patterns across multiple answers     │
│  Examples: BehavioralPatternDetector,                        │
│            ConsistencyAcrossInterviewDetector,               │
│            Leadership, Collaboration, Adaptability (V1.2)   │
├──────────────────────────────────────────────────────────────┤
│  Layer 4: Calibration Detectors  (priority 100–130)          │
│  Input: CandidateProfile (dimension_scores + signals)        │
│  Purpose: Meta-analysis of candidate self-assessment         │
│  Examples: ConfidenceCalibrationDetector (DET-10, M2-7F)    │
└──────────────────────────────────────────────────────────────┘
```

**Layer ownership rules:**

| Layer | Reads from | May NOT read from |
|---|---|---|
| Foundation | `EvidenceStore` (raw signals only) | `ReasoningHistory`, `CandidateProfile` |
| Analytical | `EvidenceStore` (enriched) | `ReasoningHistory`, `CandidateProfile.dimension_scores` |
| Behavioral | `ReasoningHistory`, `EvidenceStore` | `CandidateProfile.dimension_scores` (use scores only if unavoidable) |
| Calibration | `CandidateProfile` (full) | — (may read everything) |

---

### §19.2 — Dependency Rules

**Formal rule: dependencies are strictly downward within the layer graph.**

```
Foundation (1–30)
    ↓ (allowed)
Analytical (31–69)
    ↓ (allowed)
Behavioral (70–99)
    ↓ (allowed)
Calibration (100–130)
```

**Forbidden dependency directions:**

- A Foundation detector may NOT depend on Analytical, Behavioral, or Calibration.
- An Analytical detector may NOT depend on another Analytical detector in a higher priority slot unless explicitly documented with an ADR rationale.
- A Behavioral detector may NOT depend on Calibration.
- No detector may have a cyclic dependency. The `PatternDetectorRegistry` enforces this via DFS at registration time.

**Within-layer dependencies** (same-layer priority constraints):

- Within Analytical: `ReasoningDepthDetector(40)` → `EngineeringJudgmentDetector(50)` → `CommunicationDetector(60)` is the canonical chain. New Analytical detectors must choose a priority > 60 and < 70.
- Within Behavioral: `BehavioralPatternDetector(70)` → `ConsistencyAcrossInterviewDetector(80)`. New Behavioral detectors must be in range 70–99.
- Within Calibration: `ConfidenceCalibrationDetector(90)` (NOTE: priority 90 is in Behavioral range; effective layer is Calibration by input type). Future calibration detectors: 100–130.

**Priority slot policy (ADR-049, supplemented here):**

- Priorities 5, 10, 20, 30, 40, 50, 60, 70, 80 are occupied by existing detectors.
- New detectors must NOT claim an occupied priority.
- Priority changes require a new ADR.

---

### §19.3 — Mandatory Detector Contract

Every `PatternDetector` subclass MUST expose these elements without exception:

#### 19.3.1 — Metadata

```python
_METADATA = DetectorMetadata(
    name="<DetectorName>",     # unique, PascalCase, ends with "Detector"
    version="1.0.0",           # semver; bump on behavioral changes
    priority=<int>,            # unique; must comply with layer range
    enabled=True,              # default; feature-flag gate
    dependencies=["<Name>"],   # must be registered before this detector
)
```

- `name` must exactly match the class name.
- `version` follows semantic versioning: `MAJOR.MINOR.PATCH`.
  - PATCH: bug fix, no signal type change.
  - MINOR: new produced signal types added (backward-compatible).
  - MAJOR: produced signal types removed or renamed (breaking change → new ADR required).

#### 19.3.2 — detect() Contract

```python
def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
    ...
```

**Mandatory invariants:**

1. **Deterministic**: same input → same output, always.
2. **Stateless**: no instance-level mutable state; all state from `reasoner_input`.
3. **Side-effect-free**: no writes, no I/O, no networking, no database.
4. **No LLM calls**: ADR-028, absolute prohibition.
5. **O(n)** over session history (or bounded polynomial for cross-area analysis).
6. **Idempotency guard**: every candidate signal must pass through `filter_new_signals()` before being placed in `generated_signals`.
7. **Empty result on insufficient data**: never emit signals when guard conditions are not met. Return `DetectorResult(detector_name=_METADATA.name)`.

#### 19.3.3 — DetectorResult Fields

| Field | Required | Notes |
|---|---|---|
| `detector_name` | ✓ | Must equal `_METADATA.name` |
| `matches` | When non-empty | List of `PatternMatch`; one per detected rule |
| `generated_signals` | When non-empty | Output of `filter_new_signals()` |
| `confidence` | Optional | Default `ReasoningConfidence()` |
| `warnings` | Optional | Internal diagnostics only; NEVER candidate-facing |
| `execution_time_ms` | Auto | Populated by `ReasonerService` pipeline |

#### 19.3.4 — PatternMatch Contract

```python
PatternMatch(
    pattern_type=EvidenceType.<VALUE>,   # signal type produced
    evidence_signals=[sig],              # supporting evidence
    label="<context>: <details>",       # max 200 chars; no candidate text
)
```

- `label` must NEVER contain candidate-supplied text.
- `label` must identify the detector context and key metric.

#### 19.3.5 — EvidenceSignal Contract

All signals produced by detectors MUST have:

```python
EvidenceSignal(
    id=str(uuid.uuid4()),           # unique per signal
    source=EvidenceSource.PATTERN_DETECTOR,  # always
    dimension=ProfileDimension.<X>, # the dimension this signal relates to
    polarity=EvidencePolarity.<P>,  # POSITIVE or NEGATIVE
    signal_type=EvidenceType.<T>,   # must be defined in EvidenceType enum
    strength=<float in [0.0, 1.0]>, # derived from analysis metrics
    question_index=q_idx,
    question_area=area,
    timestamp_question_index=q_idx,
)
```

---

### §19.4 — Decomposition Standard (Collaborator Pattern)

Every non-trivial detector MUST be decomposed into three collaborators:

```
detectors/<feature_name>/
    analyzer.py        ← BoundedObservationExtractor (or *Analyzer)
    scorer.py          ← *Scorer
    signal_factory.py  ← *SignalFactory
```

**Analyzer responsibility:**
- Single O(n) pass over input data.
- Returns a plain `@dataclass(frozen=True)` stats object.
- No business logic — only classification and counting.
- V1.2: this dataclass will be promoted to an `Observation` subclass.

**Scorer responsibility:**
- Pure function: receives stats object, returns Verdict enum.
- No I/O; no side effects.
- Threshold constants defined at module level (not inside methods).
- All guard conditions checked here (min evidence, min entries, etc.).

**SignalFactory responsibility:**
- Maps Verdict + stats → `EvidenceSignal | None`.
- `None` returned for NEUTRAL verdict.
- All signals have `source=EvidenceSource.PATTERN_DETECTOR`.
- Strength derived from analysis metrics, clamped to `[0.0, 1.0]`.

**Main Detector responsibility:**
- Orchestrates Analyzer → Scorer → SignalFactory.
- Builds `PatternMatch` objects.
- Calls `filter_new_signals()` before returning.
- No business logic beyond orchestration.

**Size limits (ADR-056):**

| File | Max LOC |
|---|---|
| Main Detector | 150 |
| Analyzer | 120 |
| Scorer | 60 |
| SignalFactory | 80 |

---

### §19.5 — Performance Standard

**Mandatory rules (ADR-054, extended here):**

| Rule | Requirement |
|---|---|
| Algorithmic complexity | O(n) over EvidenceStore signals |
| Cross-dimension comparison | O(d × a²) permitted; d,a bounded (≤5 dims, ≤10 areas) |
| History traversal | O(h) where h ≤ 20 (ReasoningHistory.MAX_ENTRIES) |
| Nested scans | Forbidden unless both dimensions are bounded and documented |
| Global mutable state | Forbidden (no module-level caches, no class-level mutation) |
| I/O | Forbidden (no file reads, no DB queries, no network calls) |
| LLM calls | Forbidden (ADR-028) |
| Prompt templates | Forbidden |
| External process | Forbidden |

**Performance budget (ADR-054):**

| Layer | Soft Target | Hard Limit |
|---|---|---|
| Foundation (≤ 30) | < 1ms | 5ms |
| Analytical (31–69) | < 3ms | 10ms |
| Behavioral (70–99) | < 5ms | 10ms |
| Calibration (100–130) | < 5ms | 20ms |
| Total pipeline | < 20ms | 50ms |

**Measurement standard:** `time.perf_counter()` wrapping `detector.detect()`. Warmup excluded.

---

### §19.6 — Test Standard

Every detector requires four test files:

```
tests/services/interview_reasoner/pattern_detection/detectors/
    <feature>/
        test_analyzer.py       ← unit tests for Analyzer
        test_scorer.py         ← unit tests for Scorer
        test_signal_factory.py ← unit tests for SignalFactory
    test_<feature>_detector.py ← integration tests for main Detector
```

**Mandatory test coverage per collaborator:**

**Analyzer tests (minimum 8 cases):**
- Empty input → neutral stats
- Single signal of each relevant type
- Wrong polarity on correct type → not counted
- Multi-dimension split
- Irrelevant signal types ignored
- Ratio/count properties

**Scorer tests (minimum 8 cases):**
- NEUTRAL when below minimum evidence/entries
- Each non-neutral verdict
- Threshold boundary cases (both sides)
- Verdict precedence (if multiple verdicts possible)

**SignalFactory tests (minimum 8 cases):**
- Each verdict → correct signal type
- NEUTRAL → None
- Polarity correct per verdict
- Strength derivation
- `source = PATTERN_DETECTOR`
- `dimension` correct
- Unique IDs across calls
- Strength clamped to [0.0, 1.0]

**Main Detector tests (minimum 15 cases):**
- Metadata: name, priority, dependencies, version
- Each positive verdict scenario
- Each negative verdict scenario
- Guard condition: insufficient data → empty result
- Idempotency: no re-emission after signal already in store
- False positive: wrong dimension/area signals ignored
- Signal contract: source, dimension correct
- Label content verification

**Target: 40–50 new tests per detector.**

---

### §19.7 — EvidenceType Registration Policy

New `EvidenceType` values added by a detector must:

1. Be grouped with a comment identifying the milestone (e.g., `# --- M2-7D ---`).
2. Follow the naming convention: `<DIMENSION_OR_CONCEPT>_<QUALIFIER>` (e.g., `BEHAVIORAL_GROWTH`, `CROSS_AREA_CONSISTENT`).
3. Be positive-leaning values for positive polarity signals.
4. Be documented in the detector's module docstring under "Signals emitted".
5. Never be re-used across detectors with different semantics.

**Existing EvidenceType enum as of M2-7D:**

```
Original (12):  REPEATED_STRENGTH, RECOVERED_WEAKNESS, DEMONSTRATED_DEPTH,
                ENGINEERING_JUDGMENT_ARTICULATED, REPEATED_WEAKNESS, KNOWLEDGE_GAP,
                COMMUNICATION_GAP, REASONING_GAP, CONFIDENCE_DROP, MISSING_EVIDENCE,
                SHALLOW_ANSWER, CONTRADICTORY_ANSWER

M2-7B (4):      REASONING_DEPTH_HIGH, REASONING_DEPTH_LOW,
                REASONING_IMPROVING, REASONING_STAGNATING

M2-7C (5):      ENGINEERING_JUDGMENT_HIGH, ENGINEERING_JUDGMENT_LOW,
                COMMUNICATION_CLEAR, COMMUNICATION_WEAK, COMMUNICATION_INCONSISTENT

M2-7D (5):      BEHAVIORAL_GROWTH, BEHAVIORAL_INSTABILITY, BEHAVIORAL_PLATEAU,
                CROSS_AREA_CONSISTENT, CROSS_AREA_CONTRADICTORY

Total: 26
```

---

### §19.8 — Detector Lifecycle

Every detector passes through the following lifecycle stages. No stage may be skipped.

```
1. DESIGN
   ├── Requirements from TDS §18 DET-XX
   ├── Input/output contract documented
   ├── Layer assignment determined
   └── ADR created if decisions deviate from TDS

2. IMPLEMENTATION
   ├── Collaborators (Analyzer, Scorer, SignalFactory) implemented first
   ├── Main Detector orchestrates collaborators
   └── All files < LOC limits (§19.4)

3. TESTING
   ├── Unit tests per collaborator
   ├── Integration tests per main Detector
   └── Coverage ≥ 40 test cases

4. REGISTRY
   ├── Registered in build_default_registry()
   ├── Priority unique and within layer range
   ├── Dependencies declared and already registered
   └── Registry cycle-check passes

5. AUDIT
   ├── Code review against DDS §19.3–§19.6
   ├── Performance budget verified
   └── No detector-specific code in ReasonerService

6. DOCUMENTATION
   ├── DET-XX entry in TDS §18.2
   ├── Module-level docstring complete
   ├── V1.2 Observation/ProfileFeature mapping documented
   └── Roadmap table updated

7. RELEASE
   ├── Included in milestone tag
   └── Regression suite green

8. MONITORING (V1.2+)
   ├── Execution time metrics
   ├── Signal emission rates
   └── False positive / false negative rates (future Diagnostics layer)

9. FUTURE EXTENSION
   ├── Version bump if behavior changes (§19.3.1)
   ├── New ADR if signal types change
   └── Observation upgrade path ready (§19.9)
```

---

### §19.9 — V1.2 Evolution Path

**No production code changes are defined here. This section freezes the V1.2 migration path so that V1.1 implementation decisions are forward-compatible.**

#### 19.9.1 — Observation Layer

The `Observation` abstraction (ADR-055) will be introduced in V1.2:

```
V1.1 Analyzer returns:   @dataclass(frozen=True) stats
V1.2 Analyzer returns:   Observation(stats + description: str + observation_type: ObservationType)
```

**Migration strategy per detector:**

| V1.1 Dataclass | V1.2 Observation |
|---|---|
| `DimensionDepthStats` | `DepthObservation` |
| `JudgmentStats` | `JudgmentObservation` |
| `CommunicationStats` | `CommunicationObservation` |
| `BehavioralStats` | `BehavioralObservation` |
| `CrossAreaResult` | `ConsistencyObservation` |

The `description` field on each `Observation` will be the input to the `CoachingEngine`.

**V1.1 detectors are forward-compatible because:**
- Dataclasses are frozen and immutable — no changes needed to existing code.
- The V1.2 migration wraps existing dataclasses rather than replacing them.
- `PatternDetector` ABC signature does not change.
- `DetectorResult` contract does not change.

#### 19.9.2 — ProfileFeature Layer

The `ProfileFeature` abstraction (ADR-048) will be activated in V1.2:

```
V1.1: CandidateProfile.dimension_scores only
V1.2: CandidateProfile.dimension_scores + CandidateProfile.features: dict[str, ProfileFeature]
```

**Detector → ProfileFeature mapping (frozen for V1.2 planning):**

| Detector | ProfileFeature class | V1.2 writer |
|---|---|---|
| ReasoningDepthDetector | `ReasoningDepthFeature` | `CandidateProfileEngine` |
| EngineeringJudgmentDetector | `EngineeringJudgmentFeature` | `CandidateProfileEngine` |
| CommunicationDetector | `CommunicationFeature` | `CandidateProfileEngine` |
| BehavioralPatternDetector | `BehavioralPatternFeature` | `CandidateProfileEngine` |
| ConsistencyAcrossInterviewDetector | `CrossDomainConsistencyFeature` | `CandidateProfileEngine` |
| ConfidenceCalibrationDetector | `ConfidenceCalibrationFeature` | `CandidateProfileEngine` |

#### 19.9.3 — AbstractAnalyticalDetector (Reserved)

A future base class `AbstractAnalyticalDetector` may be introduced in V1.2 to reduce boilerplate across the Analyzer→Scorer→SignalFactory chain. The pattern is sufficiently uniform that extraction is mechanical. The V1.2 decision will depend on:
- Whether ≥ 5 Analytical-layer detectors exist and share ≥ 50% of orchestration code.
- Whether the abstraction improves testability without adding indirection cost.

**V1.1 detectors are forward-compatible because:** the base class would inject the orchestration as a template method, not replace the existing orchestration.

#### 19.9.4 — DetectorPipeline

A future `DetectorPipeline` abstraction could replace `ReasonerService._run_detectors()` with a composable, configurable pipeline object. This is deferred to V1.2 pending `NarrativeGenerator` and `CoachingEngine` requirements.

#### 19.9.5 — Detector Diagnostics (V1.2+)

A `DetectorDiagnostics` subsystem will be introduced to track:
- Per-detector emission rates (signals emitted / calls)
- Per-detector execution time percentiles
- False positive indicators (signals emitted but no follow-up action taken)
- Version compatibility tracking

**V1.1 compatibility:** `DetectorResult.warnings` is the existing hook for diagnostic messages. No changes needed to V1.1 detectors.

---

### §19.10 — New ADRs (M2-7E)

---

#### ADR-056: Detector File Size Limits

**Status: Accepted — M2-7E**

**Context:** As the detector ecosystem grows, individual files risk exceeding maintainability thresholds. Experience from M2-7B through M2-7D shows that detectors decomposed into Analyzer/Scorer/SignalFactory naturally stay within 60–120 LOC per file.

**Decision:** Enforce the following soft limits:

| File | Soft Limit | Hard Limit |
|---|---|---|
| Main Detector | 120 LOC | 150 LOC |
| Analyzer | 100 LOC | 120 LOC |
| Scorer | 50 LOC | 60 LOC |
| SignalFactory | 70 LOC | 80 LOC |

Files exceeding the hard limit require documented justification in the code review. A detector exceeding the soft limit is a signal that SRP is being violated.

**Rationale:** Enforces SRP at the file level. Large files are a leading indicator of mixed responsibilities.

---

#### ADR-057: Detector Dependency Direction Enforcement

**Status: Accepted — M2-7E**

**Context:** The detector layer model (§19.1) defines four layers. Without explicit rules, future detectors could introduce upward dependencies (e.g., a Foundation detector depending on an Analytical one), breaking the layering contract.

**Decision:** Dependency direction must be downward only (higher priority → lower priority allowed as dependency, but only within documented allowed patterns). The `PatternDetectorRegistry` validates existence and cycle-freedom at registration time. Layer direction is validated by the DDS checklist at code review time (not yet automated).

**V1.2 enforcement:** A `LayerValidator` utility will be introduced to automate the direction check at registration time.

**Rationale:** Prevents architectural debt. Ensures the detector pipeline remains a DAG, not a mesh.

---

#### ADR-058: Detector Versioning and Compatibility

**Status: Accepted — M2-7E**

**Context:** Detectors produce `EvidenceSignal` records that flow into `EvidenceStore`, `CandidateProfile`, and eventually `ReasonerDecision`. A behavioral change in a detector without a version bump is silent and hard to debug.

**Decision:**

| Change type | Version action | ADR required? |
|---|---|---|
| Bug fix (same signals) | `PATCH` bump | No |
| New signal types added | `MINOR` bump | No |
| Signal types removed/renamed | `MAJOR` bump | Yes |
| Priority change | `MINOR` bump | Yes |
| Dependency change | `MINOR` bump | Yes |
| Enabled→Disabled | `MINOR` bump | No |

The `DetectorMetadata.version` field is the single source of truth for detector version.

**Monitoring hook:** `ReasonerService` logs `detector_name + version` per cycle in `ReasoningTraceStep.summary`. Future `DetectorDiagnostics` will use this for version-drift detection.

---

#### ADR-059: Detector Deprecation Policy

**Status: Accepted — M2-7E**

**Context:** As the detector catalog matures, some detectors will be superseded (e.g., `EvaluationBridgeDetector` was superseded by `EvaluationSignalDetector` in M2-7B). Without a formal policy, deprecated detectors accumulate.

**Decision:**

1. **Deprecation notice**: Set `enabled=False` in `DetectorMetadata`. Add `# DEPRECATED: <reason>` to the class docstring. Bump `MINOR` version.
2. **Deprecation period**: Minimum one milestone (≈ 1–2 weeks).
3. **Removal**: Remove from `build_default_registry()`. Keep file for one additional milestone. Then delete.
4. **Signal type retirement**: Signal types produced exclusively by a removed detector must be added to a `DEPRECATED_EVIDENCE_TYPES` frozenset in `evidence_type.py` for one milestone before removal from the enum.

**Existing deprecated detector:** `EvaluationBridgeDetector` — deprecated M2-7B, removed from registry. May be deleted from codebase in M2-8.

---

#### ADR-060: Detector Test Coverage Standard

**Status: Accepted — M2-7E**

**Context:** Detector tests in M2-7B through M2-7D were written ad-hoc. The test counts (40–50 per detector) and coverage patterns were consistent but undocumented. Formalising the standard ensures consistency for future detectors.

**Decision:** The minimum test requirement per detector is:

| Test file | Minimum cases | Coverage focus |
|---|---|---|
| `test_analyzer.py` | 8 | Empty, signal classification, polarity rules, multi-dim |
| `test_scorer.py` | 8 | Guard conditions, each verdict, boundaries, precedence |
| `test_signal_factory.py` | 8 | Each verdict → correct signal, NEUTRAL→None, contract fields |
| `test_<name>_detector.py` | 15 | Metadata, scenarios, guards, idempotency, false positives |

**Total minimum:** 39 tests per detector. Target: 40–50.

Any pull request introducing a new detector with fewer than 39 tests must be rejected.

---

#### ADR-061: Detector Framework Stability Guarantee

**Status: Accepted — M2-7E**

**Context:** The DDS (§19) defines the architecture for all V1.1 detectors. V1.2 will introduce `Observation`, `ProfileFeature`, and potentially `AbstractAnalyticalDetector`. It is critical that the V1.2 evolution does not require rewriting V1.1 detectors.

**Decision:** The following are **frozen and backward-compatible guarantees** for V1.2:

1. `PatternDetector` ABC signature (`metadata` + `detect(ReasonerInput) → DetectorResult`) does not change.
2. `DetectorMetadata` fields do not change (new fields are additive and optional).
3. `DetectorResult` contract does not change.
4. `EvidenceSignal` contract does not change.
5. `filter_new_signals()` identity key does not change.
6. `PatternDetectorRegistry` interface does not change.
7. All V1.1 `EvidenceType` values are preserved (no renames, no removals in V1.2).
8. All V1.1 detectors remain registered and enabled unless explicitly deprecated.

**V1.2 additions are purely additive:** new dataclasses, new fields, new classes. No breaking changes to V1.1 interfaces.

---

### §19.11 — Detector Implementation Checklist

The following checklist is mandatory for every new detector before merging:

**Design**
- [ ] DET-XX entry created in TDS §18.2 with input/output/acceptance criteria
- [ ] Layer assignment documented (Foundation / Analytical / Behavioral / Calibration)
- [ ] Priority slot unique and within layer range
- [ ] Dependencies declared and within allowed direction rules
- [ ] New `EvidenceType` values added with milestone comment
- [ ] V1.2 Observation mapping documented in module docstring

**Implementation**
- [ ] Collaborators created in `detectors/<feature>/` subfolder
- [ ] Analyzer: O(n) pass, frozen dataclass output, no business logic
- [ ] Scorer: pure function, thresholds as module constants, guard conditions first
- [ ] SignalFactory: NEUTRAL → None, `source=PATTERN_DETECTOR`, strength clamped [0,1]
- [ ] Main Detector: < 150 LOC, orchestration only, calls `filter_new_signals()`
- [ ] No detector-specific code added to `ReasonerService`
- [ ] No LLM calls anywhere in the detector

**Testing**
- [ ] `test_analyzer.py` ≥ 8 cases
- [ ] `test_scorer.py` ≥ 8 cases
- [ ] `test_signal_factory.py` ≥ 8 cases
- [ ] `test_<name>_detector.py` ≥ 15 cases (total ≥ 39)
- [ ] Idempotency test present
- [ ] False positive test present
- [ ] Guard condition test present

**Registry**
- [ ] Registered in `build_default_registry()`
- [ ] Dependency declared in `_METADATA.dependencies`
- [ ] All dependencies already in registry before this detector
- [ ] `build_default_registry()` cycle-check passes

**Documentation**
- [ ] Roadmap table §18.7 updated
- [ ] Module docstring complete (purpose, priority, deps, signals, V1.2 notes)
- [ ] Regression suite green

---

## §20 — M2-7F Design Freeze: Leadership, Collaboration & Adaptability Detectors

> **Status: Frozen — 2026-07-01 | Milestone: M2-7F (Design Only)**
> This section freezes the complete design of DET-11, DET-12, and DET-13 — the final behavioral
> detector family. Zero production code is introduced here. Implementation in V1.2 must be purely
> mechanical: all architectural decisions are resolved by this document.

---

### §20.1 — Behavioral Detector Family Overview

The final three detectors complete the behavioral detection tier. They operate at the highest
priority range (100–120) in the Behavioral Layer and are designed exclusively to assess
**interpersonal and professional growth signals** — never technical correctness.

```
Behavioral Detection Tier (V1.1 foundation)
  BehavioralPatternDetector              (70) ← growth/instability over session
  ConsistencyAcrossInterviewDetector     (80) ← cross-domain signal consistency

Behavioral Detection Tier (V1.2 completion)
  LeadershipDetector                    (100) ← ownership, initiative, accountability
  CollaborationDetector                 (110) ← teamwork, knowledge sharing, conflict
  AdaptabilityDetector                  (120) ← recovery, flexibility, reframing
```

**Family ownership rules:**

| Detector | Owns exclusively |
|---|---|
| `BehavioralPatternDetector` | Session-level growth/instability patterns over time |
| `ConsistencyAcrossInterviewDetector` | Cross-domain signal coherence |
| `LeadershipDetector` | Ownership, accountability, initiative, mentoring, strategic thinking |
| `CollaborationDetector` | Team orientation, conflict management, knowledge sharing, feedback |
| `AdaptabilityDetector` | Recovery, flexibility, context-switching, reframing, change acceptance |

**Absolute forbidden overlaps:**

- `LeadershipDetector` MUST NOT assess communication quality → owned by `CommunicationDetector`
- `LeadershipDetector` MUST NOT assess technical correctness → owned by evaluation pipeline
- `CollaborationDetector` MUST NOT assess reasoning depth → owned by `ReasoningDepthDetector`
- `CollaborationDetector` MUST NOT assess grammar or language quality → owned by `CommunicationDetector`
- `AdaptabilityDetector` MUST NOT assess whether answers are correct → outside its scope
- `AdaptabilityDetector` MUST NOT assess domain knowledge → outside its scope
- No behavioral detector may assess `ProfileDimension.ENGINEERING_JUDGMENT` → owned by `EngineeringJudgmentDetector`

---

### §20.2 — DET-11: LeadershipDetector (Full Specification)

#### 20.2.1 — Identity

| Field | Value |
|---|---|
| **Class name** | `LeadershipDetector` |
| **Priority** | 100 |
| **Tier** | Behavioral (V1.2) |
| **Milestone** | V1.2 |
| **Dependencies** | `ConsistencyAcrossInterviewDetector` |
| **Version** | `1.0.0` |
| **Performance budget** | < 5ms soft / 20ms hard |
| **Complexity** | O(n) over EvidenceStore signals + O(h) over ReasoningHistory |

#### 20.2.2 — Purpose and Scope

Detect **leadership potential** emerging through interview behavior. Leadership signals are
inferred from how the candidate describes their actions and role in situations — not from
the technical quality of the actions themselves.

**Signals within scope:**

| Signal concept | Definition |
|---|---|
| Ownership | Candidate uses first-person accountability language; does not deflect responsibility |
| Decision responsibility | Candidate describes making decisions, not just implementing others' decisions |
| Initiative | Candidate describes proactively identifying problems or improvements without being asked |
| Mentoring attitude | Candidate references teaching, explaining, guiding, or developing others |
| Technical influence | Candidate describes shaping team direction, standards, or architectural choices |
| Strategic thinking | Candidate demonstrates awareness of long-term trade-offs and context beyond the immediate task |
| Accountability | Candidate owns failures, describes lessons learned, does not externalize blame |

**Explicitly outside scope (never evaluate):**

- Technical correctness of any described action
- Knowledge depth on any technical topic
- Communication quality, grammar, or fluency
- Engineering judgment (owned by `EngineeringJudgmentDetector`)
- Reasoning structure (owned by `ReasoningDepthDetector`)

#### 20.2.3 — Input Contract

| Source | Field | Usage |
|---|---|---|
| `ReasonerInput.interview_memory.evidence_store` | Behavioral signals from `BehavioralPatternDetector` | Primary signal source |
| `ReasonerInput.interview_memory.reasoning_history` | Pattern continuity across recent cycles | Trend detection |
| `ReasonerInput.interview_memory.candidate_profile.dimension_scores` | `PROBLEM_SOLVING` DimensionTrace | Baseline anchoring only |

The detector reads signals with `EvidenceType` values from the behavioral family:
`BEHAVIORAL_GROWTH`, `BEHAVIORAL_INSTABILITY`, `CROSS_AREA_CONSISTENT`, `CROSS_AREA_CONTRADICTORY`.

It does NOT read signals from Analytical-layer detectors directly.

#### 20.2.4 — Analyzer: `LeadershipAnalyzer`

**Responsibility:** Single O(n) pass over behavioral signals in EvidenceStore. Classifies each
signal as contributing to one or more leadership dimensions. Returns a frozen dataclass.

**Output dataclass:**

```
@dataclass(frozen=True)
class LeadershipStats:
    ownership_signal_count: int       # signals tagged with ownership indicators
    initiative_signal_count: int      # signals tagged with initiative indicators
    accountability_signal_count: int  # signals tagged with accountability indicators
    mentoring_signal_count: int       # signals tagged with mentoring indicators
    strategic_signal_count: int       # signals tagged with strategic thinking indicators
    total_behavioral_signals: int     # denominator for ratios
    leadership_ratio: float           # (ownership + initiative + accountability) / total
    trend: str                        # "RISING" | "STABLE" | "DECLINING" | "INSUFFICIENT"
```

**Classification rules:**

| Leadership dimension | Evidence types that contribute |
|---|---|
| Ownership | `BEHAVIORAL_GROWTH` with `dimension=PROBLEM_SOLVING`, strong positive polarity |
| Initiative | `BEHAVIORAL_GROWTH` with cross-area signals showing proactive action |
| Accountability | `BEHAVIORAL_GROWTH` following a `BEHAVIORAL_INSTABILITY` (recovery pattern) |
| Mentoring | Signal labels mentioning cross-area teaching or explaining patterns |
| Strategic | `CROSS_AREA_CONSISTENT` patterns across >= 3 distinct question areas |

**Guard condition:** Analyzer returns zeroed stats if `total_behavioral_signals < 2`.

**V1.2 migration:** `LeadershipStats` → `LeadershipObservation(Observation)` with a
`description: str` field summarizing the pattern.

#### 20.2.5 — Scorer: `LeadershipScorer`

**Responsibility:** Pure function. Receives `LeadershipStats`, returns `LeadershipVerdict`.

```python
class LeadershipVerdict(str, Enum):
    STRONG_LEADER     = "STRONG_LEADER"      # leadership_ratio >= 0.6 and >= 2 dimensions
    EMERGING_LEADER   = "EMERGING_LEADER"    # leadership_ratio >= 0.35 and >= 1 dimension
    NEUTRAL           = "NEUTRAL"            # insufficient or mixed evidence
    LEADERSHIP_ABSENT = "LEADERSHIP_ABSENT"  # behavioral signals present but none leadership-coded
```

**Threshold constants (module-level):**

```python
MIN_BEHAVIORAL_SIGNALS         = 3
MIN_LEADERSHIP_RATIO_STRONG    = 0.60
MIN_LEADERSHIP_RATIO_EMERGING  = 0.35
MIN_DIMENSIONS_STRONG          = 2
MIN_DIMENSIONS_EMERGING        = 1
```

**Guard condition:** Returns `NEUTRAL` if `total_behavioral_signals < MIN_BEHAVIORAL_SIGNALS`.

**Verdict precedence:** STRONG_LEADER > EMERGING_LEADER > LEADERSHIP_ABSENT > NEUTRAL.
NEUTRAL is returned only when guard conditions are not met (not when evidence is negative).

#### 20.2.6 — SignalFactory: `LeadershipSignalFactory`

**Responsibility:** Maps `LeadershipVerdict + LeadershipStats` → `EvidenceSignal | None`.

| Verdict | EvidenceType | Polarity | Strength formula |
|---|---|---|---|
| `STRONG_LEADER` | `LEADERSHIP_STRONG` | POSITIVE | `min(1.0, leadership_ratio * 1.5)` |
| `EMERGING_LEADER` | `LEADERSHIP_EMERGING` | POSITIVE | `leadership_ratio` |
| `LEADERSHIP_ABSENT` | `LEADERSHIP_ABSENT` | NEGATIVE | `0.4` (fixed) |
| `NEUTRAL` | — | — | Returns `None` |

**Signal contract:**

```python
EvidenceSignal(
    id=str(uuid.uuid4()),
    source=EvidenceSource.PATTERN_DETECTOR,
    dimension=ProfileDimension.PROBLEM_SOLVING,  # temporary V1.1 mapping; see ADR-063
    polarity=<per verdict>,
    signal_type=<per verdict>,
    strength=<per formula, clamped [0.0, 1.0]>,
    question_index=latest_question_index,
    question_area=current_area,
    timestamp_question_index=latest_question_index,
)
```

**Rule:** `NEUTRAL` verdict → return `None`. No signal emitted.

#### 20.2.7 — Main Detector: `LeadershipDetector`

**Orchestration:**

```
detect(reasoner_input):
    1. Guard: if insufficient behavioral signals → return empty DetectorResult
    2. analyzer = LeadershipAnalyzer(); stats = analyzer.analyze(reasoner_input)
    3. scorer = LeadershipScorer(); verdict = scorer.score(stats)
    4. factory = LeadershipSignalFactory(); signal = factory.create(verdict, stats, reasoner_input)
    5. candidates = [signal] if signal else []
    6. new_signals = filter_new_signals(candidates, reasoner_input.interview_memory.evidence_store)
    7. match = PatternMatch(pattern_type=verdict_to_evidence_type(verdict), ...)
    8. return DetectorResult(detector_name=_METADATA.name, matches=[match], generated_signals=new_signals)
```

**PatternMatch label format:** `"Leadership[{verdict}]: ratio={ratio:.2f}, dims={dim_count}"`

**LOC limits:** Main detector <= 150. Analyzer <= 120. Scorer <= 60. Factory <= 80.

#### 20.2.8 — New EvidenceTypes (M2-7F)

```python
# --- M2-7F (Leadership) ---
LEADERSHIP_STRONG   = "LEADERSHIP_STRONG"    # strong multi-dimension leadership signals
LEADERSHIP_EMERGING = "LEADERSHIP_EMERGING"  # early leadership pattern detected
LEADERSHIP_ABSENT   = "LEADERSHIP_ABSENT"    # behavioral data present but no leadership signals
```

#### 20.2.9 — Future Observation Mapping

| V1.1 | V1.2 |
|---|---|
| `LeadershipStats` dataclass | `LeadershipObservation(Observation)` |
| `stats.leadership_ratio` | `observation.value` |
| — | `observation.description` (human-readable summary for CoachingEngine) |
| — | `observation.observation_type = ObservationType.LEADERSHIP` |

#### 20.2.10 — Future ProfileFeature Mapping

| Field | Value |
|---|---|
| **Feature name** | `LeadershipFeature` |
| **Key in CandidateProfile.features** | `"leadership"` |
| **Value** | Normalized leadership score `[0.0, 1.0]` derived from `leadership_ratio` |
| **Confidence** | Grows with `total_behavioral_signals` |
| **Writer** | `CandidateProfileEngine` (V1.2 `ProfileFeatureUpdater`) |
| **Consumers** | `NarrativeGenerator`, `ReportBuilder`, `CoachingEngine` |
| **Update strategy** | EMA: `value = 0.3 * new_ratio + 0.7 * existing_value` |

#### 20.2.11 — Acceptance Criteria

- [ ] Fires only when `total_behavioral_signals >= 3`
- [ ] STRONG_LEADER requires `leadership_ratio >= 0.60` AND `dim_count >= 2`
- [ ] EMERGING_LEADER requires `leadership_ratio >= 0.35` AND `dim_count >= 1`
- [ ] NEUTRAL returns empty `DetectorResult` with no signals
- [ ] LEADERSHIP_ABSENT emits one negative signal at strength `0.4`
- [ ] Never emits signals about technical correctness
- [ ] Idempotency guard prevents signal re-emission
- [ ] Deterministic: same input → same output
- [ ] Performance: <= 20ms on 5-question, 20-signal input
- [ ] >= 39 tests (8+8+8+15 minimum)

---

### §20.3 — DET-12: CollaborationDetector (Full Specification)

#### 20.3.1 — Identity

| Field | Value |
|---|---|
| **Class name** | `CollaborationDetector` |
| **Priority** | 110 |
| **Tier** | Behavioral (V1.2) |
| **Milestone** | V1.2 |
| **Dependencies** | `LeadershipDetector` |
| **Version** | `1.0.0` |
| **Performance budget** | < 5ms soft / 20ms hard |
| **Complexity** | O(n) over EvidenceStore signals |

#### 20.3.2 — Purpose and Scope

Evaluate **collaborative behavior** emerging through interview responses. Collaboration signals
are identified by how the candidate describes working with others, sharing knowledge, accepting
feedback, and navigating conflict — never by technical knowledge or grammar quality.

**Signals within scope:**

| Signal concept | Definition |
|---|---|
| Team orientation | Candidate consistently frames problems and solutions in terms of team outcomes, not individual credit |
| Conflict management | Candidate describes navigating disagreements constructively; does not avoid or escalate conflict |
| Knowledge sharing | Candidate references proactively teaching, documenting, or enabling others |
| Feedback acceptance | Candidate describes incorporating feedback without defensiveness |
| Cross-functional collaboration | Candidate references working effectively across roles (PM, design, ops, etc.) |
| Stakeholder awareness | Candidate demonstrates awareness of stakeholder needs and perspectives in decisions |
| Pair-programming attitude | Candidate describes collaborative coding, code review culture, shared ownership |

**Explicitly outside scope (never evaluate):**

- Technical knowledge on any domain
- Grammar or language quality (owned by `CommunicationDetector`)
- Reasoning structure or depth (owned by `ReasoningDepthDetector`)
- Engineering judgment on technical decisions (owned by `EngineeringJudgmentDetector`)
- Leadership behaviors (owned by `LeadershipDetector`)

#### 20.3.3 — Input Contract

| Source | Field | Usage |
|---|---|---|
| `ReasonerInput.interview_memory.evidence_store` | Behavioral signals | Primary |
| `ReasonerInput.interview_memory.reasoning_history` | Pattern continuity | Trend detection |
| `ReasonerInput.interview_memory.candidate_profile.dimension_scores` | `COMMUNICATION` DimensionTrace | Baseline anchoring |

Input signals consumed: `BEHAVIORAL_GROWTH`, `BEHAVIORAL_INSTABILITY`, `CROSS_AREA_CONSISTENT`,
`CROSS_AREA_CONTRADICTORY`, `LEADERSHIP_EMERGING`, `LEADERSHIP_STRONG` (from DET-11, read-only).

**Note on DET-11 dependency:** `CollaborationDetector` MAY read `LEADERSHIP_*` signals to
distinguish collaborative leadership from solo leadership. It MUST NOT overwrite or re-score
any leadership signal.

#### 20.3.4 — Analyzer: `CollaborationAnalyzer`

**Output dataclass:**

```
@dataclass(frozen=True)
class CollaborationStats:
    team_orientation_count: int       # signals showing team-first framing
    knowledge_sharing_count: int      # signals showing teaching/enabling others
    conflict_signals_count: int       # signals (positive=managed well, negative=avoided/escalated)
    feedback_acceptance_count: int    # signals showing feedback incorporation
    cross_functional_count: int       # signals referencing cross-role collaboration
    total_behavioral_signals: int     # denominator
    collaboration_ratio: float        # weighted: (team + sharing + feedback) / total
    conflict_resolution_ratio: float  # positive_conflict / total_conflict (1.0 if no conflicts)
    trend: str                        # "RISING" | "STABLE" | "DECLINING" | "INSUFFICIENT"
```

**Guard condition:** Analyzer returns zeroed stats if `total_behavioral_signals < 2`.

**V1.2 migration:** `CollaborationStats` → `CollaborationObservation(Observation)`.

#### 20.3.5 — Scorer: `CollaborationScorer`

```python
class CollaborationVerdict(str, Enum):
    STRONG_COLLABORATOR    = "STRONG_COLLABORATOR"    # ratio >= 0.55 and conflict_resolution >= 0.6
    EFFECTIVE_COLLABORATOR = "EFFECTIVE_COLLABORATOR" # ratio >= 0.30 or cross_functional >= 2
    NEUTRAL                = "NEUTRAL"                # insufficient evidence
    COLLABORATION_DEFICIT  = "COLLABORATION_DEFICIT"  # individualistic pattern detected
```

**Threshold constants:**

```python
MIN_BEHAVIORAL_SIGNALS         = 3
MIN_COLLAB_RATIO_STRONG        = 0.55
MIN_COLLAB_RATIO_EFFECTIVE     = 0.30
MIN_CONFLICT_RESOLUTION_STRONG = 0.60
MIN_CROSS_FUNCTIONAL_EFFECTIVE = 2
```

**Guard:** Returns `NEUTRAL` if `total_behavioral_signals < MIN_BEHAVIORAL_SIGNALS`.

**Verdict precedence:** STRONG_COLLABORATOR > EFFECTIVE_COLLABORATOR > COLLABORATION_DEFICIT > NEUTRAL.

#### 20.3.6 — SignalFactory: `CollaborationSignalFactory`

| Verdict | EvidenceType | Polarity | Strength |
|---|---|---|---|
| `STRONG_COLLABORATOR` | `COLLABORATION_STRONG` | POSITIVE | `min(1.0, collaboration_ratio * 1.6)` |
| `EFFECTIVE_COLLABORATOR` | `COLLABORATION_EFFECTIVE` | POSITIVE | `collaboration_ratio` |
| `COLLABORATION_DEFICIT` | `COLLABORATION_DEFICIT` | NEGATIVE | `0.45` (fixed) |
| `NEUTRAL` | — | — | `None` |

**Signal dimension:** `ProfileDimension.COMMUNICATION` (temporary V1.1 mapping; see ADR-064).

#### 20.3.7 — New EvidenceTypes (M2-7F)

```python
# --- M2-7F (Collaboration) ---
COLLABORATION_STRONG    = "COLLABORATION_STRONG"    # strong multi-faceted collaboration pattern
COLLABORATION_EFFECTIVE = "COLLABORATION_EFFECTIVE" # solid collaboration indicators present
COLLABORATION_DEFICIT   = "COLLABORATION_DEFICIT"   # individualistic or conflict-avoidant pattern
```

#### 20.3.8 — Future Observation Mapping

| V1.1 | V1.2 |
|---|---|
| `CollaborationStats` dataclass | `CollaborationObservation(Observation)` |
| `stats.collaboration_ratio` | `observation.value` |
| — | `observation.description` |
| — | `observation.observation_type = ObservationType.COLLABORATION` |

#### 20.3.9 — Future ProfileFeature Mapping

| Field | Value |
|---|---|
| **Feature name** | `CollaborationFeature` |
| **Key in CandidateProfile.features** | `"collaboration"` |
| **Value** | Normalized `[0.0, 1.0]` from `collaboration_ratio` |
| **Confidence** | Grows with `total_behavioral_signals` |
| **Writer** | `CandidateProfileEngine` (V1.2 `ProfileFeatureUpdater`) |
| **Consumers** | `ReportBuilder`, `CoachingEngine` |
| **Update strategy** | EMA with alpha=0.3 |

#### 20.3.10 — Acceptance Criteria

- [ ] Fires only when `total_behavioral_signals >= 3`
- [ ] STRONG_COLLABORATOR requires both `collaboration_ratio >= 0.55` AND `conflict_resolution_ratio >= 0.60`
- [ ] EFFECTIVE_COLLABORATOR requires `ratio >= 0.30` OR `cross_functional_count >= 2`
- [ ] COLLABORATION_DEFICIT emits a negative signal (strength `0.45`)
- [ ] NEUTRAL returns empty result
- [ ] Never evaluates grammar, technical knowledge, or reasoning depth
- [ ] Does not overwrite any `LEADERSHIP_*` signal
- [ ] Idempotency guard in place
- [ ] Deterministic
- [ ] Performance <= 20ms
- [ ] >= 39 tests

---

### §20.4 — DET-13: AdaptabilityDetector (Full Specification)

#### 20.4.1 — Identity

| Field | Value |
|---|---|
| **Class name** | `AdaptabilityDetector` |
| **Priority** | 120 |
| **Tier** | Behavioral (V1.2) |
| **Milestone** | V1.2 |
| **Dependencies** | `CollaborationDetector` |
| **Version** | `1.0.0` |
| **Performance budget** | < 5ms soft / 20ms hard |
| **Complexity** | O(n) over EvidenceStore signals |

#### 20.4.2 — Purpose and Scope

Detect **adaptability** demonstrated during the interview — the candidate's ability to respond
constructively to novel situations, feedback, mistakes, and changing contexts.

**Signals within scope:**

| Signal concept | Definition |
|---|---|
| Reaction to feedback | Candidate incorporates or meaningfully engages with interviewer cues and pivots |
| Recovery after mistakes | After an incorrect path or `BEHAVIORAL_INSTABILITY` signal, candidate course-corrects |
| Learning speed | Candidate demonstrates rapid uptake of new constraints or revised problem framing |
| Flexibility | Candidate shifts approach when initial solution proves insufficient |
| Change acceptance | Candidate describes embracing change rather than resisting it |
| Context switching | Candidate moves fluidly across different domains or question types |
| Problem reframing | Candidate redefines a problem when the initial framing is unproductive |

**Explicitly outside scope (never evaluate):**

- Whether the adapted answer is technically correct (evaluation pipeline scope)
- Domain knowledge depth (evaluation pipeline scope)
- Communication style (owned by `CommunicationDetector`)
- Leadership behaviors (owned by `LeadershipDetector`)
- Collaboration quality (owned by `CollaborationDetector`)

#### 20.4.3 — Input Contract

| Source | Field | Usage |
|---|---|---|
| `ReasonerInput.interview_memory.evidence_store` | Behavioral signals (especially recovery patterns) | Primary |
| `ReasonerInput.interview_memory.reasoning_history` | Cross-cycle patterns | Recovery trend |
| `ReasonerInput.interview_memory.candidate_profile.dimension_scores` | `PROBLEM_SOLVING` DimensionTrace | Trend baseline |

**Key signal patterns consumed:**

- `BEHAVIORAL_INSTABILITY` followed by `BEHAVIORAL_GROWTH` → recovery indicator (positive adaptability)
- `BEHAVIORAL_INSTABILITY` with no follow-up growth → rigidity indicator (negative adaptability)
- `CROSS_AREA_CONSISTENT` with rising trend across distinct areas → flexibility indicator
- `CROSS_AREA_CONTRADICTORY` → may indicate poor context switching OR reframing (context-dependent)

#### 20.4.4 — Analyzer: `AdaptabilityAnalyzer`

**Output dataclass:**

```
@dataclass(frozen=True)
class AdaptabilityStats:
    recovery_count: int           # INSTABILITY -> GROWTH sequences detected (window: 3 questions)
    rigidity_count: int           # INSTABILITY with no recovery within next 3 cycles
    flexibility_count: int        # CROSS_AREA_CONSISTENT with rising trend
    context_switch_count: int     # distinct area transitions with consistent performance
    reframing_events: int         # CROSS_AREA_CONTRADICTORY resolved positively
    total_instability_events: int
    adaptability_ratio: float     # recovery_count / max(1, total_instability_events)
    flexibility_ratio: float      # flexibility_count / max(1, distinct_areas_count)
    trend: str                    # "IMPROVING" | "STABLE" | "DECLINING" | "INSUFFICIENT"
```

**Recovery detection rule (ADR-065):** An INSTABILITY event at question index `i` is "recovered"
if a BEHAVIORAL_GROWTH signal appears within questions `i+1` to `i+3` in the same or adjacent
dimension. Window size `RECOVERY_WINDOW_QUESTIONS = 3` is a module-level constant.

**Guard condition:** Analyzer returns zeroed stats if `total_behavioral_signals < 2`.

**V1.2 migration:** `AdaptabilityStats` → `AdaptabilityObservation(Observation)`.

#### 20.4.5 — Scorer: `AdaptabilityScorer`

```python
class AdaptabilityVerdict(str, Enum):
    HIGHLY_ADAPTABLE = "HIGHLY_ADAPTABLE"  # adaptability_ratio >= 0.7 and trend != DECLINING
    ADAPTABLE        = "ADAPTABLE"         # ratio >= 0.4 or flexibility_ratio >= 0.5
    NEUTRAL          = "NEUTRAL"           # insufficient data
    LOW_ADAPTABILITY = "LOW_ADAPTABILITY"  # rigidity_count > recovery_count and rigidity >= 2
```

**Threshold constants:**

```python
MIN_INSTABILITY_EVENTS           = 2
RECOVERY_WINDOW_QUESTIONS        = 3     # also used by Analyzer (same constant, imported)
MIN_ADAPTABILITY_RATIO_HIGH      = 0.70
MIN_ADAPTABILITY_RATIO_ADAPTABLE = 0.40
MIN_FLEXIBILITY_RATIO_ADAPTABLE  = 0.50
LOW_ADAPTABILITY_RIGIDITY_FLOOR  = 2
```

**Special rule:** If `total_instability_events == 0` but `flexibility_count >= 3`, verdict is
`ADAPTABLE` (proactive flexibility without instability is a positive signal).

**Guard:** Returns `NEUTRAL` if `total_instability_events < MIN_INSTABILITY_EVENTS AND flexibility_count < 3`.

**Verdict precedence:** HIGHLY_ADAPTABLE > ADAPTABLE > LOW_ADAPTABILITY > NEUTRAL.

#### 20.4.6 — SignalFactory: `AdaptabilitySignalFactory`

| Verdict | EvidenceType | Polarity | Strength |
|---|---|---|---|
| `HIGHLY_ADAPTABLE` | `ADAPTABILITY_HIGH` | POSITIVE | `min(1.0, adaptability_ratio * 1.3)` |
| `ADAPTABLE` | `ADAPTABILITY_MODERATE` | POSITIVE | `max(adaptability_ratio, flexibility_ratio)` |
| `LOW_ADAPTABILITY` | `ADAPTABILITY_LOW` | NEGATIVE | `min(1.0, rigidity_count / 5.0)` |
| `NEUTRAL` | — | — | `None` |

**Signal dimension:** `ProfileDimension.PROBLEM_SOLVING` (temporary V1.1 mapping).

#### 20.4.7 — New EvidenceTypes (M2-7F)

```python
# --- M2-7F (Adaptability) ---
ADAPTABILITY_HIGH     = "ADAPTABILITY_HIGH"     # strong recovery and flexibility demonstrated
ADAPTABILITY_MODERATE = "ADAPTABILITY_MODERATE" # adequate adaptability present
ADAPTABILITY_LOW      = "ADAPTABILITY_LOW"      # rigidity pattern; low recovery rate
```

#### 20.4.8 — Future Observation Mapping

| V1.1 | V1.2 |
|---|---|
| `AdaptabilityStats` dataclass | `AdaptabilityObservation(Observation)` |
| `stats.adaptability_ratio` | `observation.value` |
| — | `observation.description` |
| — | `observation.observation_type = ObservationType.ADAPTABILITY` |

#### 20.4.9 — Future ProfileFeature Mapping

| Field | Value |
|---|---|
| **Feature name** | `AdaptabilityFeature` |
| **Key in CandidateProfile.features** | `"adaptability"` |
| **Value** | Normalized `[0.0, 1.0]` from `max(adaptability_ratio, flexibility_ratio)` |
| **Confidence** | Grows with `total_instability_events + flexibility_count` |
| **Writer** | `CandidateProfileEngine` (V1.2 `ProfileFeatureUpdater`) |
| **Consumers** | `NarrativeGenerator`, `CoachingEngine` |
| **Update strategy** | EMA with alpha=0.3 |

#### 20.4.10 — Acceptance Criteria

- [ ] Requires `total_instability_events >= 2` OR `flexibility_count >= 3` to score
- [ ] HIGHLY_ADAPTABLE requires `adaptability_ratio >= 0.70` AND `trend != DECLINING`
- [ ] ADAPTABLE requires `ratio >= 0.40` OR `flexibility_ratio >= 0.50`
- [ ] Low adaptability requires `rigidity_count > recovery_count AND rigidity_count >= 2`
- [ ] Recovery detection: INSTABILITY -> GROWTH within 3 questions in adjacent dimension (ADR-065)
- [ ] Zero instability + flexibility >= 3 → ADAPTABLE (proactive path)
- [ ] Never evaluates technical correctness
- [ ] Idempotency guard in place
- [ ] Deterministic
- [ ] Performance <= 20ms
- [ ] >= 39 tests

---

### §20.5 — Complete Behavioral Detector Family Freeze

#### 20.5.1 — Responsibility Matrix (Final)

| Behavioral Signal | Detector | ProfileFeature | Notes |
|---|---|---|---|
| Session growth over time | `BehavioralPatternDetector` (70) | `BehavioralPatternFeature` | V1.1 |
| Cross-domain consistency | `ConsistencyAcrossInterviewDetector` (80) | `CrossDomainConsistencyFeature` | V1.1 |
| Ownership & accountability | `LeadershipDetector` (100) | `LeadershipFeature` | V1.2 |
| Decision responsibility | `LeadershipDetector` (100) | `LeadershipFeature` | V1.2 |
| Initiative & proactivity | `LeadershipDetector` (100) | `LeadershipFeature` | V1.2 |
| Mentoring attitude | `LeadershipDetector` (100) | `LeadershipFeature` | V1.2 |
| Strategic thinking | `LeadershipDetector` (100) | `LeadershipFeature` | V1.2 |
| Team orientation | `CollaborationDetector` (110) | `CollaborationFeature` | V1.2 |
| Conflict management | `CollaborationDetector` (110) | `CollaborationFeature` | V1.2 |
| Knowledge sharing | `CollaborationDetector` (110) | `CollaborationFeature` | V1.2 |
| Feedback acceptance | `CollaborationDetector` (110) | `CollaborationFeature` | V1.2 |
| Cross-functional work | `CollaborationDetector` (110) | `CollaborationFeature` | V1.2 |
| Stakeholder awareness | `CollaborationDetector` (110) | `CollaborationFeature` | V1.2 |
| Recovery after mistakes | `AdaptabilityDetector` (120) | `AdaptabilityFeature` | V1.2 |
| Flexibility under pressure | `AdaptabilityDetector` (120) | `AdaptabilityFeature` | V1.2 |
| Learning speed | `AdaptabilityDetector` (120) | `AdaptabilityFeature` | V1.2 |
| Problem reframing | `AdaptabilityDetector` (120) | `AdaptabilityFeature` | V1.2 |
| Context switching | `AdaptabilityDetector` (120) | `AdaptabilityFeature` | V1.2 |
| Change acceptance | `AdaptabilityDetector` (120) | `AdaptabilityFeature` | V1.2 |

#### 20.5.2 — Forbidden Signal Overlap Contracts

The following assignments are binding and enforced at code review:

```
Technical correctness → evaluation pipeline ONLY
Grammar / fluency     → CommunicationDetector ONLY
Reasoning depth       → ReasoningDepthDetector ONLY
Engineering judgment  → EngineeringJudgmentDetector ONLY
Leadership signals    → LeadershipDetector ONLY
Collaboration signals → CollaborationDetector ONLY
Adaptability signals  → AdaptabilityDetector ONLY
Growth/instability    → BehavioralPatternDetector ONLY (produces; others READ)
Cross-area consistency → ConsistencyAcrossInterviewDetector ONLY (produces; others READ)
```

#### 20.5.3 — Shared Behavioral Concepts (Read-only across detectors)

`BEHAVIORAL_GROWTH` and `BEHAVIORAL_INSTABILITY` are **produced only by `BehavioralPatternDetector`**.
`LeadershipDetector`, `CollaborationDetector`, and `AdaptabilityDetector` **read** these signals
as their primary input but MUST NOT produce them.

`CROSS_AREA_CONSISTENT` and `CROSS_AREA_CONTRADICTORY` are **produced only by
`ConsistencyAcrossInterviewDetector`**. All downstream behavioral detectors read these signals
as context. No detector may re-produce them.

#### 20.5.4 — Dependency Chain (Behavioral Tier, Complete)

```
BehavioralPatternDetector (70)
        ↓ produces BEHAVIORAL_GROWTH, BEHAVIORAL_INSTABILITY
ConsistencyAcrossInterviewDetector (80)
        ↓ produces CROSS_AREA_CONSISTENT, CROSS_AREA_CONTRADICTORY
[Both above read-accessible by downstream detectors]
LeadershipDetector (100)
        ↓ produces LEADERSHIP_STRONG, LEADERSHIP_EMERGING, LEADERSHIP_ABSENT
CollaborationDetector (110)    [reads LEADERSHIP_* for context; does not own them]
        ↓ produces COLLABORATION_STRONG, COLLABORATION_EFFECTIVE, COLLABORATION_DEFICIT
AdaptabilityDetector (120)     [reads all above for context; does not own them]
        ↓ produces ADAPTABILITY_HIGH, ADAPTABILITY_MODERATE, ADAPTABILITY_LOW
```

All edges are downward. No upward dependency permitted. Enforced by `PatternDetectorRegistry`
cycle-check and DDS §19.2.

#### 20.5.5 — Complete EvidenceType Catalog (Post-M2-7F Design Freeze)

```
Original (12):        REPEATED_STRENGTH, RECOVERED_WEAKNESS, DEMONSTRATED_DEPTH,
                      ENGINEERING_JUDGMENT_ARTICULATED, REPEATED_WEAKNESS, KNOWLEDGE_GAP,
                      COMMUNICATION_GAP, REASONING_GAP, CONFIDENCE_DROP, MISSING_EVIDENCE,
                      SHALLOW_ANSWER, CONTRADICTORY_ANSWER

M2-7B (4):            REASONING_DEPTH_HIGH, REASONING_DEPTH_LOW,
                      REASONING_IMPROVING, REASONING_STAGNATING

M2-7C (5):            ENGINEERING_JUDGMENT_HIGH, ENGINEERING_JUDGMENT_LOW,
                      COMMUNICATION_CLEAR, COMMUNICATION_WEAK, COMMUNICATION_INCONSISTENT

M2-7D (5):            BEHAVIORAL_GROWTH, BEHAVIORAL_INSTABILITY, BEHAVIORAL_PLATEAU,
                      CROSS_AREA_CONSISTENT, CROSS_AREA_CONTRADICTORY

M2-7F Leadership (3): LEADERSHIP_STRONG, LEADERSHIP_EMERGING, LEADERSHIP_ABSENT

M2-7F Collaboration (3): COLLABORATION_STRONG, COLLABORATION_EFFECTIVE, COLLABORATION_DEFICIT

M2-7F Adaptability (3): ADAPTABILITY_HIGH, ADAPTABILITY_MODERATE, ADAPTABILITY_LOW

Total post-M2-7F: 35
```

---

### §20.6 — Future Observation Layer Architecture (V1.2)

> No production code is defined here. This section freezes the Observation Layer design so that
> V1.2 implementation requires no architectural decisions.

#### 20.6.1 — New Observation Subtypes

The `Observation` base class (ADR-055) will be extended in V1.2 with three new subclasses:

```
Observation (base — domain/contracts/reasoning/observation.py)
├── observation_type: ObservationType
├── dimension: ProfileDimension | None
├── value: float | None         # normalized [0.0, 1.0]
├── strength: float
├── description: str            # short, non-candidate-facing explanation
└── supporting_signal_ids: list[str]

LeadershipObservation(Observation)
├── leadership_dimensions_detected: list[str]
├── ownership_signal_count: int
├── initiative_signal_count: int
├── accountability_signal_count: int
└── leadership_ratio: float

CollaborationObservation(Observation)
├── team_orientation_count: int
├── conflict_resolution_ratio: float
├── cross_functional_count: int
└── collaboration_ratio: float

AdaptabilityObservation(Observation)
├── recovery_count: int
├── rigidity_count: int
├── adaptability_ratio: float
└── flexibility_ratio: float
```

**ObservationType enum additions (V1.2):**

```python
class ObservationType(str, Enum):
    # ... existing values ...
    LEADERSHIP    = "LEADERSHIP"
    COLLABORATION = "COLLABORATION"
    ADAPTABILITY  = "ADAPTABILITY"
```

#### 20.6.2 — Observation Lifecycle

```
Analyzer.analyze(reasoner_input) → stats: *Stats (V1.1) | *Observation (V1.2)
        ↓
Scorer.score(stats) → verdict: *Verdict
        ↓
SignalFactory.create(verdict, stats, reasoner_input) → EvidenceSignal | None
        ↓                                ↓
  EvidenceStore                    Observation (V1.2 only)
        ↓                                ↓
  PatternMatch                    CoachingEngine (V1.2)
        ↓
  DetectorResult → ReasonerDecision → NarrativeGenerator / ReportBuilder
```

#### 20.6.3 — Observation Ownership Rules

| Rule | Detail |
|---|---|
| Single producer | Each Observation type produced by exactly one detector |
| Read-only for consumers | NarrativeGenerator, CoachingEngine read; never write |
| Immutable | All Observation subclasses are frozen dataclasses |
| Non-candidate-facing | `description` field is internal; never shown to candidate |
| Lifecycle scope | Observation is transient per detection cycle; persisted only as `EvidenceSignal` |

#### 20.6.4 — Relationship Diagram

```
EvidenceSignal  ← atomic unit; persisted in EvidenceStore; polarity, strength, type
PatternMatch    ← aggregation of EvidenceSignals; in ReasonerDecision.reasoning_basis
Observation     ← richer intermediate: captures WHY a signal was emitted
ProfileFeature  ← derived characteristic; persisted in CandidateProfile; incremental
NarrativeGenerator ← reads ProfileFeatures only; never reads Observations directly
CoachingEngine  ← reads Observations (for why) + ProfileFeatures (for current state)
```

---

### §20.7 — Future ProfileFeatures (V1.2 Design Freeze)

> Frozen for V1.2 planning. No production code changes.

#### 20.7.1 — LeadershipFeature

| Attribute | Value |
|---|---|
| **Key** | `"leadership"` |
| **Value type** | `float | None` in `[0.0, 1.0]` |
| **Inputs** | `LEADERSHIP_STRONG`, `LEADERSHIP_EMERGING`, `LEADERSHIP_ABSENT` signals |
| **Owner (writer)** | `CandidateProfileEngine` via `LeadershipProfileFeatureUpdater` |
| **Consumers** | `NarrativeGenerator` (leadership coaching text), `ReportBuilder` (leadership section), `CoachingEngine` (leadership roadmap) |
| **Update strategy** | EMA: `value = 0.3 * new_ratio + 0.7 * existing_value` |
| **Confidence** | `min(1.0, evidence_count / 10)` |
| **Future coaching** | Leadership development, managerial readiness |

#### 20.7.2 — CollaborationFeature

| Attribute | Value |
|---|---|
| **Key** | `"collaboration"` |
| **Value type** | `float | None` in `[0.0, 1.0]` |
| **Inputs** | `COLLABORATION_STRONG`, `COLLABORATION_EFFECTIVE`, `COLLABORATION_DEFICIT` signals |
| **Owner (writer)** | `CandidateProfileEngine` via `CollaborationProfileFeatureUpdater` |
| **Consumers** | `ReportBuilder` (team fit section), `CoachingEngine` (collaboration coaching) |
| **Update strategy** | EMA with alpha=0.3 |
| **Confidence** | `min(1.0, evidence_count / 8)` |
| **Future coaching** | Team dynamics, conflict resolution, feedback skills |

#### 20.7.3 — AdaptabilityFeature

| Attribute | Value |
|---|---|
| **Key** | `"adaptability"` |
| **Value type** | `float | None` in `[0.0, 1.0]` |
| **Inputs** | `ADAPTABILITY_HIGH`, `ADAPTABILITY_MODERATE`, `ADAPTABILITY_LOW` signals |
| **Owner (writer)** | `CandidateProfileEngine` via `AdaptabilityProfileFeatureUpdater` |
| **Consumers** | `NarrativeGenerator` (resilience coaching), `CoachingEngine` (adaptability roadmap) |
| **Update strategy** | EMA with alpha=0.3 |
| **Confidence** | `min(1.0, (recovery_count + flexibility_count) / 8)` |
| **Future coaching** | Learning agility, change readiness |

#### 20.7.4 — V1.2 ProfileFeature Catalog (Complete)

| Feature key | Feature class | Source detector | V1.2 writer |
|---|---|---|---|
| `"reasoning_depth"` | `ReasoningDepthFeature` | `ReasoningDepthDetector` | `CandidateProfileEngine` |
| `"engineering_judgment"` | `EngineeringJudgmentFeature` | `EngineeringJudgmentDetector` | `CandidateProfileEngine` |
| `"communication"` | `CommunicationFeature` | `CommunicationDetector` | `CandidateProfileEngine` |
| `"behavioral_pattern"` | `BehavioralPatternFeature` | `BehavioralPatternDetector` | `CandidateProfileEngine` |
| `"cross_domain_consistency"` | `CrossDomainConsistencyFeature` | `ConsistencyAcrossInterviewDetector` | `CandidateProfileEngine` |
| `"confidence_calibration"` | `ConfidenceCalibrationFeature` | `ConfidenceCalibrationDetector` | `CandidateProfileEngine` |
| `"leadership"` | `LeadershipFeature` | `LeadershipDetector` | `CandidateProfileEngine` |
| `"collaboration"` | `CollaborationFeature` | `CollaborationDetector` | `CandidateProfileEngine` |
| `"adaptability"` | `AdaptabilityFeature` | `AdaptabilityDetector` | `CandidateProfileEngine` |

---

### §20.8 — Future Coaching Engine Integration (V1.2)

> Architecture only. No production code. No coupling to existing components.

#### 20.8.1 — CoachingEngine Purpose

The `CoachingEngine` (V1.2) produces **actionable improvement recommendations** for the candidate
based on their `ProfileFeatures` and the `Observations` produced during the session. It is
deliberately decoupled from both detectors and `NarrativeGenerator`.

#### 20.8.2 — Decoupling Architecture

```
PatternDetector → EvidenceSignal + Observation
                        ↓
         CandidateProfileEngine → ProfileFeature
                        ↓
┌───────────────────────────────────────────────────┐
│              CoachingEngine (V1.2)                │
│  Input: CandidateProfile.features                 │
│  Input: Session Observations (from Analyzers)     │
│  Output: CoachingPlan (list[CoachingRecommendation])│
└───────────────────────────────────────────────────┘
                        ↓
         NarrativeGenerator (M2-8) reads CoachingPlan
         ReportBuilder (M2-9) reads CoachingPlan
```

**Critical constraint:** `NarrativeGenerator` does NOT call `CoachingEngine`. Both consume
`CandidateProfile` independently. `CoachingEngine` outputs are separate artifacts read by
report and UI layers without coupling to narrative text generation.

#### 20.8.3 — Coaching Domains Enabled by the Three New Features

| Feature(s) | Coaching domain | Coaching output |
|---|---|---|
| `LeadershipFeature` | Leadership coaching | Leadership development recommendations |
| `LeadershipFeature` | Managerial readiness | Management track readiness assessment |
| `CollaborationFeature` | Collaboration coaching | Team dynamics, feedback, conflict resolution |
| `AdaptabilityFeature` | Adaptability coaching | Learning agility, change readiness |
| `LeadershipFeature` + `CollaborationFeature` | Managerial communication coaching | How to communicate decisions to teams |
| `CollaborationFeature` + `AdaptabilityFeature` | Team resilience coaching | Managing team ambiguity |

#### 20.8.4 — CoachingRecommendation Contract (V1.2 Reserved)

```
CoachingRecommendation (V1.2, not yet implemented)
├── coaching_type: CoachingType       # LEADERSHIP | COLLABORATION | ADAPTABILITY | ...
├── priority: int                     # 1 (high) to 3 (low)
├── evidence_features: list[str]      # feature keys that triggered this recommendation
├── recommendation_text: str          # coaching content
├── action_items: list[str]           # concrete steps
└── confidence: float                 # [0.0, 1.0]
```

**Decoupling guarantee:** Detectors NEVER produce `CoachingRecommendation` directly.
Chain: `Detector → EvidenceSignal → ProfileFeature → CoachingEngine → Recommendation`.
No detector-specific code exists in `CoachingEngine`.

#### 20.8.5 — NarrativeGenerator Boundary (ADR-050 Preserved)

`NarrativeGenerator` (M2-8) continues to consume only `CandidateProfile.features` and NEVER
directly accesses `DetectorResult`, `PatternMatch`, `Observation`, or `CoachingRecommendation`.
This boundary is enforced by ADR-050 and is not altered by the addition of the three new features.

---

### §20.9 — New ADRs (M2-7F)

---

#### ADR-062: Behavioral Detector Family — Responsibility Matrix

**Status: Accepted — M2-7F Design Freeze**

**Context:** With the design of `LeadershipDetector`, `CollaborationDetector`, and
`AdaptabilityDetector`, the behavioral tier is complete. Without a formal responsibility
boundary, signal assignment ambiguity risks duplicate detection.

**Decision:** The responsibility matrix in §20.5.1 is the binding ownership contract for all
behavioral signals. Each signal category is owned by exactly one detector. Signal assignment
cannot be changed without a new ADR.

**Enforcement:** Code review gate. Any detector producing a signal type outside its ownership
scope fails the DDS checklist (§19.11).

**Consequences:** `CommunicationDetector` owns grammar/fluency signals only. `CollaborationDetector`
owns all team-interaction signals. `LeadershipDetector` owns all ownership/accountability signals.
`AdaptabilityDetector` owns all recovery/flexibility signals.

---

#### ADR-063: LeadershipFeature — Dimension Anchor and Update Strategy

**Status: Accepted — M2-7F Design Freeze**

**Context:** No `LEADERSHIP` dimension exists in the V1.1 `ProfileDimension` enum. A temporary
dimension anchor is needed for V1.1 signal emission.

**Decision:**
1. In V1.1: `LeadershipDetector` signals use `ProfileDimension.PROBLEM_SOLVING` as the closest
   behavioral proxy. This temporary mapping is declared in the module docstring.
2. In V1.2: `ProfileDimension.LEADERSHIP` is added. A migration script re-maps existing signals.
3. `LeadershipFeature` uses EMA with alpha=0.3.
4. Single writer: `CandidateProfileEngine` via `LeadershipProfileFeatureUpdater`.

**Constraints:** No V1.1 code references `ProfileDimension.LEADERSHIP`.

---

#### ADR-064: CollaborationFeature — Dimension Anchor

**Status: Accepted — M2-7F Design Freeze**

**Context:** No `COLLABORATION` dimension exists in V1.1. Collaboration overlaps with both
`COMMUNICATION` and `PROBLEM_SOLVING` dimensions.

**Decision:**
1. In V1.1: `CollaborationDetector` signals use `ProfileDimension.COMMUNICATION` as anchor.
   Collaboration is fundamentally interpersonal communication in interview context.
2. In V1.2: `ProfileDimension.COLLABORATION` reserved for future addition if needed.
3. `CollaborationFeature` uses EMA with alpha=0.3.
4. Single writer: `CandidateProfileEngine` via `CollaborationProfileFeatureUpdater`.

---

#### ADR-065: AdaptabilityDetector — Recovery Detection Algorithm

**Status: Accepted — M2-7F Design Freeze**

**Context:** `AdaptabilityDetector` relies on detecting INSTABILITY→GROWTH sequences. The window
size and proximity rule must be frozen to ensure deterministic behavior across all future
implementations.

**Decision:**
1. Recovery window: INSTABILITY at index `i` is matched to GROWTH at index `j` where `j > i`
   and `j <= i + 3`.
2. Dimension proximity: growth signal must be in the same dimension OR an adjacent dimension
   (adjacent = sharing the same question area).
3. Unmatched INSTABILITY events after the window count as `rigidity_count`.
4. Algorithm is O(n) via single forward pass with sliding window queue.
5. `RECOVERY_WINDOW_QUESTIONS = 3` is a module-level constant.

**Constraints:** Idempotency guaranteed by algorithm structure; same input always produces
same output regardless of call count.

---

#### ADR-066: Behavioral Observation Model — V1.2 Extension Contract

**Status: Accepted — Architecture direction; implementation V1.2**

**Context:** ADR-055 reserved the `Observation` abstraction. Three new subtypes are now designed.
The V1.2 migration contract must be explicitly frozen.

**Decision:**
1. V1.1 Analyzers produce plain `@dataclass(frozen=True)` stat objects.
2. V1.2 migration: stat objects become `Observation` subclasses by adding `description: str`
   and inheriting from `Observation`. No existing fields are removed.
3. `ObservationType.LEADERSHIP`, `COLLABORATION`, `ADAPTABILITY` are added to the enum.
4. `PatternDetector` ABC contract does not change.

**Constraints:** V1.1 code MUST NOT import or reference `Observation` class.
The `description` field is reserved in V1.1 Analyzer docstrings with a V1.2 note.

---

#### ADR-067: Behavioral Coaching Pipeline — Detector-to-CoachingEngine Decoupling

**Status: Accepted — Architecture direction; CoachingEngine deferred to V1.2**

**Context:** With nine ProfileFeatures now designed (§20.7.4), it is critical to freeze the
data flow from detectors to the eventual CoachingEngine.

**Decision:** The coaching pipeline follows a strict chain:
```
Detector → EvidenceSignal → ProfileFeature → CoachingEngine → CoachingRecommendation
```
No detector may produce a `CoachingRecommendation`. No `CoachingEngine` code may import
any detector class or collaborator. The only interface between detectors and the coaching
layer is `CandidateProfile.features: dict[str, ProfileFeature]`.

**Constraints:**
- `CoachingEngine` is NOT implemented in V1.1.
- `CoachingRecommendation` is NOT implemented in V1.1.
- `CandidateProfile.features` remains absent in V1.1; added in V1.2 (ADR-048).
- `NarrativeGenerator` (M2-8) MUST NOT call `CoachingEngine` (ADR-050 boundary preserved).

---

### §20.10 — Updated Detector Catalog (Post-M2-7F Design Freeze)

| Priority | Detector | Milestone | Status | Layer |
|---|---|---|---|---|
| 5 | `EvaluationSignalDetector` | M2-7B | Active | Foundation |
| 10 | `CoverageDetector` | M2-3 | Active | Foundation |
| 20 | `ConsistencyDetector` | M2-3 | Active | Foundation |
| 30 | `TrendDetector` | M2-3 | Active | Foundation |
| 40 | `ReasoningDepthDetector` | M2-7B | Active | Analytical |
| 50 | `EngineeringJudgmentDetector` | M2-7C | Active | Analytical |
| 60 | `CommunicationDetector` | M2-7D | Active | Analytical |
| 70 | `BehavioralPatternDetector` | M2-7E | Active | Behavioral |
| 80 | `ConsistencyAcrossInterviewDetector` | M2-7F | Active | Behavioral |
| 90 | `ConfidenceCalibrationDetector` | M2-7G | Planned | Calibration |
| 100 | `LeadershipDetector` | V1.2 | **Design Frozen** | Behavioral |
| 110 | `CollaborationDetector` | V1.2 | **Design Frozen** | Behavioral |
| 120 | `AdaptabilityDetector` | V1.2 | **Design Frozen** | Behavioral |

---

### §20.11 — M2-7F Acceptance Checklist

| Item | Status |
|---|---|
| `LeadershipDetector` fully specified (§20.2) | Frozen |
| `CollaborationDetector` fully specified (§20.3) | Frozen |
| `AdaptabilityDetector` fully specified (§20.4) | Frozen |
| Behavioral detector family responsibility matrix (§20.5.1) | Frozen |
| Forbidden overlap contracts (§20.5.2) | Frozen |
| Shared behavioral concept ownership (§20.5.3) | Frozen |
| Complete EvidenceType catalog (§20.5.5, total 35) | Frozen |
| Observation Layer architecture (§20.6) | Frozen |
| V1.2 Observation migration contracts (§20.6.1) | Frozen |
| `LeadershipFeature` ProfileFeature design (§20.7.1) | Frozen |
| `CollaborationFeature` ProfileFeature design (§20.7.2) | Frozen |
| `AdaptabilityFeature` ProfileFeature design (§20.7.3) | Frozen |
| V1.2 ProfileFeature catalog complete (§20.7.4, total 9) | Frozen |
| CoachingEngine integration architecture (§20.8) | Frozen |
| Detector-to-CoachingEngine decoupling (ADR-067) | Frozen |
| ADR-062 (Responsibility Matrix) | Accepted |
| ADR-063 (LeadershipFeature dimension anchor) | Accepted |
| ADR-064 (CollaborationFeature dimension anchor) | Accepted |
| ADR-065 (AdaptabilityFeature recovery algorithm) | Accepted |
| ADR-066 (Observation Model extension contract) | Accepted |
| ADR-067 (Coaching Pipeline decoupling) | Accepted |
| DDS fully respected by all three detectors | Verified |
| Zero production code modified | Confirmed |
| Zero tests modified | Confirmed |

---

### §20.12 — Implementation Recommendation (V1.2)

The three detectors must be implemented in the following order to respect the dependency chain:

```
Step 1: LeadershipDetector (DET-11, priority 100)
  ├── Implement LeadershipAnalyzer, LeadershipScorer, LeadershipSignalFactory
  ├── Add EvidenceTypes: LEADERSHIP_STRONG, LEADERSHIP_EMERGING, LEADERSHIP_ABSENT
  ├── Register in build_default_registry() with dependency=ConsistencyAcrossInterviewDetector
  └── 39+ tests

Step 2: CollaborationDetector (DET-12, priority 110)
  ├── Implement CollaborationAnalyzer, CollaborationScorer, CollaborationSignalFactory
  ├── Add EvidenceTypes: COLLABORATION_STRONG, COLLABORATION_EFFECTIVE, COLLABORATION_DEFICIT
  ├── Register with dependency=LeadershipDetector
  └── 39+ tests

Step 3: AdaptabilityDetector (DET-13, priority 120)
  ├── Implement AdaptabilityAnalyzer (recovery algorithm per ADR-065)
  ├── Implement AdaptabilityScorer (including zero-instability / high-flexibility path)
  ├── Implement AdaptabilitySignalFactory
  ├── Add EvidenceTypes: ADAPTABILITY_HIGH, ADAPTABILITY_MODERATE, ADAPTABILITY_LOW
  ├── Register with dependency=CollaborationDetector
  └── 39+ tests

Step 4: ProfileFeatureUpdaters (CandidateProfileEngine extension)
  ├── LeadershipProfileFeatureUpdater
  ├── CollaborationProfileFeatureUpdater
  ├── AdaptabilityProfileFeatureUpdater
  └── Add CandidateProfile.features: dict[str, ProfileFeature] (backward-compatible, ADR-048)

Step 5: Observation Layer (V1.2 — after all detectors pass regression)
  ├── Promote *Stats to *Observation subclasses
  ├── Add ObservationType enum values (ADR-066)
  └── Wire CoachingEngine input pipeline (ADR-067)
```

Each step is independently deliverable and independently testable. No step requires changes to
V1.1 `ReasonerService`, `NarrativeGenerator`, `ReportBuilder`, or any existing detector.

---

