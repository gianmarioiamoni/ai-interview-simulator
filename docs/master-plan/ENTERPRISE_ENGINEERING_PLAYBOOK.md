# Enterprise Engineering Playbook
## AI Interview Simulator — and All Future Enterprise Projects

**Version:** 1.2  
**Date:** 2026-07-03  
**Status:** FOUNDATIONAL — Authoritative for all versions ≥ V1.1  
**Classification:** FOUNDATIONAL DOCUMENT  
**Supplements:** Platform Engineering Manifest

---

## Section A — Purpose

This Playbook exists because principles alone do not produce consistent execution.

The **Platform Engineering Manifest** defines *what* the engineering standards are. It is the constitution — permanent, authoritative, non-negotiable.

This **Playbook** defines *how* engineering work is actually performed, day to day, milestone by milestone, prompt by prompt.

The Manifest answers: "What does correct engineering look like?"  
The Playbook answers: "How do I perform it tomorrow morning?"

### Document Ecosystem

| Document | Role | When Used |
|---|---|---|
| **Platform Engineering Manifest** | Engineering constitution — principles and invariants | Referenced every time an architectural decision is made |
| **Enterprise Engineering Playbook** (this document) | Operational handbook — execution methodology | Referenced every time a milestone begins |
| **PRD** | Product requirements — what to build | Referenced during planning and acceptance |
| **TDS** | Technical design — how to build it | Referenced during architecture design and implementation |
| **ADR** | Individual architectural decisions | Created before implementation begins |
| **README** | Repository identity — outside-world description | Updated at stable release |
| **Technical Debt Register** | Inventory of registered, accepted, and deferred debt | Updated at every audit and freeze |

### How They Interact

```
PRD defines the goal.
    ↓
TDS translates the goal into an architecture.
    ↓
ADRs record individual decisions within that architecture.
    ↓
Manifest validates that every decision complies with principles.
    ↓
Playbook defines how the work is executed operationally.
    ↓
Technical Debt Register tracks what was deferred and why.
    ↓
README summarises the result for the outside world.
```

No document replaces another. Gaps are not acceptable. Every document has a single, unique purpose.

---

## Section B — Project Lifecycle

Every enterprise software project follows this lifecycle. Each phase has a defined purpose, inputs, outputs, and exit criteria.

### Phase 1 — Idea

**Purpose:** Establish that the problem is real and that solving it is viable.  
**Inputs:** Problem statement, user research, business case.  
**Outputs:** Approved problem definition, initial scope boundaries.  
**Exit criteria:** Stakeholder sign-off on problem statement. No implementation begins.

### Phase 2 — Architecture

**Purpose:** Define the system boundaries, component responsibilities, data flows, and extension points before any code is written.  
**Inputs:** Problem definition, platform constraints, existing contracts (if extending).  
**Outputs:** TDS draft (or new TDS section), initial ADR candidates, identified extension points.  
**Exit criteria:** Architecture reviewed and approved. No contract or implementation work begins.

### Phase 3 — Requirements

**Purpose:** Translate the architecture into verifiable acceptance criteria for every deliverable.  
**Inputs:** Approved architecture, TDS.  
**Outputs:** PRD Epic and Milestone definitions with acceptance criteria, milestone-specific acceptance documents.  
**Exit criteria:** Every deliverable has a measurable acceptance criterion. Ambiguity is resolved.

### Phase 4 — Contracts

**Purpose:** Define all cross-component boundaries as explicit, immutable contracts before implementation.  
**Inputs:** Approved architecture, PRD acceptance criteria.  
**Outputs:** Pydantic contracts in `domain/contracts/`, port definitions, frozen DTO schemas.  
**Exit criteria:** All contracts defined with `extra=forbid`. No implementation begins on any component whose contract is not yet frozen.

### Phase 5 — ADR

**Purpose:** Record every non-trivial architectural decision before code is written.  
**Inputs:** Approved contracts, architecture review outputs.  
**Outputs:** Registered ADRs for every decision that is not obvious or that deviates from prior patterns.  
**Exit criteria:** Every decision that will influence implementation is recorded. Implementation is blocked until relevant ADRs are accepted.

### Phase 6 — Implementation

**Purpose:** Build what was designed. Not discover the design by building.  
**Inputs:** Frozen contracts, accepted ADRs, TDS section.  
**Outputs:** Working implementation that satisfies contracts and acceptance criteria.  
**Exit criteria:** All acceptance criteria met. No contract violations. No hidden state. All configuration values in SSOT.

### Phase 7 — Unit Tests

