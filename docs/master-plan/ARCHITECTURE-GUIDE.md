# Architecture Guide

**Primary architectural reference for engineers joining the project.**

---

## 1. Overview

The platform conducts structured interview sessions, accumulates structured knowledge about a candidate's capabilities across those sessions, and produces an immutable, inspectable record of what was learned. It is not a question-and-answer system. It is a knowledge accumulation system that uses a question-and-answer session as its data source.

Three principles govern the entire architecture:

**Accumulate during the session.** Every observation, feature derivation, and reasoning decision is made incrementally, during the live interview cycle. Nothing is deferred to session end.

**Seal at closure.** When the session ends, all accumulated knowledge is assembled into a self-contained, immutable record. No new computation occurs at this stage.

**Project from the record.** Reports, exports, and UI representations are derived from the sealed record. They read. They do not compute.

These three principles — accumulate, seal, project — define the boundary between every major subsystem. Understanding them is the prerequisite for understanding every other architectural decision in the platform.

### Major Subsystems

| Subsystem | Responsibility |
|-----------|----------------|
| **Interview Graph** | Orchestrates the interview session; owns the runtime lifecycle |
| **Reasoning Engine** | Accumulates intelligence about the candidate across question cycles |
| **Knowledge Pipeline** | Derives structured features from observations within each reasoning cycle |
| **Session Closure** | Seals all accumulated knowledge into an immutable SessionHistory |
| **Reporting** | Projects SessionHistory into a structured, presentation-ready Report |
| **Presentation Layer** | Reads the Report and renders it for the user |
| **Replay** | Reconstructs knowledge from a sealed SessionHistory for historical analysis |

---

## 2. Runtime Architecture

### The Interview as a Graph

The entire interview runtime is expressed as a directed graph managed by a dedicated graph orchestrator. Every step in the interview — question generation, answer evaluation, reasoning, navigation, session closure, report generation — is a node in this graph. Every transition between steps is an edge.

This design is not incidental. It is a constitutional constraint. The graph orchestrator is the sole runtime orchestrator. No service, pipeline, or coordinator may sequence operations or implement conditional routing outside of graph edges. This constraint prevents hidden orchestration: execution paths whose behavior is invisible to graph-level inspection.

### Runtime Flow

The interview session proceeds through the following phases:

**Initialization.** The session begins with a start node that configures the session context, loads questions, and transitions to the question phase.

**Question Cycle.** The question node selects and presents a question. The candidate's answer triggers evaluation (for correctness, written quality, or code execution), followed by feedback generation.

**Reasoning Cycle.** After each question cycle, the reasoning node executes. This is the knowledge accumulation step. The reasoning node extracts observations from the answer, runs the knowledge pipeline to derive features and update the candidate profile, and executes reasoning detectors that produce advisory decisions about how the interview should proceed.

**Navigation.** The navigation node reads the reasoning decision and the current session state to determine the next action: ask another question, retry the current question, or end the session.

**Session Closure.** When the interview ends, the session-close node seals all accumulated knowledge. It assembles the knowledge snapshot, generates the narrative, produces the coaching snapshot, and writes the session history.

**Report Generation.** The report node reads the sealed session history and assembles the final report. No new computation occurs at this step.

### Why the Graph Is the Sole Orchestrator

Services and pipelines compute results. They do not decide what happens next. The graph decides what happens next. This separation ensures that every conditional branch in the interview lifecycle is visible, testable, and documented as a graph edge — not buried inside a service method or a pipeline stage.

A service that sequences two operations is a hidden orchestrator. A pipeline that calls the next node is a hidden orchestrator. The architecture prohibits both.

---

## 3. Knowledge Flow

Knowledge flows through the platform in a single, unidirectional chain. Each stage is strictly downstream of the previous one. No stage reaches backward to re-derive data that a prior stage already produced.

