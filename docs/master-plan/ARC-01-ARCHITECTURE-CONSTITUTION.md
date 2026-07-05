# Architecture Constitution — AI Interview Simulator Platform

**Version 1.0 | Extracted from V1.2 RC1 | Effective from RC1 Freeze**

---

## Preamble

This document is the highest-level architectural reference for the platform. It extracts the constitutional principles that govern every future evolution. It does not describe how V1.2 was implemented. It describes what was learned by implementing it — and what must never be violated without an explicit architectural decision.

Individual ADRs govern specific design choices. Individual PATs govern specific implementation patterns. This Constitution governs both. When an ADR and the Constitution conflict, the Constitution takes precedence. When a new ADR is proposed, it must first demonstrate constitutional compliance.

This document is intentionally abstract. It should remain valid across V1.3, V1.4, and beyond.

---

## 1. Mission

The platform's architectural mission is to accumulate structured knowledge about a candidate's capabilities across a live, multi-turn interview session and to make that knowledge available for deterministic projection, historical inspection, and longitudinal evolution.

Three responsibilities follow from this mission:

**Accumulation.** The live runtime cycle is the only legitimate site of knowledge computation. Every observation, signal, feature derivation, and reasoning decision must occur within the runtime cycle, not at session close, not at report generation, not in the UI layer.

**Closure.** At session end, all accumulated knowledge is sealed into an immutable, self-contained artifact. No computation occurs at closure. Closure is a structured projection of what the runtime already produced.

**Projection.** Downstream consumers — reports, UI, exports, replay — read from closed artifacts. They never recompute, regenerate, or augment the knowledge they display.

These three responsibilities define the constitutional boundary of the system. Any component that violates the boundary between accumulation, closure, and projection is architecturally incorrect regardless of whether it produces correct output.

---

## 2. Core Principles

### P-01 — The Runtime Computes; Projection Never Computes

**Rationale.** V1.1 ran feature derivation, narrative generation, and coaching computation at session close. This made session close slow, non-deterministic, and expensive to test. V1.2 moved all computation into the live reasoning cycle. Session close and report generation became pure assembly. The distinction proved so consequential that it must be constitutionally protected.

**Statement.** Knowledge computation — including LLM calls, feature derivation, signal extraction, narrative generation, and coaching evaluation — must occur only within the live runtime cycle (i.e., within `reasoner_node` and its subordinate pipelines). Session close, report generation, and UI rendering are projection operations. They assemble, format, and display. They do not compute.

**Consequences.** Any node whose sole purpose is session termination or artifact assembly must not invoke `FeatureEngine`, `NarrativeGenerator`, `CoachingEngine`, `KnowledgePipeline`, or any LLM-backed service. Replay is a controlled exception governed by the Replay Boundary (§3).

**Examples.** `session_close_node` reads `state.candidate_profile_v2.features` — it does not run the feature engine again. `report_node` reads `state.session_history` — it does not recompute the narrative. `UIResponseBuilder` reads `state.report` — it does not re-derive scores.

**Anti-patterns.** Running `FeatureEngine` inside `session_close_node`. Calling `NarrativeGenerator` inside `report_node`. Computing dimension scores inside `UIResponseBuilder`. Invoking any LLM in any node other than `reasoner_node` and its direct dependencies.

---

### P-02 — Single Ownership

**Rationale.** Every case of data corruption, inconsistency, or silent state divergence in V1.1 traced back to an artifact that had more than one producer or more than one writer. When ownership is shared, correctness becomes a coordination problem. When ownership is singular, correctness is a local invariant.

**Statement.** Every runtime artifact must have exactly one producer (the component responsible for its computation), exactly one writer (the node responsible for persisting it to `InterviewState`), and a declared set of readers. No artifact may be produced or written by more than one component.

**Consequences.** Dual-path migrations — where both an old and a new path can produce the same artifact — are constitutionally prohibited. When a new production path is introduced, the old path must be disabled in the same migration increment.