**Purpose:** Verify every component in isolation.  
**Inputs:** Implementation, acceptance criteria, ADR test coverage requirements.  
**Outputs:** Unit test suite with coverage meeting ADR-060 standards.  
**Exit criteria:** All unit tests pass. No new failures introduced. Core reasoning path coverage mandatory.

### Phase 8 — Integration Tests

**Purpose:** Verify that components work together as designed.  
**Inputs:** Unit-tested implementation, contracts.  
**Outputs:** Integration test suite covering all cross-component interactions.  
**Exit criteria:** All integration tests pass. Pipeline execution order verified. State transitions verified.

### Phase 9 — Audit

**Purpose:** Verify that the implementation is structurally correct, not just functionally correct.  
**Inputs:** Complete implementation, test suite, ADRs, contracts.  
**Outputs:** Audit report with findings classified by severity. Technical Debt Register updates.  
**Exit criteria:** No Forbidden debt present. All Accepted debt registered with target milestone. All P0/P1 findings resolved.

### Phase 9a — Construction Architecture Review (CAR)

**Purpose:** Identify architectural violations, structural regressions, and emerging patterns that appeared during construction but were not captured at design time. CAR is the mandatory gate between Construction and Freeze.  
**Inputs:** Completed implementation, accepted ADRs, Implementation Baseline, Phase 9 audit reports.  
**Outputs:** CAR Report (findings P0–P3), Remediation Backlog, Pattern Candidates, Runtime Ownership verification.  
**Exit criteria:** CAR Report issued. All P0/P1 findings identified. Pattern candidates handed to Phase 9b. No second runtime orchestrator present (PAT-06).

### Phase 9b — Remediation Sprint

**Purpose:** Resolve all P0/P1 findings from the CAR before any freeze gate is opened.  
**Inputs:** CAR Report, Remediation Backlog.  
**Outputs:** Corrected implementation. Updated audit report.  
**Exit criteria:** Zero P0/P1 open findings. Zero Forbidden technical debt. All corrections registered in Technical Debt Register.

### Phase 9c — Pattern Extraction

**Purpose:** Extract, name, document, and freeze engineering patterns identified during CAR that recurred ≥ 2 times in independent construction contexts.  
**Inputs:** CAR Pattern Candidates, V1.2-PATTERN-FREEZE.md, Playbook §N.  
**Outputs:** New named patterns registered in V1.2-PATTERN-FREEZE.md. Playbook §N updated. Manifest Pattern Registry updated.  
**Exit criteria:** All accepted patterns documented with full structure. Cross-reference map updated. Methodology Evolution section updated.

### Phase 10 — Documentation Freeze

**Purpose:** Ensure all documentation reflects the final shipped state.  
**Inputs:** Audit-clean implementation, TDS, INDEX, ADRs, CAR Report, Pattern Freeze.  
**Outputs:** Updated TDS sections, INDEX freeze table updates, README updates (if applicable).  
**Exit criteria:** Every frozen component documented in INDEX. Every new ADR registered. TDS reflects actual shipped architecture. Pattern Freeze registered.

### Phase 11 — Release Candidate

**Purpose:** Create a stable, certifiable snapshot. No features after this point.  
**Inputs:** Documentation-frozen codebase.  
**Outputs:** RC tag, certification audit, regression suite results.  
**Exit criteria:** RC certification audit passes. Regression suite passes. All acceptance criteria satisfied. All Forbidden debt absent.

### Phase 12 — Stable Release

**Purpose:** Publish the certified version.  
**Inputs:** Certified RC.  
**Outputs:** Stable version tag, release notes, changelog, README update.  
**Exit criteria:** Stable tag applied. VERSION file updated. Repository baseline established.

### Phase 13 — Maintenance

**Purpose:** Operate the stable version safely.  
**Inputs:** Stable release.  
**Outputs:** Bug fixes only. No new features. No contract changes.  
**Exit criteria:** No outstanding Forbidden debt. All reported defects triaged.

### Phase 14 — Next Version

**Purpose:** Open the next version development cycle on the frozen baseline of the current version.  
**Inputs:** Stable release, V1.2 reserved extension points (ADRs).  
**Outputs:** New version scope, new TDS sections, new ADRs starting from the next available number.  
**Exit criteria:** New version kickoff documented. Previous version baseline locked.

---

## Section C — Milestone Workflow

Every milestone follows this exact sequence. The sequence is non-negotiable.

### Mandatory Sequence

```
1. Architecture review
        ↓
2. Contract definition
        ↓
3. ADR updates
        ↓
4. Implementation
        ↓
5. Unit testing
        ↓
6. Integration testing
        ↓
7. Audit
        ↓
8. Documentation update
        ↓
9. Freeze
        ↓
10. Certification
```