```
Answer
  ↓
Observation        (raw signal: what was demonstrated in this answer)
  ↓
FeatureCandidate   (typed, dimensioned signal: candidate for a ProfileFeature)
  ↓
ProfileFeature     (resolved, evidence-backed capability unit)
  ↓
CandidateProfile   (ordered collection of ProfileFeatures for this session)
  ↓
CandidateProfileSnapshot  (sealed projection at session close)
  ↓
KnowledgeSnapshot  (all session-close artifacts: profile, narrative, coaching)
  ↓
SessionHistory     (complete, self-contained session record)
  ↓
Report             (projection for presentation)
```

### Stage Responsibilities

**Observation.** A raw, uninterpreted signal extracted from a candidate's answer. It carries evidence of what was said or demonstrated but makes no claim about the candidate's capability. Observations are the inputs to feature derivation; they are never directly presented to the user.

**FeatureCandidate.** An intermediate object produced by a `FeatureUpdater`. It proposes a feature value and direction for a specific capability dimension, based on one or more observations. Feature candidates are resolved by a `FeatureComposer` before becoming `ProfileFeature` instances.

**ProfileFeature.** The platform's primary unit of knowledge about a candidate. A `ProfileFeature` has a type, a value, a direction, a confidence level, and a provenance chain linking it back to the observations that support it. It is immutable once produced.

**CandidateProfile.** An ordered collection of `ProfileFeature` instances representing the current knowledge state for the session. Updated at each reasoning cycle. The latest profile is the authoritative representation of what has been learned about the candidate so far.

**CandidateProfileSnapshot.** A sealed, point-in-time projection of the `CandidateProfile` at session close. It contains no new derivation — it is a structured copy of the feature set at the moment of closure. It exists to make the historical profile inspectable independently of the live session.

**KnowledgeSnapshot.** The complete sealed record of all knowledge artifacts produced during the session: profile snapshot, narrative, and coaching snapshot. Assembled by `KnowledgeSnapshotBuilder` at session close.

**SessionHistory.** The complete, self-contained record of the session: knowledge snapshot, question timeline, transcript, session metadata, and replay hints. Written once. Never modified after construction. The canonical source of truth for everything that happened during the session.

**Report.** A structured projection of the `SessionHistory` for presentation. Assembled by `ReportBuilder`. It contains no new knowledge — every value in the report was either accumulated during the session or assembled from session-close artifacts.

---

## 4. State Model

### InterviewState

`InterviewState` is the single data structure that carries the entire session state across every node in the graph. Every node receives the current `InterviewState` and returns a new one. No node holds a reference to a prior state. No node modifies a state object after returning it.

`InterviewState` contains:

- **Session configuration** — role, interview type, seniority, language
- **Question state** — the question list, the current question, asked question IDs
- **Answer and result state** — answers, per-question results, dimension signals
- **Reasoning state** — `InterviewMemory` (evidence, coverage, reasoning history, session metrics), the current reasoning decision
- **Pipeline artifacts** — `ObservationStore`, `CandidateProfile` (V1.2 path)
- **Closure artifacts** — `SessionHistory`, `Report`
- **Navigation state** — allowed actions, retrieval memory, follow-up state
- **Processing flags** — `is_processing`, `current_step`, `is_completed`

### Immutable State Transitions

Every state transition in the platform is a replacement, never a mutation. When a node needs to update the state, it creates a new `InterviewState` that copies all unchanged fields and sets the updated ones. In-place field assignment to a state object is prohibited.

This constraint eliminates an entire class of bugs: it is impossible for a downstream node to observe a state that was partially modified by an upstream node's concurrent operation. Each node sees a complete, consistent snapshot.

### Ownership

Every field in `InterviewState` has a declared sole writer: the one node responsible for setting it. No other node writes to that field. This constraint ensures that the provenance of every value in the state is unambiguous. When a value is wrong, there is exactly one place to look.

---

## 5. Architectural Layers

The platform is organized into layers with a strict dependency direction. Higher layers depend on lower layers; lower layers never depend on higher layers.