**Examples.** `CandidateProfileBuilder` is the sole producer of `CandidateProfile`. `reasoner_node` is the sole writer of `state.candidate_profile_v2`. `session_close_node` is the sole writer of `state.session_history`. `report_node` is the sole writer of `state.report`.

**Anti-patterns.** Two builders for the same artifact. A node that reads a field produced by another node and then republishes it under a different name. A migration that activates a new production path while leaving the old one active.

---

### P-03 — Immutable Domain Contracts

**Rationale.** Mutable shared objects make it impossible to reason about state at any point in time. Immutability guarantees that the state observed at the entry of a node is identical to the state that existed when it was written.

**Statement.** All domain contracts — every object that represents knowledge, state, or an intermediate computation result — must be immutable after construction. Construction is the only moment at which values may be set. Post-construction mutation is prohibited.

**Consequences.** All `InterviewState` updates must use `model_copy`. All domain contracts must be declared with `frozen=True` or its equivalent. No field may be updated in place. Every "update" is a new object.

**Examples.** `ProfileFeature(frozen=True)`. `Report(frozen=True)`. `InterviewState.model_copy(update={...})`. `InterviewMemory` replaced, not mutated, at each reasoning cycle.

**Anti-patterns.** In-place mutation of any domain object. Appending to a list field on an existing domain object. Modifying a `CandidateProfile` after it has been produced by `CandidateProfileBuilder`.

---

### P-04 — LangGraph Is the Sole Runtime Orchestrator

**Rationale.** V1.1 had coordinator objects, service chains, and sequential runners that duplicated routing logic outside the graph. This created hidden orchestration — execution paths whose behavior was invisible to the runtime graph and untestable through graph-level inspection.

**Statement.** All runtime control flow — node sequencing, conditional routing, retry logic, and session lifecycle management — must be expressed as LangGraph edges and conditions. No production service, no pipeline, and no node may invoke another node directly. No object may implement a sequence of operations that constitutes graph routing.

**Consequences.** Services and pipelines are computational units, not orchestrators. They compute a result and return it. They do not decide what happens next. Only the graph decides what happens next.

**Examples.** `SessionClosePipeline.run()` returns a result — it does not invoke `report_node`. `ReasonerService.reason()` returns a decision — it does not advance the interview. `KnowledgePipeline` returns a `CandidateProfile` — it does not trigger `session_close_node`.

**Anti-patterns.** A service that calls two nodes in sequence. A pipeline that has a reference to the LangGraph runner. A coordinator class that contains `if state.is_completed: run_session_close()`. Any object with the word "coordinator," "runner," "sequencer," or "orchestrator" in its name.

---

### P-05 — Builders Assemble; Engines Compute

**Rationale.** Mixing assembly logic with computation logic produces objects that are simultaneously too complex and too coupled. Separating them creates components that can be tested, reasoned about, and evolved independently.

**Statement.** Engines perform computation — they transform inputs into derived knowledge through non-trivial logic. Builders assemble — they collect pre-computed components and construct an immutable artifact. A Builder must never contain computation logic. An Engine must never construct immutable artifacts directly.

**Consequences.** Every immutable artifact has exactly one Builder (sole creation path, PAT-05). No Builder contains conditional business logic. No Engine produces a final domain artifact. The output of an Engine is always an intermediate computational result, not a finished domain contract.

**Examples.** `FeatureEngine` produces `ProfileFeature[]` — it does not build a `CandidateProfile`. `CandidateProfileBuilder` assembles `ProfileFeature[]` into a `CandidateProfile` — it does not run feature derivation. `NarrativeGenerator` produces a `Narrative` — `KnowledgeSnapshotBuilder` assembles it into a `KnowledgeSnapshot`.

**Anti-patterns.** A Builder that calls an LLM. A Builder that contains if/else logic derived from feature values. An Engine that returns a finished `Report`. A `build()` method that has side effects.

---

### P-06 — Fail Fast Over Silent Fallback

**Rationale.** Every silent fallback in V1.1 — including the legacy navigation fallback — eventually caused either a production incident or architectural confusion. A silent fallback allows the system to continue with wrong behavior without emitting any observable signal. A fail-fast invariant surfaces the configuration error immediately, where it can be fixed.