### Why the Order Must Never Change

**Step 1 before Step 4:** Implementation that precedes architecture produces systems that cannot be reasoned about. Architecture is cheap to change on paper. Code is expensive to change.

**Step 2 before Step 4:** A service that starts implementing before its contract is frozen implicitly defines the contract through its convenience. This produces contracts that serve the implementation, not the domain.

**Step 3 before Step 4:** An ADR written after implementation is post-hoc rationalization. The reasoning was present when the decision was made. Recording it afterward introduces selective memory and omits rejected alternatives.

**Step 7 before Step 9:** The audit must evaluate a complete implementation. Freezing before audit means accepting unknown violations into the stable contract. This is not recoverable without breaking the freeze.

**Step 9 before Step 10:** Certification evaluates a stable target. A codebase that is still changing during certification cannot be certified. The certification result would be invalid the moment the next change is applied.

---

## Section D — Prompt Engineering Workflow

Every prompt used in AI-assisted development has a defined purpose and mandatory sections.

### Planning Prompts

**Purpose:** Produce an architecture or design proposal for human review.

Mandatory sections:
- Problem statement (what needs to be designed)
- Existing context (frozen contracts, relevant ADRs, TDS references)
- Constraints (what cannot change, what is reserved)
- Expected output (architecture diagram, TDS section draft, ADR candidates)
- Success criteria (how the human will evaluate the proposal)

### Implementation Prompts

**Purpose:** Produce implementation code against a frozen architecture.

Mandatory sections:
- Architecture reference (TDS section, accepted ADRs)
- Frozen contract references (exact contract file paths)
- Implementation scope (exactly what to implement — not more)
- Exclusions (what not to touch, reserved extension points)
- Quality requirements (file size limits, coverage requirements, layering rules)

### Audit Prompts

**Purpose:** Verify structural correctness of a completed implementation.

Mandatory sections:
- Audit scope (files, components, or milestone boundaries to audit)
- Audit checklist (layering, ownership, configuration SSOT, contract compliance, technical debt)
- Severity classification criteria (Forbidden / Accepted / Deferred)
- Expected output format (finding ID, severity, location, resolution)

### Freeze Prompts

**Purpose:** Document the current frozen state into INDEX and TDS.

Mandatory sections:
- Components being frozen (names, file paths)
- Frozen API surface (public method signatures)
- INDEX update target (table name, row format)
- Version number and date

### Certification Prompts

**Purpose:** Validate that a Release Candidate satisfies all acceptance criteria.

Mandatory sections:
- Acceptance document reference (milestone-specific acceptance file)
- Test results (total, passed, failed, skipped)
- Audit status (all findings resolved or registered)
- Frozen component list (confirmed against INDEX)
- Forbidden debt check (must be zero)

### Release Prompts

**Purpose:** Produce release artefacts (VERSION, README, release notes).

Mandatory sections:
- Version number
- Milestone summary (what was shipped)
- Technical debt snapshot (Accepted, Deferred, Forbidden — must be zero)
- ADR count
- Test count

---

## Section E — ADR Workflow

### When an ADR Is Required

- Any architectural decision that is not obvious from the code alone.
- Any deviation from the Platform Engineering Manifest principles.
- Any decision to defer a feature or contract to a future milestone.
- Any decision to deprecate a component or contract.
- Any decision that introduces a new extension point or reserves a future capability.
- Any decision that affects a frozen contract (even if the change is backward-compatible).
- Any decision that introduces a new file-size boundary, performance budget, or coverage standard.

### When an ADR Is NOT Required

- Renaming an internal variable within a component's own scope.
- Adding a new test for an existing contract.
- Fixing a bug that does not change any documented behaviour.
- Documentation-only changes.
- Configuration value changes within an already-documented governance threshold file.

### ADR Lifecycle

| Status | Meaning |
|---|---|
| **Proposed** | ADR is written and under review. Implementation may not begin. |
| **Accepted** | ADR is approved. Implementation may begin against this decision. |
| **Superseded** | ADR was accepted but a later decision replaces it. Reference the superseding ADR. |
| **Deprecated** | ADR was accepted but the component or decision it governs is being phased out. |
| **Reserved** | ADR records an architectural reservation for a future milestone. No implementation until explicitly activated. |

### Relationship with Milestones

Every milestone boundary must be accompanied by:
- All new ADRs for that milestone in Accepted status.
- No Proposed ADRs that affect that milestone's scope.
- ADRs for deferred work in Reserved or Accepted (with target milestone noted).

ADRs are numbered sequentially from the last registered number. No gaps. No reuse of deprecated ADR numbers.

---