### Domain Layer

The foundation of the platform. Contains all immutable contracts, value objects, and typed representations. The domain layer defines what things are. It contains no computation, no LLM calls, and no I/O.

Everything in the domain layer is immutable. Domain objects are correct by construction — they cannot be created in an invalid state, and they cannot be modified after creation.

### Services Layer

Contains the computational units of the platform: Engines, Generators, and specialized services. Services are stateless and side-effect-free. They receive inputs, apply business logic, and return results. They do not hold session state, do not call the graph orchestrator, and do not produce domain artifacts directly.

Services are organized by responsibility: reasoning, feature derivation, narrative generation, coaching, evaluation, question selection. Each service has a single, well-defined responsibility.

### Pipeline Layer

Contains composed sequences of service invocations, organized into named stages. Pipelines are owned by specific graph nodes — a pipeline is a node's private computational helper, not a shared runtime component. Pipelines return results. They do not route. They do not hold state. They do not know which node will receive their output.

### Graph Layer

Contains the LangGraph node implementations. Each node is an orchestration unit: it receives `InterviewState`, delegates computation to services and pipelines, assembles results using builders, and returns a new `InterviewState`. Nodes contain minimal logic. Their responsibility is orchestration, not computation.

### Builder Layer

Contains the sole construction paths for all immutable artifacts. Builders are fluent, stateless assembly components. They accept pre-computed inputs, validate mandatory fields, and produce immutable domain artifacts. Builders contain no business logic and no derivation. They assemble; they do not compute.

### Presentation Layer

Contains the UI layer, DTOs, export handlers, and view builders. The presentation layer is a reader of closed artifacts. It formats, projects, and displays knowledge that the rest of the platform has already produced. It does not derive new knowledge, does not modify domain objects, and does not call any Engine or Pipeline.

### Replay Layer

Contains the infrastructure for deterministic reconstruction of knowledge artifacts from sealed `SessionHistory` instances. The replay layer is isolated from the live runtime path. It uses replay-specific engines that process stored feature data rather than live observations. The replay layer never writes to `InterviewState` fields owned by live runtime nodes.

---

## 6. Core Runtime Components

### ObservationExtractor

Responsibility: extract raw, typed observations from a candidate's answer and the current reasoning context. Produces `Observation` instances for the `ObservationStore`. Does not interpret observations — it extracts them. Runs within the reasoning node's Phase C.

### FeatureEngine

Responsibility: derive `ProfileFeature` instances from `Observation` instances. Invokes a registered set of `FeatureUpdater` implementations, resolves candidates through a `FeatureComposer`, and returns a set of typed features. Does not produce a `CandidateProfile` directly — that is the Builder's responsibility.

### KnowledgePipeline

Responsibility: coordinate the execution of `ObservationExtractor` and `FeatureEngine` within each reasoning cycle. Owned by `reasoner_node`. Accepts the current `ObservationStore` and the prior `CandidateProfile`, runs the pipeline stages, and returns an updated `CandidateProfile`. Does not write to `InterviewState` — that is the node's responsibility.

### NarrativeGenerator

Responsibility: produce a structured `Narrative` from the session's accumulated knowledge at close time. The narrative provides human-readable insight into the candidate's performance across key dimensions. Runs once per session, within `session_close_node`.

### CoachingEngine

Responsibility: produce a `CoachingSnapshot` from the session's accumulated knowledge at close time. The coaching snapshot contains prioritized learning objectives, study recommendations, and coaching actions. Runs once per session, within `session_close_node`.

### ReasonerService

Responsibility: execute the reasoning cycle for a single question. Runs a registered set of pattern detectors against the current reasoning input, produces a `ReasonerDecision` and a `ReasoningTrace`, and returns an updated `InterviewMemory`. The reasoning decision advises the navigation node but does not control it — the graph controls routing.

### AdaptiveNavigationNode