**Statement.** Startup invariants must raise explicit, descriptive exceptions when violated. Runtime invariants must log warnings at a visible severity level when violated. No invariant may be satisfied by silently changing the system's behavior. Graceful degradation is acceptable; silent behavioral change is not.

**Consequences.** `configure_navigation_node()` must be called before graph invocation; failure raises `RuntimeError`. A missing `candidate_identity_id` must be detected and logged, not silently replaced with `interview_id` in perpetuity. An absent `state.report` must surface as "No report available," not as a blank screen.

**Examples.** `navigation_node` raises `RuntimeError` if `_default_navigation_node is None`. `report_node` logs a warning and clears flags if `ReportBuilder` fails — it does not silently omit the report step. `UIStateMachine` routes to an explicit "No report available" state rather than rendering an empty panel.

**Anti-patterns.** `if node is None: use_legacy_node()`. `try: ... except Exception: pass`. Any fallback that changes the system's effective behavior without logging at WARNING or above.

---

### P-07 — Delete Legacy Code; Never Deprecate Indefinitely

**Rationale.** Every "temporarily deprecated" object in V1.1 that was not deleted eventually acquired new consumers. Deprecation without deletion is a deferred cost that grows. The correct migration completion criterion is "legacy code deleted," not "new code activated."

**Statement.** When a migration activates a new path that supersedes an old one, the old path must be deleted in the same migration increment or in the immediately following increment. Deprecated objects must carry an explicit deletion ticket. Any object that remains in the codebase beyond one migration increment after deprecation is not deprecated — it is active.

**Consequences.** Compatibility bridges have a declared deletion date at creation. Deprecated fields in `InterviewState` are removed in the same sprint as the new field is activated. Test files that protect deleted behavior are removed alongside the production code.

**Examples.** `InterviewMemoryContext` was deleted in RC1-02 — not left as a deprecated import. `_legacy_navigation_node()` was deleted in RC1-01 — not wrapped in a deprecation warning. The dual `CandidateProfile` path was deleted when `FeatureEngine` became the sole producer.

**Anti-patterns.** `# deprecated — use InterviewMemory instead` left in production for more than one sprint. A bridge class that reads from the old format and writes to the new format, kept "just in case." TCP fields that outlive their migration sprint by more than one increment.

---

### P-08 — Reconstruction Completeness

**Rationale.** When an immutable object is reconstructed from a prior version (as occurs in `_append_reasoning_entry` in `reasoner_node`), every field of the target type must be explicitly included in the reconstruction. The absence of this discipline caused `session_metrics` to be silently dropped for multiple sprints.

**Statement.** Any function that constructs a new version of an immutable object from a prior version must explicitly enumerate every field of that object. The enumeration must be updated whenever a field is added to the target type. A reconstruction function that uses a wildcard copy (`**prior.__dict__`) is constitutionally prohibited.

**Consequences.** `_append_reasoning_entry` must list every field of `InterviewMemory` explicitly. When a new field is added to `InterviewMemory`, the reconstruction function must be updated in the same commit. Architectural tests must assert that the reconstruction path covers all declared fields.

**Examples.** `InterviewMemory(evidence_store=..., coverage_state=..., reasoning_history=..., session_metrics=..., schema_version=...)` — all five fields listed explicitly.

**Anti-patterns.** `InterviewMemory(**prior_memory.dict())`. `prior_memory.model_copy(update={"reasoning_history": new_history})` — this silently carries forward a stale `session_metrics` if the caller forgets to include it.

---

## 3. Constitutional Boundaries

A Constitutional Boundary defines a transition that requires a new ADR before it may be crossed. Crossing a boundary without an ADR is a constitutional violation regardless of the correctness of the resulting behavior.

**The Computation/Projection Boundary**
Separates the live runtime cycle from all post-cycle operations. Crossing this boundary means adding a computation operation (LLM call, feature derivation, signal extraction) to a node that currently performs only assembly or projection. Requires a new ADR justifying why runtime-cycle execution is not possible.