## Section F — Architecture Reviews

### When to Perform

- At the start of every new milestone.
- Before any new subsystem is designed.
- When an existing subsystem is extended in a way that touches frozen contracts.
- After an audit identifies architectural violations.

### Required Checks

1. **Layering compliance** — domain has no imports from services, app, or infrastructure.
2. **Ownership correctness** — every mutable domain object has exactly one writer.
3. **Dependency direction** — all dependencies point inward (toward domain). No domain-to-infrastructure imports.
4. **Contract completeness** — all cross-boundary interactions are defined by Pydantic contracts with `extra=forbid`.
5. **Extension point compliance** — new components use reserved extension points (not ad-hoc additions to frozen contracts).
6. **Configuration SSOT** — no governance threshold hardcoded outside designated configuration files.
7. **Determinism** — new reasoning components produce deterministic output.
8. **Plugin architecture** — new detectors implement `PatternDetector` ABC and do not modify the core pipeline.

### Severity Levels

| Severity | Definition | Release Impact |
|---|---|---|
| **P0 — Blocking** | Correctness defect in hire decision, evidence, or frozen contract | Blocks release. Must be fixed before freeze. |
| **P1 — High** | Layering violation, circular dependency in production path, SSOT violation | Must be resolved before freeze or registered as Accepted with target milestone. |
| **P2 — Medium** | Missing documentation, test coverage gap, deferred extension point | Must be registered in Technical Debt Register. |
| **P3 — Low** | Style inconsistency, non-critical technical debt | Registered in Technical Debt Register with low priority. |

### Go / No-Go Criteria

**Go:**
- Zero P0 findings.
- All P1 findings either resolved or registered as Accepted technical debt with a target milestone.
- All ADRs for this milestone are in Accepted status.

**No-Go:**
- Any P0 finding present.
- Any Forbidden technical debt present.
- Any Proposed ADR that blocks implementation.

---

## Section G — Technical Debt Workflow

### Identification

Technical debt is identified during:
- Architecture reviews.
- Milestone audit phases.
- Implementation (when a known shortcut is taken for scope reasons).
- Certification (when a pre-existing issue is rediscovered).

### Classification

| Category | Criteria |
|---|---|
| **Accepted** | No observable production impact. Registered with ID, severity, location, target milestone. Does not affect governance decisions. |
| **Deferred** | Fix requires an architectural change scoped to the next major version. Governed by an ADR. Has a concrete target milestone. |
| **Forbidden** | Affects hire decision correctness, frozen contract integrity, determinism, or bypasses a validation layer. Blocks release. |

### Registration

All debt is registered in the Technical Debt Register (INDEX.md or dedicated section) with:
- ID (TD-NNN)
- Item description
- Severity (P0–P3)
- Reason for deferral
- Target milestone
- Governing ADR (if applicable)

### Acceptance

Accepting technical debt is an explicit engineering decision, not an oversight. It requires:
- Human review and sign-off.
- Registration in the Technical Debt Register.
- Confirmation that the item is not Forbidden.

### Planning

Deferred and Accepted debt is reviewed at the start of each new milestone. Items whose target milestone has been reached are prioritised for resolution before new feature work.

### Removal

Technical debt is removed by:
- Implementing the fix in the target milestone.
- Updating the Technical Debt Register status to Closed.
- Referencing the resolution in the relevant INDEX update.

### Release Impact

- Zero Forbidden debt: required for any Release Candidate.
- Accepted and Deferred debt: must be registered. Count reported in release notes.
- Closed debt: documented in the milestone summary.

---

## Section H — Testing Strategy

### Philosophy

Every component is independently testable. No test requires a running LLM. Deterministic services are tested with real inputs — not mocks. Non-deterministic services are tested with contract-level stubs.

### Unit Tests

- Every public method of every service has unit test coverage.
- Detector tests: minimum 5 scenarios per detector (per ADR-060).
- Guard tests: all 17 rules covered.
- Contract tests: `extra=forbid` violation tests included.
- All unit tests run in isolation without database, LLM, or external service dependencies.

### Integration Tests

- Every graph node is tested in pipeline context.
- Every cross-component interaction (e.g., EvaluationSignalWriter → EvidenceStore → EvaluationSignalDetector) is tested end-to-end.
- Same-cycle visibility contracts are integration-tested.
- Registry execution order is integration-tested.

### Regression Tests

- Run on every Release Candidate.
- Full test suite must pass with zero failures before RC certification.
- Regression baseline is established at each stable release.

### Audit Scenarios

- Layering violation tests: verify that domain modules do not import from services or app.
- Configuration SSOT tests: verify that no governance threshold is hardcoded outside designated files.
- Idempotency tests: verify that append-only structures do not accept duplicate writes.