Responsibility: select the next action for the interview based on the current reasoning decision, retrieval memory, and session configuration. Updates the retrieval memory with the result of the completed question cycle. Returns a navigation decision that the graph uses to route to the next node.

### ReportBuilder

Responsibility: assemble a `Report` from a sealed `SessionHistory`. The sole construction path for `Report`. Contains no business logic — it reads pre-computed values from `SessionHistory` and assembles them into the report structure. Validates that all mandatory fields are present before constructing the artifact.

### SessionClosePipeline

Responsibility: execute the staged assembly of session-close artifacts. Produces `CandidateProfileSnapshot`, `KnowledgeSnapshot`, and `SessionHistory` from the session's accumulated state. Owned exclusively by `session_close_node`. Returns a result — does not write to `InterviewState`.

---

## 7. Immutable Artifacts

All major platform artifacts are immutable after construction. Once produced, their values never change. This section describes each artifact, its producer, and its consumers.

### ProfileFeature

**Producer:** `FeatureEngine` (via a `FeatureUpdater` and `FeatureComposer`)
**Consumers:** `CandidateProfileBuilder`, `ReasonerService` detectors, `session_close_node`
**Lifecycle:** Produced per reasoning cycle. The latest set of features for all types constitutes the current knowledge state.
**Purpose:** The primary unit of structured knowledge about a candidate capability.

### CandidateProfile

**Producer:** `CandidateProfileBuilder` (sole construction path)
**Writer:** `reasoner_node` (via `KnowledgePipeline`)
**Consumers:** `ReasonerService`, `session_close_node`, `NarrativeGenerator`, `CoachingEngine`
**Lifecycle:** Updated at each reasoning cycle. Replaced, never mutated.
**Purpose:** The current, ordered collection of all known `ProfileFeature` instances for the session.

### CandidateProfileSnapshot

**Producer:** `session_close_node` (directly constructs from `CandidateProfile.features`)
**Consumers:** `KnowledgeSnapshotBuilder`, `ReportBuilder`, Replay path
**Lifecycle:** Written once at session close. Never modified.
**Purpose:** A sealed, historical projection of the `CandidateProfile` at closure.

### KnowledgeSnapshot

**Producer:** `KnowledgeSnapshotBuilder` (sole construction path)
**Writer:** `session_close_node` (via `SessionClosePipeline`)
**Consumers:** `SessionHistoryBuilder`
**Lifecycle:** Written once at session close. Never modified.
**Purpose:** The complete sealed record of all session knowledge artifacts.

### SessionHistory

**Producer:** `SessionHistoryBuilder` (sole construction path)
**Writer:** `session_close_node`
**Consumers:** `report_node`, Replay path
**Lifecycle:** Written once at session close. Never modified.
**Purpose:** The complete, self-contained record of the session, including knowledge snapshot, transcript, timeline, and replay metadata.

### Report

**Producer:** `ReportBuilder` (sole construction path)
**Writer:** `report_node`
**Consumers:** Presentation layer, export handlers
**Lifecycle:** Written once after session close. Never modified.
**Purpose:** A structured, presentation-ready projection of the `SessionHistory`.

### InterviewMemory

**Producer:** `ReasonerService`
**Writer:** `reasoner_node`
**Consumers:** `ReasonerService`, pattern detectors
**Lifecycle:** Replaced at each reasoning cycle with a fully reconstructed instance that includes all accumulated evidence, coverage state, reasoning history, and session metrics.
**Purpose:** The accumulation point for reasoning intelligence across the session.

---

## 8. Architectural Patterns

The platform defines six official patterns, originally identified in the architectural retrospective and ratified in the Architecture Constitution (ARC-01). Each pattern addresses a recurring architectural challenge.

### OP-01 — Cascading Closure

Session termination is structured as a cascade of idempotent, write-once steps. Each step consumes the output of the prior step. Each step guards on its input being non-null and is independently non-fatal.