**The Immutable Contract Boundary**
Separates fields that may change during a session from fields that are permanently sealed after construction. Crossing this boundary means adding mutability to a previously frozen artifact. Requires a new ADR and a detailed analysis of the ownership implications.

**The Ownership Boundary**
Separates a component's declared ownership of an artifact from any other component that might produce or write it. Crossing this boundary means introducing a second producer or writer for an existing artifact. Requires a new ADR that explicitly declares the ownership transfer, including the deletion of the prior owner.

**The Orchestration Boundary**
Separates LangGraph (sole orchestrator) from all other components. Crossing this boundary means implementing routing, sequencing, or conditional control flow outside of LangGraph edges. Requires a new ADR with a constitutional exemption and explicit justification for why graph-level expression is not possible.

**The Replay Boundary**
Separates the live runtime computation path from the controlled reconstruction path. Crossing this boundary means running a live-path engine (e.g., `FeatureEngine` with live observations) on historical data, or running a replay-path engine (e.g., `ReplayFeatureEngine`) on live data. Requires a new ADR declaring the replay scope and guaranteeing determinism.

**The Presentation Boundary**
Separates the knowledge layer (`Report`, `SessionHistory`) from the presentation layer (`FinalReportDTO`, `UIResponseBuilder`). Crossing this boundary means computing knowledge-layer values inside the presentation layer. Requires a new ADR. The current RC1 boundary: `state.report` is the entry point; `interview_evaluation` provides scoring data during the RC2 migration window only.

---

## 4. Architectural Vocabulary

These definitions are canonical. When these terms appear in ADRs, PATs, test names, or code comments, they carry the meaning defined here.

**Knowledge.** A structured, derived representation of a candidate's capabilities, inferred from observations and reasoning during a live session. Knowledge is always accumulated progressively; it is never computed in a single batch at session end.

**Observation.** A raw, unstructured signal extracted from a candidate's answer. Observations are the inputs to knowledge derivation. They carry no interpretation — only evidence of what was said or demonstrated. Observations are immutable after extraction.

**Feature.** A typed, dimensioned unit of knowledge derived from one or more observations by a `FeatureEngine`. A feature represents a single, specific capability dimension with a direction, confidence, and evidence provenance. Features are immutable after production.

**Profile.** An ordered collection of `ProfileFeature` instances representing the current knowledge state of a candidate within a session. A profile is produced by `CandidateProfileBuilder` from a `FeatureEngine` result. Profiles are immutable and session-scoped.

**Snapshot.** A point-in-time, read-only projection of a mutable runtime artifact, captured at a lifecycle boundary (typically session close). A snapshot contains no new computation — it is a structured copy of what the runtime already produced. `CandidateProfileSnapshot` is a snapshot of `CandidateProfile` at close time.

**Projection.** The act of transforming a knowledge artifact into a derived representation for a specific consumer (UI, export, report). Projection involves no computation — only formatting, selection, and assembly of pre-existing data.

**Runtime.** The live, session-scoped execution cycle managed by LangGraph. The runtime begins when the first question is asked and ends when `session_close_node` writes `state.session_history`. The runtime is the only legitimate site of knowledge computation.

**Builder.** A fluent, stateless assembly component that constructs an immutable artifact from pre-computed inputs. A Builder contains no business logic, no LLM calls, and no conditional derivation. Its `build()` method validates mandatory fields and constructs the target object.

**Engine.** A stateless computational component that transforms inputs into derived knowledge. Engines contain business logic and may invoke LLM-backed services. An Engine's output is an intermediate result — never a finished domain artifact. Examples: `FeatureEngine`, `NarrativeGenerator`, `CoachingEngine`.

**Pipeline.** A composed sequence of `Engine` and `Builder` invocations, organized into named stages, owned by a single node. A pipeline is not an orchestrator — it returns a result and does not decide what happens next. Examples: `KnowledgePipeline`, `SessionClosePipeline`.

**Node.** A LangGraph execution unit that reads `InterviewState`, performs a defined operation (delegating to Engines, Pipelines, or Builders), and returns a new `InterviewState`. Every node has a declared set of write targets. Every node is the sole writer of its declared targets.