### Performance Tests

- Detector pipeline execution time validated against ADR-054 budget.
- No test introduces a timing dependency that would cause flakiness.

### Release Validation

Before every Release Candidate:
- Full test suite: all tests pass.
- No newly introduced test failures.
- Coverage of the core reasoning path confirmed.
- All acceptance criteria verified against the milestone acceptance document.

---

## Section I — Release Workflow

### Complete Sequence

```
Development (active implementation)
        ↓
Freeze (API freeze, contract freeze, feature flag lock)
        ↓
Release Candidate (certification audit, regression suite, acceptance gates)
        ↓
Bug Fix Only (no features, no contract changes after RC tag)
        ↓
Stable Release (tag, release notes, changelog)
        ↓
Baseline (VERSION locked, INDEX frozen, TDS updated)
        ↓
Next Version (new version opens on main after stable merge)
```

### Freeze Checklist

- [ ] All milestone ADRs are in Accepted status.
- [ ] All public APIs documented in INDEX freeze table.
- [ ] All contracts frozen with `extra=forbid` confirmed.
- [ ] All feature flags reviewed — no unintended production-on defaults.
- [ ] Technical Debt Register updated — all new findings registered.
- [ ] No Forbidden debt present.

### RC Checklist

- [ ] Full test suite passes (zero failures).
- [ ] Certification audit passes — no P0 findings.
- [ ] All milestone acceptance criteria satisfied.
- [ ] TDS updated to reflect shipped architecture.
- [ ] INDEX frozen state tables accurate.
- [ ] VERSION file updated to RC value.

### Stable Release Checklist

- [ ] RC certification passed.
- [ ] No post-freeze features introduced.
- [ ] Stable tag applied.
- [ ] VERSION updated to stable value.
- [ ] README updated.
- [ ] Release notes written (milestone summary, ADR count, test count, debt snapshot).

### Baseline Checklist

- [ ] Stable tag committed.
- [ ] All deferred items have target milestones confirmed for next version.
- [ ] Next version ADR numbering established (continue from last registered ADR + 1).
- [ ] New version development branch opened.

---

## Section J — AI Collaboration Workflow

### Human Responsibilities

- Define architecture before any AI-generated implementation is accepted.
- Review all AI-generated contracts before they are used as implementation inputs.
- Approve all ADRs. ADRs are never AI-authored without human review and explicit approval.
- Reject AI-generated code that assumes an unreviewed architecture.
- Perform all milestone-boundary decisions (freeze, certification, release).
- Maintain the Technical Debt Register with human judgment.

### AI Responsibilities

- Generate implementation candidates against frozen contracts and accepted ADRs.
- Identify consistency violations and layering issues in proposed designs.
- Produce audit reports against provided checklists.
- Generate documentation drafts for human review.
- Accelerate iteration by producing multiple design alternatives for human evaluation.

### Verification Process

Every AI-generated output is verified by the human engineer before it is accepted:
- Implementation: verified against frozen contracts, accepted ADRs, and audit checklist.
- Architecture proposals: reviewed against Manifest principles and existing frozen contracts.
- Audit reports: reviewed for completeness and severity classification accuracy.
- Documentation updates: reviewed for accuracy against the actual shipped state.

### Evidence-Driven Development

No architectural decision is made on intuition. Every decision requires:
- Analysis of the existing system state.
- Reference to the requirements of the current milestone.
- Analysis of the constraints imposed by frozen contracts.
- Consideration of at least two alternatives (documented in the ADR).

### Iterative Refinement

Complex subsystems are built iteratively:
1. Design proposal → human review → refinement.
2. Contract draft → human review → freeze.
3. Implementation → audit → fix → re-audit (if necessary).
4. No subsystem is generated in a single pass.

### Prompt Evolution

Prompts improve over time. After every milestone:
- Review which prompts produced high-quality outputs.
- Identify where prompts produced outputs that required significant human correction.
- Update the prompt templates in Section D accordingly.
- Document the evolution rationale.

---

## Section K — Engineering Checklists

### Feature Milestone Checklist

- [ ] Architecture review complete. No P0/P1 blockers.
- [ ] All cross-boundary contracts defined (`extra=forbid`).
- [ ] All relevant ADRs in Accepted status.
- [ ] Implementation complete and satisfies contracts.
- [ ] Unit tests pass (coverage per ADR-060).
- [ ] Integration tests pass.
- [ ] Audit complete. No Forbidden debt.
- [ ] Technical Debt Register updated.
- [ ] TDS section updated.
- [ ] INDEX updated (frozen components, ADRs).
- [ ] Freeze confirmed.