**Where it appears:** `session_close_node` produces `SessionHistory`; `report_node` consumes it to produce `Report`. Both nodes are independently idempotent and independently non-fatal.

### OP-02 — Projection Artifact

A mutable runtime artifact is captured at a lifecycle boundary as an immutable, self-contained projection. The projection contains no new computation.

**Where it appears:** `CandidateProfileSnapshot` is a projection of `CandidateProfile` at session close. `Report` is a projection of `SessionHistory`.

### OP-03 — Runtime First / Projection Later

All knowledge computation occurs during the live runtime cycle. Session close and downstream operations are pure assembly.

**Where it appears:** `FeatureEngine`, `NarrativeGenerator`, and `CoachingEngine` are invoked during the live session (in `reasoner_node` and, for narrative and coaching, at the end of the live reasoning phase in `session_close_node`). `report_node` reads without computing.

### OP-04 — Sole Writer Node

Each `InterviewState` field has exactly one node that is its sole writer. The node declares its write targets. No other node writes to those fields.

**Where it appears:** `session_close_node` is the sole writer of `state.session_history`. `report_node` is the sole writer of `state.report`. `reasoner_node` is the sole writer of `state.observation_store`, `state.candidate_profile_v2`, and `state.interview_memory`.

### OP-05 — Single Builder

Every immutable artifact has exactly one Builder. Direct constructor invocation of the artifact is prohibited in production paths.

**Where it appears:** `CandidateProfileBuilder`, `KnowledgeSnapshotBuilder`, `SessionHistoryBuilder`, `ReportBuilder`.

### OP-06 — Immutable Accumulation

Accumulation artifacts are replaced, never mutated. Each replacement explicitly enumerates every field of the target type to prevent silent data loss.

**Where it appears:** `InterviewMemory` is replaced at each reasoning cycle. `CandidateProfile` is replaced at each knowledge pipeline execution.

---

## 9. Extension Points

The platform is designed to be extended along well-defined seams. Each extension point is governed by a pattern that specifies what may change and what must remain stable.

### Adding a New Knowledge Feature Type

Implement a new `FeatureUpdater` that produces `FeatureCandidate` instances for the new feature type. Register it in the `FeatureEngine` configuration. Add a `FeatureIdentity` entry for the new type. The `FeatureEngine`, `CandidateProfileBuilder`, and all downstream consumers require no modification.

### Adding a New Reasoning Detector

Implement a new detector that conforms to the detector interface. Register it in the detector registry with an appropriate priority. The `ReasonerService` and `reasoner_node` require no modification. The new detector will be invoked at each reasoning cycle and its output will be incorporated into the `ReasonerDecision`.

### Extending the Knowledge Pipeline

Add a new stage to the `KnowledgePipeline` that accepts the output of the prior stage and returns an updated result. The stage must be non-fatal (return the prior stage's output on failure) and must not produce a domain artifact directly (that is the Builder's responsibility). The owning node requires no modification beyond registering the new stage.

### Extending the Closure Cascade

Add a new step to the `SessionClosePipeline` that follows the Cascading Closure pattern (OP-01): guard on the prior step's output being non-null, produce a new immutable artifact, return a result. The new step must be assigned a sole writer node. A new ADR is required if the new step crosses a constitutional boundary.

### Extending Reporting

Add a new field to `Report` by extending `ReportBuilder` with a new fluent setter and populating it from `SessionHistory`. The presentation layer may then read the new field. No computation may be added to `report_node` or `ReportBuilder` — any new knowledge must be accumulated during the live session and stored in `SessionHistory` before `report_node` executes.

### Extending Replay

Add a new `ReplayFeatureUpdater` to the replay path. Ensure it is registered only in `ReplayFeatureEngine` and never in the live `FeatureEngine`. Ensure the reconstruction is deterministic: the same `SessionHistory` must always produce the same reconstructed profile. An ADR is required for any change that modifies the replay boundary.

### Extending Navigation