**Replay.** A controlled reconstruction of knowledge artifacts from a closed `SessionHistory`, using stored data rather than live observations. Replay is deterministic by design. Replay uses `ReplayFeatureEngine`, not the live `FeatureEngine`. Replay occurs outside the live runtime cycle.

---

## 5. Official Patterns

### OP-01 — Cascading Closure

**Intent.** Structure session termination as a cascade of idempotent, write-once steps, each consuming the output of the prior step.

**Applicability.** Any multi-step session termination process where each step produces an immutable artifact consumed by the next.

**Structure.** Step N produces artifact A. Step N+1 guards on `A is not None` before executing. Step N+1 produces artifact B from A. Each step is independently non-fatal and independently idempotent.

**Benefits.** Independent testability. Independent non-fatal behavior. Safe retry at any step. Absence of an artifact at any step propagates cleanly to the next step without corrupting state.

**Common mistakes.** Making Step N+1 produce artifact A as a side effect when it cannot find it. Combining two steps into one node to "simplify." Allowing Step N+1 to compute data that should have been computed in Step N.

---

### OP-02 — Projection Artifact

**Intent.** Capture the state of a mutable runtime artifact at a lifecycle boundary as an immutable, self-contained projection for historical reference or downstream consumption.

**Applicability.** Any artifact whose runtime value changes progressively but whose value at session close must be preserved exactly.

**Structure.** At the lifecycle boundary (session close), the current runtime artifact is passed to a Builder that constructs a frozen Snapshot. The Snapshot contains no new computation. It is a structured copy.

**Benefits.** Enables deterministic replay. Enables historical inspection without re-running computation. Decouples the live profile from the historical record.

**Common mistakes.** Adding derivation logic inside the Snapshot construction. Re-running computation at snapshot time to "enrich" the historical record. Allowing the Snapshot to hold a reference to the live artifact rather than a copy of its values.

---

### OP-03 — Runtime First / Projection Later

**Intent.** Ensure all knowledge computation occurs during the live session cycle, so that session close and downstream operations are pure projection.

**Applicability.** Any operation that derives structured knowledge from session data.

**Structure.** Computation (feature derivation, narrative generation, coaching evaluation) runs inside `reasoner_node` or its subordinate Engines during the live cycle. Session close reads pre-computed values from `InterviewState`. Report generation reads from `SessionHistory`. UI reads from `Report`.

**Benefits.** Session close is fast, deterministic, and inexpensive. Reports are reproducible from `SessionHistory` without re-running computation. The runtime cycle is the single source of truth for all knowledge.

**Common mistakes.** Running an LLM call in `session_close_node` because "the data is available there." Enriching a Report with derived values not present in `SessionHistory`. Invoking `FeatureEngine` during export.

---

### OP-04 — Sole Writer Node

**Intent.** Assign each state field to exactly one node that is the sole writer of that field for the session lifetime.

**Applicability.** Every field of `InterviewState` that is written by graph nodes.

**Structure.** Each node declares, in its module docstring, the state fields it writes and the state fields it reads. No other node writes to those fields. The declaration is enforced by architectural tests that verify no other node file imports the writer's sole-write target with write intent.

**Benefits.** Field-level ownership is visible, verifiable, and testable. Persistence bugs are immediately locatable. Adding a new field requires exactly one decision: which node is its sole writer.

**Common mistakes.** A node that reads a field produced by another node and republishes it under a new name. Two nodes that both write the same field "in different conditions." A utility function, called from multiple nodes, that writes a state field.

---

### OP-05 — Single Builder

**Intent.** Every immutable artifact has exactly one Builder, and that Builder is the only permitted construction path.

**Applicability.** All immutable domain artifacts: `CandidateProfile`, `KnowledgeSnapshot`, `SessionHistory`, `Report`.

**Structure.** The Builder is a fluent object with typed setters, validation in `build()`, and no business logic. Direct constructor invocation of the artifact is prohibited in production code (tests may use convenience constructors). The Builder raises `ValueError` if mandatory fields are absent at `build()` time.