### Detector Milestone Checklist

- [ ] Detector responsibility defined (single responsibility).
- [ ] Evidence types consumed and produced documented.
- [ ] Priority in execution order assigned (ADR-049).
- [ ] New EvidenceType entries added to domain catalog (if required).
- [ ] ADR filed for detector design and responsibility matrix position.
- [ ] `PatternDetector` ABC implemented.
- [ ] Detector registered in `default_registry.py`.
- [ ] Unit tests: ≥ 5 scenarios (per ADR-060).
- [ ] Performance budget validated (per ADR-054).
- [ ] File size within limit (per ADR-056).
- [ ] Integration test: pipeline execution order verified.
- [ ] Detector catalog in INDEX updated.

### Architecture Milestone Checklist

- [ ] TDS new section drafted.
- [ ] Architecture review performed against Manifest principles.
- [ ] All P0/P1 findings resolved.
- [ ] Contracts defined for all new component boundaries.
- [ ] ADRs registered for all significant decisions.
- [ ] Extension points documented and reserved (if V1.2 scope).
- [ ] Technical Debt Register updated for any accepted architectural shortcuts.

### Audit Milestone Checklist

- [ ] Layering compliance verified (domain imports checked).
- [ ] Ownership correctness verified (single writer per mutable object).
- [ ] Configuration SSOT verified (no hardcoded governance thresholds).
- [ ] Contract compliance verified (`extra=forbid`, `schema_version`).
- [ ] Append-only structure integrity verified (EvidenceStore, ReasoningHistory).
- [ ] All findings classified by severity.
- [ ] All P0 findings resolved.
- [ ] Technical Debt Register updated.

### Documentation Milestone Checklist

- [ ] TDS reflects shipped architecture (no documentation-code divergence).
- [ ] INDEX frozen state tables accurate and complete.
- [ ] All new ADRs registered in INDEX.
- [ ] Technical Debt Register complete and current.
- [ ] No undocumented frozen components.
- [ ] README current (if stable release).

### Release Milestone Checklist

- [ ] Freeze checklist complete.
- [ ] RC checklist complete.
- [ ] Stable release checklist complete.
- [ ] Baseline checklist complete.
- [ ] VERSION file at correct stable value.
- [ ] Next version ADR numbering confirmed.

---

## Section L — Lessons Learned from V1.1

These lessons are drawn from the V1.1 engineering process. They are process lessons, not implementation lessons.

### Architecture Before Implementation

The most expensive mistakes in V1.1 were made when implementation began before architecture was fully reviewed. Every instance where the architecture was reviewed first produced cleaner contracts, fewer ADRs, and fewer audit findings.

**Rule established:** Architecture review is gate zero. No milestone begins implementation without a completed architecture review.

### Small Components

Services that accumulated multiple responsibilities required decomposition mid-milestone. Decomposition during implementation is more expensive than decomposition during design.

**Rule established:** File size limit of 200 lines is a design signal, not a cosmetic constraint. Files approaching the limit during design are a warning to decompose before implementation.

### Contracts First

In milestones where contracts were defined first, implementation proceeded without ambiguity. In milestones where contracts were inferred from implementation, the contracts required revision post-implementation — which forced test rewrites.

**Rule established:** No implementation file is created before the contract it implements is reviewed and frozen.

### Freeze Discipline

The value of a freeze is its absoluteness. Any exception creates a precedent that erodes the freeze boundary. Post-freeze changes that appeared minor required re-audit and re-certification.

**Rule established:** After freeze, no new features, no new contracts, no new ADRs unless a genuine defect is discovered in already-frozen behaviour.

### Audit Discipline

Milestones that skipped or abbreviated the audit phase produced frozen states that contained P1 technical debt that was discovered in the next milestone. Discovering debt in a later milestone is more expensive than discovering it in the current one.

**Rule established:** Audit is not optional. No milestone proceeds to freeze without a completed audit.

### Plugin Architecture

The detector registry pattern (ADR-051) eliminated the need to modify the core pipeline when adding new detectors. The lesson was that plugin architecture must be designed upfront — retrofitting it is expensive.

**Rule established:** Every extensible subsystem defines its plugin contract before the first implementation of the plugin type.

### Extension Points

V1.1 ADRs that reserved V1.2 extension points (ProfileFeature, ObservationModel, NarrativeGenerator) eliminated the risk of V1.2 work requiring V1.1 contract changes. The cost of defining a reservation is negligible. The cost of missing one is a breaking change.

**Rule established:** Every milestone must explicitly identify what the next milestone will need to extend and reserve those extension points in current-milestone ADRs.