Modify the `AdaptiveNavigationNode` to incorporate new signals from the reasoning decision or session state. Navigation decisions must remain within the node — they must not be delegated to a service that implements routing logic.

---

## 10. Reading Order

A new engineer should explore the project in the following order. Each step builds on the previous one.

### Step 1 — Architecture Guide (this document)

Establish a conceptual model of the platform: what it does, how knowledge flows, and how the major components relate. Do not read any source code yet.

### Step 2 — Architecture Constitution (ARC-01)

Understand the non-negotiable principles. Every subsequent architectural decision is governed by these principles. The Constitution explains not just what the rules are but why they exist.

### Step 3 — Architecture Review Checklist (ARC-02)

Understand how architectural compliance is verified. The checklist operationalizes the Constitution and provides the practical framework for evaluating proposals.

### Step 4 — ADR Governance (ARC-03)

Understand how architectural decisions are recorded and managed. Before reading individual ADRs, understand the governance framework that gives them meaning.

### Step 5 — ADR Catalogue

Read the active ADRs in numerical order. Each ADR records a binding decision. Together they describe the specific constraints that govern the current architecture.

### Step 6 — Domain Contracts

Read the domain layer contracts: `ProfileFeature`, `CandidateProfile`, `KnowledgeSnapshot`, `SessionHistory`, `Report`, `InterviewMemory`. These are the types that the rest of the system manipulates. Understanding their shapes is a prerequisite for understanding any runtime component.

### Step 7 — Graph Nodes

Read the graph node implementations in pipeline order: `reasoner_node`, `session_close_node`, `report_node`, `navigation_node`. Each node has a module docstring that declares its responsibilities, write targets, and constraints.

### Step 8 — Services and Pipelines

Read the service implementations for the areas relevant to your current work. Services are organized by responsibility; explore the area that your task falls into.

### Step 9 — Tests

Read the architectural invariant tests before reading the behavioral tests. The invariant tests document the ownership and immutability contracts that the behavioral tests rely on.

---

## 11. Reference Map

The following documents together constitute the architectural governance record of the platform. Each has a distinct, non-overlapping purpose.

| Document | Purpose |
|----------|---------|
| **Architecture Guide** (this document) | Descriptive: explains how the platform is organized, what the components do, and how they relate. The starting point for all engineers. |
| **Architecture Constitution** (ARC-01) | Normative: defines the non-negotiable principles that govern every future decision. The highest-level reference. Supersedes all other documents on matters of principle. |
| **Architecture Review Checklist** (ARC-02) | Operational: defines the verification process for every architectural proposal. Operationalizes the Constitution for practical review use. |
| **ADR Governance** (ARC-03) | Process: defines the lifecycle, structure, and management rules for Architecture Decision Records. Governs how decisions are proposed, approved, and superseded. |
| **ADR Catalogue** | Binding decisions: each ADR records a specific architectural decision within the principles established by the Constitution. Binding on all implementations in scope. |
| **Pattern Application Tracking (PATs)** | Implementation conventions: specify how official patterns are applied in code. More specific than ADRs; less fundamental than the Constitution. |

### Governance Hierarchy

```
Architecture Constitution          — what may never be violated
        ↓
Architecture Review Checklist      — how compliance is verified
        ↓
ADR Governance                     — how decisions are recorded
        ↓
Architecture Decision Records      — specific binding decisions
        ↓
Pattern Application Tracking       — implementation conventions
        ↓
Implementation
```

When any conflict arises between levels of this hierarchy, the higher level takes precedence. An implementation that satisfies all PATs but violates an ADR is non-compliant. An ADR that satisfies the review checklist but contradicts the Constitution is invalid.

The Architecture Guide does not occupy a position in the governance hierarchy. It is descriptive, not normative. It describes the architecture as it stands; it does not govern how it must evolve. That governance is the responsibility of the Constitution, the Checklist, the ADR Governance document, and the ADR catalogue.