**Benefits.** Structural validity is guaranteed by construction. All construction paths converge to the same validation logic. The artifact cannot exist in an invalid state.

**Common mistakes.** Creating a "convenience constructor" that bypasses the Builder for "simple cases." Two Builders for the same artifact with different validation rules. A Builder with conditional logic that produces different artifact shapes depending on inputs.

---

### OP-06 — Immutable Accumulation

**Intent.** Accumulate knowledge progressively across reasoning cycles by replacing, not mutating, the accumulation artifact at each cycle.

**Applicability.** Any artifact that grows across the session lifetime: `InterviewMemory`, `ObservationStore`, `CandidateProfile`.

**Structure.** At the start of each cycle, the node reads the current artifact from `InterviewState`. The Engine or Pipeline produces an updated version. The node writes the new artifact to `InterviewState` via `model_copy`. The prior artifact is discarded. The reconstruction path must enumerate all fields explicitly (P-08).

**Benefits.** Each cycle's input is a complete, valid snapshot of accumulated knowledge. No cycle can corrupt the state of a prior cycle. The accumulation is fully auditable from `InterviewState` at any point.

**Common mistakes.** Appending to a list on the existing artifact in place. Passing a mutable reference to the Engine and allowing it to modify the artifact. Reconstructing the artifact from a subset of fields and relying on defaults for the rest.

---

## 6. Explicit Anti-Patterns

These patterns are constitutionally forbidden. Introducing one requires a documented constitutional exception.

**Dual Ownership.** Two components produce or write the same artifact. The second production path must be disabled in the same increment that activates the first. There is never a valid architectural reason for two runtime paths to produce the same domain artifact simultaneously.

**Hidden Orchestrators.** Any component — service, pipeline, coordinator, factory — that calls other components in a sequence that implements control flow. Control flow is the exclusive domain of LangGraph. A pipeline may have internal stages but must return a result, not invoke the next node.

**Silent Runtime Fallbacks.** A conditional branch that changes the system's effective behavior without emitting a log at WARNING or above. Silent fallbacks make systems appear to function correctly while producing wrong results. Every fallback must be observable.

**Close-Time Recomputation.** Invoking any Engine, LLM call, or `KnowledgePipeline` execution in a closure or projection node. Computation at close time means the knowledge in the closed artifact was not accumulated during the live session — it was computed from a batch of historical data. This violates P-01 and breaks replay determinism.

**Mutable Shared Domain Objects.** Passing a domain object to a service or pipeline and allowing the service to mutate it in place. This is impossible when objects are `frozen=True`, which is why the frozen default is constitutionally required.

**Compatibility Bridges Without Removal Plans.** A bridge, adapter, or translation layer introduced during a migration that does not carry a declared deletion ticket. Bridges without removal plans become permanent features. The presence of a bridge in production code implies the migration is not complete.

**Parallel Production Paths.** A migration that activates a new production path while leaving the old path active in production. The old path must be disabled — not deprecated, disabled — in the same migration increment that activates the new path. Parallel paths create ambiguity about which path is authoritative.

**Reconstruction by Omission.** A reconstruction function that copies a subset of fields from a prior artifact and relies on defaults for the rest. Every field of the target type must be explicitly included. Default values mask silent data loss.

**Presentation-Layer Computation.** A UI builder, DTO mapper, or export handler that derives or enriches knowledge values from raw state. The presentation layer is a reader of closed artifacts. It formats and displays. It does not compute.

---

## 7. Evolution Rules

**Introducing a New Artifact.** Every new runtime artifact requires: a declared type with `frozen=True`, a single Builder as the sole construction path, a declared sole writer node, and declared readers. It must be introduced as a TCP field (nullable) and activated in a subsequent increment. The legacy default (None) must not affect any V1.x node until the field is activated.