### Backward Compatibility

Every post-freeze modification that attempted to change a frozen contract required a new ADR and a deprecation plan. The lesson: frozen means frozen. Design for extensibility upfront rather than treating freeze as a starting point for negotiation.

**Rule established:** Additive-only evolution after freeze. Breaking changes require a new major version.

### Technical Debt Honesty

Technical debt that was not registered was discovered during later audits at higher cost. Registered debt was predictable and plannable. The act of registration forced the team to confront debt explicitly rather than hoping it would be resolved "naturally."

**Rule established:** Any known shortcut taken during implementation is registered immediately — not at the next audit.

---

## Section M — Reuse Across Projects

This Playbook is intentionally designed to be independent of the AI Interview Simulator's specific domain. The workflow, checklists, and principles apply to any enterprise software project.

### AI Platforms

For AI platforms (RAG systems, coding agents, decision support systems):
- Replace `PatternDetector` with the platform's extension mechanism.
- Apply the same ADR workflow for any LLM integration decision.
- Apply the Manifest principle "LLMs are assistants, never decision-makers" universally.
- Replace `EvidenceStore` with the platform's evidence or memory structure.

### RAG Systems

- The same "contracts before code" discipline applies to retrieval pipeline components.
- Chunking strategies, embedding providers, and retrieval policies are all ADR-worthy decisions.
- The plugin architecture principle applies to embedding providers and retrieval strategies.

### Coding Agents

- The same milestone workflow applies.
- Tool call contracts are equivalent to `PatternDetector` contracts.
- Agent memory structures are equivalent to `InterviewMemory`.

### Decision Support Systems

- Evidence-driven reasoning (Section G of the Manifest) is universally applicable.
- Every decision that affects a user-facing outcome must be traceable to typed evidence.
- No qualitative judgment without a supporting evidence trail.

### Enterprise SaaS

- The release workflow (Freeze → RC → Stable → Baseline) applies directly.
- The Technical Debt Policy (Accepted / Deferred / Forbidden) applies with domain-specific forbidden categories.
- The AI Collaboration Workflow applies unchanged.

### General Backend Platforms

- Domain-Driven Design principles apply to any bounded context.
- Single Writer Principle applies to any mutable aggregate.
- Configuration SSOT principle applies to any governance threshold.

### How to Adapt

1. Replace domain-specific component names with the new project's equivalents.
2. Retain all workflow sequences, checklists, and lifecycle phases unchanged.
3. Define the new project's equivalent of "Forbidden Technical Debt" based on what decisions affect user-facing correctness.
4. Establish the new project's ADR numbering from ADR-001.
5. Create the new project's Manifest and Playbook on day one — before any implementation.

---

## Section N — Engineering Pattern Registry

Engineering patterns are named, reusable practices that emerge from construction and are formally recorded after acceptance. They are not new architecture — they are implementations of existing Manifest principles, named for reuse and discoverability.

### Pattern Catalogue (V1.2)

Full documentation for all patterns lives in `V1.2-PATTERN-FREEZE.md`.

| ID | Name | When to Apply | Manifest Principle |
|---|---|---|---|
| **PAT-01** | Engine Five-Artifact Pattern | Any domain engine with composable transformations and a persistent output aggregate | Small components; Composition over inheritance; Single Writer |
| **PAT-02** | Runtime First, Orchestration Second | Any milestone sequence where an engine has both a runtime contract and a wiring/orchestration contract | Contracts before Code |
| **PAT-03** | Construction Parallelism Review (CPR) | Before any construction phase with ≥ 3 Epics or cross-Epic dependencies | Architecture before Implementation; Progressive Evolution |
| **PAT-04** | Temporary Construction Placeholder (TCP) | When a future-milestone capability requires a schema field that has no V1.x behaviour | Progressive Evolution; Backward Compatibility; Immutability |
| **PAT-05** | Builder-only Construction | When a domain object requires invariant validation during construction and multiple callers exist | Single Writer Principle; Single Responsibility |
| **PAT-06** | Single Runtime Orchestrator | Always active. Any component coordinating multiple services at workflow level violates this pattern | Runtime Ownership; Single Writer Principle |

### Pattern Lifecycle

| Stage | Definition |
|---|---|
| **Observed** | Pattern is applied in construction but not yet named or documented |
| **Proposed** | Pattern is named and a documentation draft is circulated |
| **Accepted** | Pattern is reviewed, formally documented, and registered in this section |
| **Deprecated** | Pattern has been superseded by a newer pattern or a Manifest principle update |

Patterns are accepted by the human architect. AI tooling may propose patterns; it does not accept them.

### Adding a New Pattern

1. Observe the pattern recurring in ≥ 2 independent construction contexts.
2. Name it. A pattern without a name cannot be referenced or enforced.
3. Draft the documentation: Purpose, Motivation, Responsibilities, Benefits, When to use, When NOT to use, ADR relationships, Examples.
4. Review against existing Manifest principles — ensure the pattern implements, not contradicts, them.
5. Register in `V1.2-PATTERN-FREEZE.md` (or the relevant version's pattern freeze document).
6. Add to the catalogue table in this Section N.
7. Update the Pattern Registry in the Manifest.

### What Patterns Are NOT

- Patterns are not ADRs. ADRs record architectural decisions. Patterns record reusable construction practices.
- Patterns are not new architecture. If a pattern introduces new components or contract boundaries, it requires an ADR.
- Patterns are not optional guidelines. An accepted pattern is the default practice. Deviating from an accepted pattern requires explicit justification documented in the relevant milestone ADR or audit report.

---

## Section O — Construction Architecture Review (CAR)

The CAR is a mandatory engineering activity that occurs after a construction phase and before the freeze gate. It is the primary mechanism for discovering PAT-06 violations (second runtime orchestrators), PAT-05 violations (duplicated construction paths), and other structural regressions that emerge during implementation.

### CAR Checklist

- [ ] Runtime ownership verified: exactly one runtime orchestrator present (LangGraph). No second orchestrator. (PAT-06)
- [ ] Builder-only construction verified: every domain object with invariants has exactly one builder. (PAT-05)
- [ ] Single writer verified per mutable aggregate: no second writer introduced during construction.
- [ ] No service-to-service workflow coordination: services are stateless with respect to workflow.
- [ ] All P0/P1 audit findings from Phase 9 are captured and classified.
- [ ] Pattern candidates identified: recurring structures that appeared ≥ 2 times.
- [ ] CAR Report issued and registered in INDEX.

### CAR Findings Classification

| Classification | Meaning | Required Action |
|---|---|---|
| **P0** | Second runtime orchestrator; correctness defect | Must resolve before any freeze gate |
| **P1** | Duplicated construction path; second writer; hidden coupling | Must resolve or register as Accepted with target milestone |
| **P2** | Missing pattern documentation; coverage gap | Register in Technical Debt Register |
| **P3** | Style inconsistency; non-critical structural issue | Register; low priority |

### Thin Orchestrator Rule

A LangGraph node that calls application services is a Thin Orchestrator: it coordinates business capabilities but does not own any business logic itself. A Thin Orchestrator is the correct design. A node that contains business logic is a design violation (move logic to the service). A service that coordinates other services is a second orchestrator violation (move coordination to the node).

---

## Section P — Methodology Evolution

The engineering methodology of this project evolves from implementation experience. This section documents how that evolution occurs and what has changed across versions.

### How New Methodology Is Produced

```
Observation (something recurring is noticed during construction)
    ↓
Repeated occurrence (≥ 2 independent contexts)
    ↓
Engineering Pattern (named, extracted via Phase 9c Pattern Extraction)
    ↓
Pattern Freeze (registered in V1.2-PATTERN-FREEZE.md)
    ↓
Methodology (codified in this Playbook and the Manifest)
    ↓
Baseline (default practice for the next construction sprint)
```

### Methodology History

| Version | Methodology Addition |
|---|---|
| V1.1 | Manifest and Playbook established. Lessons from V1.1 construction codified (§L). |
| V1.2 DOC-M1 | PAT-01 to PAT-04 extracted and frozen. Section N (Engineering Pattern Registry) added. |
| V1.2 RC-C | PAT-05 and PAT-06 extracted and frozen. CAR formalised (§O). Pattern Extraction formalised (§B Phase 9c). Runtime Ownership added to Manifest. Methodology Evolution documented (this section). |

### Methodology Principles

- Methodology is discovered, not imposed. No practice is codified before it has proven its value.
- A pattern that appears only once is an observation, not a rule.
- Patterns that contradict Manifest principles are not extracted — the implementation is corrected.
- The human architect accepts patterns. AI tooling may propose candidates.

---

## Document History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-01 | Initial Playbook — V1.1 RC foundation |
| 1.1 | 2026-07-02 | DOC-M1 Pattern Freeze: Section N (Engineering Pattern Registry) added; PAT-01 to PAT-04 registered |
| 1.2 | 2026-07-03 | RC-C Methodology Freeze: PAT-05 and PAT-06 added to §N; CAR added to §B lifecycle (Phase 9a–9c) and formalised in §O; Methodology Evolution documented in §P; Thin Orchestrator rule added to §O |