**Extending a Pipeline.** A new stage may be added to an existing Pipeline provided: it consumes output from the prior stage, it does not call LangGraph, it does not produce a domain artifact directly (that is the Builder's responsibility), and its failure is non-fatal (the Pipeline returns the prior-stage result on failure).

**Extending the Session Close Cascade.** A new closure step may be added provided: it follows OP-01 (Cascading Closure), it is idempotent, it guards on its input artifact being non-None, it is the sole writer of its output artifact, and its activation crosses the Computation/Projection Boundary only with an ADR.

**Introducing Replay.** A replay path may be introduced provided: it uses `ReplayFeatureEngine` exclusively (not the live `FeatureEngine`), it reads only from closed `SessionHistory` artifacts, it does not write to `InterviewState` fields owned by live nodes, its context declares `is_replay=True`, and its introduction is governed by an ADR crossing the Replay Boundary.

**Longitudinal Knowledge.** A multi-session accumulation artifact may be introduced provided: it is populated only from `CandidateProfileSnapshot` instances from closed sessions (never from live `InterviewState`), it has a single Builder, it is treated as immutable within a session, and it does not introduce shared mutable state between concurrent sessions.

**Scoring Pipeline Evolution.** Moving scoring data from `InterviewEvaluation` to `Report` requires an ADR crossing the Presentation Boundary, a TCP field addition to `Report`, a migration of `FinalReportDTO` to read from `Report`, and deletion of `interview_evaluation` as a routing or presentation dependency once the migration is complete.

---

## 8. Decision Rule

When any proposed architectural change is evaluated, apply the following questions in order. The first question that returns **No** constitutes a constitutional violation and requires either a new ADR with constitutional justification or rejection of the proposal.

---

**Q1 — Computation boundary.**
Does this change introduce computation (LLM call, Engine invocation, feature derivation) outside the live runtime cycle?

- If Yes → constitutional violation unless an ADR crossing the Computation/Projection Boundary is present.
- If No → proceed to Q2.

**Q2 — Ownership.**
Does this change produce or write an artifact that already has a declared sole producer or writer?

- If Yes → constitutional violation unless the prior owner is simultaneously disabled and an ADR crossing the Ownership Boundary is present.
- If No → proceed to Q3.

**Q3 — Immutability.**
Does this change mutate a domain object after construction?

- If Yes → constitutional violation. No ADR exemption is available. Immutability is absolute.
- If No → proceed to Q4.

**Q4 — Orchestration.**
Does this change implement control flow, routing, or node sequencing outside of LangGraph edges?

- If Yes → constitutional violation unless an ADR crossing the Orchestration Boundary is present.
- If No → proceed to Q5.

**Q5 — Builder.**
Does this change introduce a second construction path for an existing immutable artifact?

- If Yes → constitutional violation unless the prior construction path is simultaneously deleted and an ADR is present.
- If No → proceed to Q6.

**Q6 — Deletion.**
Does this change deprecate a component without deleting it in the same or immediately following increment?

- If Yes → the component must be added to the deletion backlog with a declared sprint. If the sprint is not declared, the change is deferred.
- If No → proceed to Q7.

**Q7 — Reconstruction completeness.**
Does this change add a field to an immutable accumulation artifact without updating all reconstruction paths to include the new field?

- If Yes → constitutional violation. The reconstruction path must be updated in the same commit.
- If No → proceed to Q8.

**Q8 — Fail fast.**
Does this change introduce a conditional path that changes observable behavior without emitting a log at WARNING or above?

- If Yes → constitutional violation. Replace the silent conditional with an explicit observable signal.
- If No → the proposal is constitutionally acceptable.

---

## Appendix: Constitutional Hierarchy

```
Architecture Constitution   (this document)
        ↓
Architecture Decision Records (ADRs)
        ↓
Pattern Application Tracking (PATs)
        ↓
Migration Tickets (MIG-xx / RC1-xx)
        ↓
Implementation
```

When a conflict arises at any layer, the higher layer takes precedence. An ADR may not contradict the Constitution. A PAT may not contradict an ADR. A Migration Ticket may not contradict a PAT. Implementation may not contradict a Migration Ticket.

A constitutional amendment — a change to this document — requires an explicit Architecture Review (CAR-level) and consensus that the amendment reflects a validated principle, not a convenience. This document does not change with individual features. It changes when the architecture itself teaches a new lesson that is both fundamental and durable.