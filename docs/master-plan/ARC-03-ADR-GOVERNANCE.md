# ARC-03 — ADR Governance

**Version 1.0 | Architectural Decision Record Lifecycle and Management**

---

## Purpose

An Architecture Decision Record (ADR) is the authoritative written record of a significant architectural decision: what was decided, why it was decided, what alternatives were rejected, and what consequences follow. ADRs do not record discussions, exploratory thinking, or feature specifications. They record decisions — specifically, decisions whose implications outlast the sprint in which they were made.

ADRs serve three audiences. For the current team, they eliminate the need to rediscover why a constraint exists. For future maintainers, they provide the reasoning chain behind the architecture they inherit. For the architecture review process, they provide the evidence base against which new proposals are evaluated.

### Relationship to Other Governance Documents

ADRs exist within a governance hierarchy. Each layer is subordinate to the one above it.

```
Architecture Constitution          (non-negotiable principles)
        ↓
Architecture Review Checklist      (operational verification)
        ↓
Architecture Decision Records      (specific binding decisions)
        ↓
Pattern Application Tracking       (implementation conventions)
        ↓
Implementation
```

The Architecture Constitution defines what may never be violated. ADRs define how the platform is built within those boundaries. An ADR may not contradict the Constitution. When a proposed ADR appears to require a constitutional exception, the constitutional boundary must be formally crossed via an explicit Architecture Review before the ADR is accepted.

ADRs record decisions, not their implementations. An ADR that describes how code is structured is an implementation specification, not an architectural decision. The distinction matters: implementation specifications belong in code, comments, and technical documentation. ADRs belong in the governance layer.

---

## ADR Lifecycle

Every ADR passes through a defined sequence of states. State transitions are explicit and require documented justification. An ADR in any state other than Draft or Proposed is considered part of the permanent architectural record and must not be silently modified.

### Draft

The ADR has been initiated but is not yet ready for review. The author is clarifying the problem, gathering context, and evaluating alternatives. A Draft ADR has no binding force. It may be abandoned without ceremony.

### Proposed

The author considers the ADR complete and submits it for architectural review. A Proposed ADR has undergone at least an internal consistency check by the author. The problem is clearly stated, at least two alternatives have been considered, and the consequences section is populated. Submission for review is the transition from Draft to Proposed.

### Under Review

An Architecture Review is in progress. The reviewers are applying ARC-02 and verifying constitutional compliance, ADR consistency, PAT alignment, and testing implications. No implementation work related to the decision may begin while the ADR is Under Review, unless explicitly authorized by the review body as a low-risk prerequisite.

### Accepted

The review body has approved the ADR. The decision is binding. Implementation may begin. The ADR text is frozen: it may receive minor clarifications (see §ADR Versioning) but may not be substantively revised without re-entering the review process. An Accepted ADR that is not yet implemented is a commitment, not an aspiration.

### Implemented

The decision described in the ADR is fully reflected in production code. All testing requirements stated in the ADR have been satisfied. The ADR is annotated with the version or release at which implementation was completed. This state is informational — it confirms closure of the implementation commitment.

### Superseded

A later ADR replaces this ADR's decision. The superseding ADR is referenced in this record. The superseded ADR is preserved in full — it is never deleted. Its historical record, including the reasoning that led to the original decision, remains accessible. A Superseded ADR has no binding force, but its existence explains why the superseding ADR was necessary.

### Deprecated

The decision in this ADR is no longer relevant to the current platform but has not been formally replaced by a superseding ADR. Deprecation occurs when the subject of the decision has been removed from the platform entirely (the artifact, pipeline, or pattern no longer exists), making the ADR's constraints moot. A Deprecated ADR carries a deprecation note explaining why it is no longer applicable.

### Retired

The ADR is removed from the active governance set. Retirement is appropriate only for Superseded or Deprecated ADRs that have been inactive for at least one major release cycle and whose content no longer informs any current decision. Retired ADRs are archived, not deleted. Retirement requires explicit approval from the review body.

---

## When an ADR Is Required

### Situations That Require an ADR

An ADR is required before implementation when the proposed change:

- introduces a new runtime artifact type into the platform (a new class of domain contract, not a new instance of an existing class)
- transfers or splits the ownership of an existing artifact between components
- introduces a new production pipeline or adds a new stage to an existing pipeline that crosses a constitutional boundary
- modifies the schema of an immutable domain contract in a way that affects downstream consumers or historical reconstruction
- changes the sole-writer assignment for any `InterviewState` field
- introduces a new Builder as the sole construction path for an artifact
- introduces a new Engine with novel computational responsibility
- changes the orchestration topology of the runtime graph
- introduces a new node into the runtime graph
- extends, modifies, or crosses the Replay Boundary
- introduces a compatibility bridge between two representations of the same concept
- changes the routing signal or entry condition for any major presentation state
- introduces a new pattern that is intended to become a platform convention
- supersedes, extends, or formally contradicts an existing Accepted ADR

### Situations That Do Not Require an ADR

An ADR is not required when the change:

- adds a new concrete implementation of an existing, well-defined interface (e.g., a new `FeatureUpdater` that follows all existing conventions)
- adds fields to an existing contract in a backward-compatible, additive way that does not affect ownership or reconstruction
- refactors the internal implementation of a component without changing its contract, ownership, or observable behavior
- adds, removes, or reorganises test coverage without touching production code
- corrects a defect in production code where the correct behavior is unambiguous from existing ADRs and patterns
- introduces tooling, infrastructure, or deployment configuration changes that do not affect the runtime architecture

When in doubt, the reviewer should consult the Architecture Review Checklist (ARC-02). If any checklist item in sections A through F applies to the change, an ADR is likely required.

---

## ADR Structure

Every ADR must contain the following sections. Sections may be brief when the content is simple, but none may be omitted. An ADR that omits a required section is not complete and may not be submitted for review.

### ADR Identifier and Title

A stable, sequential identifier (e.g., ADR-053) and a concise title that names the decision, not the problem. The title should complete the sentence "We decided to…" without requiring the body to be read.

### Status

The current lifecycle state: Draft, Proposed, Under Review, Accepted, Implemented, Superseded, Deprecated, or Retired. If Superseded, reference the superseding ADR. If Implemented, reference the release version.

### Context

The architectural situation that makes this decision necessary. Context is descriptive, not prescriptive. It describes the current state of the platform, the constraints in force, and the forces at work. The context section must be written as if the reader has no prior knowledge of the current sprint's work.

### Problem

A precise statement of the architectural problem being solved. One paragraph. The problem must be stated in terms of architectural correctness, ownership, immutability, or constitutional compliance — not in terms of feature requirements, performance goals, or implementation preferences. A problem statement that cannot be expressed in architectural terms suggests the proposal may not require an ADR.

### Decision

A clear, affirmative statement of what was decided. One to three paragraphs. The decision must be stated as a constraint — what the platform will do, will not do, or must always do as a result of this ADR. Vague decisions ("we will aim to…", "where possible…") are not acceptable. The decision must be verifiable: a future reviewer must be able to determine unambiguously whether production code complies with it.

### Alternatives Considered

A structured list of alternatives that were evaluated and rejected. For each alternative: a brief description, the reason it was rejected, and any tradeoffs that made rejection non-trivial. A minimum of two alternatives must be documented. An ADR with no alternatives considered is a declaration of foregone conclusion, not an architectural decision.

### Consequences

The binding constraints that follow from the decision. What becomes true. What becomes false. What is now required. What is now prohibited. Consequences must be stated at the architectural level — not as implementation tasks. A consequence such as "all future Builders must conform to this interface" is architectural. A consequence such as "update the `build()` method in `ReportBuilder`" is an implementation task and belongs in a ticket, not in an ADR.

### Tradeoffs

The costs accepted in exchange for the benefits of the decision. Every architectural decision accepts a tradeoff. An ADR that lists only benefits has not been fully reasoned. The tradeoff section acknowledges what is made harder, more constrained, or more expensive by this decision. It does not reverse the decision — it contextualizes it.

### Impact

The artifact types, nodes, pipelines, and patterns directly affected by this decision. A brief enumeration, not a detailed implementation plan. Future readers must be able to determine at a glance which parts of the system are governed by this ADR.

### Compatibility

The backward compatibility implications of this decision. Does this ADR break existing contracts? Does it require migration? Does it affect closed historical artifacts (replay implications)? Does it affect any currently Accepted ADR? If so, which ones, and how?

### Review Outcome

Populated after the Architecture Review. Records the review decision (Accepted, Rejected, Accepted with Actions), the names of the reviewers, the date of the decision, and any required actions that must be completed before or during implementation.

---

## ADR Review Process

The review of a Proposed ADR follows the sequence described below. Reviewers must apply each step independently — skipping to the conclusion without completing the sequence is not a valid review.

### Step 1 — Constitutional Compliance

Verify that the decision stated in the ADR does not contradict any principle in the Architecture Constitution. If the ADR requires crossing a constitutional boundary, verify that the crossing is explicitly acknowledged in the ADR's Consequences section and that the review body has authority to authorize the crossing.

### Step 2 — Architecture Review Checklist (ARC-02)

Apply the relevant sections of ARC-02 to the decision described in the ADR. An ADR that would fail any checklist item must address the failure in its Consequences or Tradeoffs section. If the ADR requires an explicit exception to a checklist requirement, the exception must be documented and justified.

### Step 3 — PAT Verification

Identify every official pattern (OP-01 through OP-06 and any subsequently ratified patterns) that applies to the decision. Verify that the ADR either conforms to these patterns or explicitly supersedes or extends them. An ADR that introduces a new convention without examining its relationship to existing patterns is incomplete.

### Step 4 — ADR Consistency

Identify every existing Accepted or Implemented ADR that is affected by this proposal. Verify that the new ADR does not silently contradict any existing ADR. If contradiction is unavoidable, the new ADR must explicitly declare which existing ADR it supersedes and why the prior decision is no longer valid.

### Step 5 — Replay Implications

Determine whether the decision affects the deterministic reconstruction contract. Any ADR that modifies an artifact included in `SessionHistory`, `CandidateProfileSnapshot`, or any closed artifact must evaluate whether historical replay remains valid. If replay is affected, the ADR must specify how replay compatibility is maintained or how the Replay Boundary is crossed.

### Step 6 — Testing Implications

Identify the ownership invariant tests, architectural guard tests, and behavioral tests that must be updated, created, or removed as a consequence of this ADR. The ADR's Review Outcome section must reference the testing requirements explicitly.

### Step 7 — Approval

The review body records the decision in the ADR's Review Outcome section and transitions the ADR to Accepted or returns it to Draft with documented reasons for rejection. An ADR is Accepted by the review body, not by the author. Self-approval is not a valid outcome.

---

## ADR Relationships

ADRs do not exist in isolation. They form a network of decisions that must be internally consistent.

### Referencing Earlier ADRs

An ADR may reference earlier ADRs to establish context, inherit constraints, or build on a prior decision. A reference is informational — it does not transfer binding force. A new ADR that references an older ADR is still independently evaluated.

### Superseding Earlier ADRs

When a new ADR replaces the decision of an earlier ADR, it must explicitly declare the supersession. The superseded ADR transitions to the Superseded state. The superseding ADR must explain why the prior decision is no longer valid — not merely that a new decision is preferred. Supersession is a significant architectural event and requires a full Architecture Review.

### Extending Earlier ADRs

When a new ADR adds constraints to an earlier ADR without replacing it, it is an extension. The earlier ADR remains Accepted and binding. The new ADR adds to its constraints. Both must remain consistent. If an extension produces an inconsistency in the extended ADR, the extension must be treated as a supersession.

### Independent ADRs

An ADR that addresses a new domain without touching the constraints of any existing ADR is independent. It must still pass constitutional compliance and the full review process, but it does not need to declare relationships to unrelated ADRs.

### Forbidden Dependency Patterns

An ADR may not declare itself as superseding another ADR that it does not actually address. Nominal supersession — marking an ADR as superseded to avoid the appearance of contradiction — is a governance violation. An ADR may not circularly depend on an ADR that depends on it. An ADR may not require the simultaneous acceptance of another Proposed ADR — each ADR must be independently viable.

---

## ADR Versioning

### Minor Clarification

An Accepted ADR may receive minor clarifications that correct typographical errors, improve the precision of language, or add examples that do not change the substance of the decision. Minor clarifications do not require a full review. They require acknowledgment by at least one reviewer and must be annotated with the date and nature of the clarification.

### Major Revision

A change to the substance of the decision, the alternatives considered, the consequences, or the tradeoffs is a major revision. A major revision returns the ADR to Proposed state and requires a full Architecture Review. The prior version is preserved as a dated snapshot within the ADR document.

### Superseded ADR

When a decision is replaced by a new ADR, the original ADR is frozen at its final Accepted text. It transitions to Superseded. The superseding ADR's identifier is recorded in the original. No further edits are made to the superseded document.

### Retired ADR

A Deprecated or Superseded ADR that has been inactive for at least one major release cycle may be retired. Retirement requires explicit review body approval. The ADR is moved to an archive section and annotated with the retirement date and reason.

### Immutability of Accepted ADRs

An Accepted ADR is the written record of a binding decision. Retroactive modification of substance without a formal review process is a governance violation. Future maintainers reading an Accepted ADR must be able to trust that the text reflects the decision as it was made, not as it has been quietly revised. This trust is the foundation of the ADR system's value.

---

## Architectural Stability

The ADR catalogue is an asset only if it remains coherent and navigable. An accumulation of redundant, conflicting, or superseded ADRs degrades the catalogue's value faster than it adds to it. The following principles govern ADR growth.

### Avoid Redundant ADRs

Before proposing a new ADR, verify that no existing Accepted or Implemented ADR already addresses the same decision. A new ADR that restates an existing one without superseding it creates ambiguity about which record governs. If the intent is to refine or clarify an existing ADR, a minor clarification or extension is preferable to a new record.

### Avoid Conflicting ADRs

The review process must actively check for conflicts with existing ADRs. A conflict between two Accepted ADRs is a governance failure. When a conflict is discovered, the review body must determine which ADR governs, document the resolution, and update one or both records accordingly.

### Prefer Technology-Neutral Statements

ADRs that bind the platform to specific technologies, frameworks, or library versions have a shorter useful life than ADRs that bind it to architectural principles. Where possible, state the constraint in terms of the behavior or contract required, not the specific tool that provides it. A technology-specific ADR should explain why the technology choice is itself the architectural decision, rather than merely a convenient implementation of a principle that could be stated more durably.

### Prefer Extension Over Duplication

When a new use case is substantially similar to an existing decided case, prefer extending the existing ADR to creating a new one. New ADRs should address genuinely new architectural questions. An ADR for each new artifact type, each new node, or each new pipeline stage produces a catalogue so large it becomes unusable. Apply the principle of minimum viable governance: the smallest number of ADRs that produces a coherent, enforceable architectural record.

---

## Common ADR Anti-Patterns

**Solution Without Problem.** The ADR describes a proposed implementation without stating the architectural problem that makes the decision necessary. A reviewer cannot evaluate whether the decision is correct without understanding the problem it solves. Detected by: the Problem section is absent, vague, or reframes the solution as the problem.

**Implementation Masquerading as Architecture.** The ADR specifies how code should be structured, which methods should be called, or which files should be created. Implementation decisions belong in code and technical documentation, not in ADRs. Detected by: the Decision section reads as a list of code changes rather than a binding architectural constraint.

**Duplicate ADR.** A new ADR is proposed that addresses a decision already governed by an existing Accepted ADR. The author was unaware of the existing record, or the existing record is poorly indexed. Detected by: ADR consistency check in step 4 of the review process.

**Premature ADR.** An ADR is proposed before the problem is well understood or before sufficient alternatives have been explored. Premature ADRs often result in decisions that must be superseded within one or two release cycles. Detected by: the Alternatives Considered section lists only one alternative, or the alternatives are superficially evaluated.

**Technology-Specific ADR Without Justification.** An ADR binds the platform to a specific tool or library without explaining why the technology choice is itself the architectural decision. The platform is then constrained by a choice that may be revisited, but the reasoning for the constraint is not captured. Detected by: the Decision section names a technology without explaining what architectural principle the technology choice enforces.

**Missing Consequences.** The ADR states a decision but does not enumerate the binding constraints that follow from it. Future implementers cannot determine what the ADR requires of them. Detected by: the Consequences section is absent or lists only benefits without constraints or prohibitions.

**Circular Dependency.** ADR A references ADR B as the justification for its decision, while ADR B references ADR A. Neither ADR is independently grounded. Detected by: following the reference chain of both ADRs results in a cycle.

**Nominal Supersession.** An ADR is declared as superseding an earlier ADR that it does not actually address, in order to avoid the appearance of conflict. The earlier ADR's actual constraints remain unresolved. Detected by: the superseded ADR's Decision section addresses a distinct problem from the superseding ADR's Decision section.

---

## ADR Quality Checklist

A reviewer should verify the following before accepting a Proposed ADR. Each item is answered YES, NO, or N.A.

| # | Item |
|---|------|
| Q-01 | Does the ADR have a stable identifier and a decision-oriented title? |
| Q-02 | Is the Problem section stated in architectural terms (not feature or performance terms)? |
| Q-03 | Is the Decision section a clear, verifiable constraint (not a goal or intent)? |
| Q-04 | Are at least two alternatives documented with substantive rejection rationale? |
| Q-05 | Does the Consequences section enumerate binding constraints and prohibitions? |
| Q-06 | Does the Tradeoffs section acknowledge what is made harder or more constrained? |
| Q-07 | Does the ADR pass constitutional compliance (no contradiction with the Architecture Constitution)? |
| Q-08 | Does the ADR pass the ARC-02 checklist for all applicable sections? |
| Q-09 | Does the ADR declare and justify every constitutional boundary it crosses? |
| Q-10 | Does the ADR evaluate its implications for deterministic reconstruction and replay? |
| Q-11 | Does the ADR declare its relationship to all relevant existing Accepted ADRs? |
| Q-12 | If this ADR supersedes an earlier ADR, does it explain why the prior decision is no longer valid? |
| Q-13 | Does the ADR avoid prescribing implementation details that belong in code or technical documentation? |
| Q-14 | Is the decision stated in technology-neutral terms, or is the technology choice itself justified as an architectural decision? |
| Q-15 | Is the Review Outcome section populated with reviewer names, date, and decision? |

---

## Governance Principles

The following principles summarize the philosophy of ADR management. They apply to every participant in the ADR process: authors, reviewers, and implementers.

**Decisions are recorded, not discussions.** An ADR is not a design document, a meeting summary, or an exploration of options. It records the binding outcome of an architectural decision that has been made.

**Every ADR must be independently grounded.** An ADR must state its own problem, its own decision, and its own consequences. An ADR that requires reading five other ADRs to be understood has not been written clearly enough.

**Binding constraints must be verifiable.** A decision that cannot be checked against production code is not a constraint — it is a preference. ADRs must be written so that a future reviewer can determine compliance or non-compliance by inspecting the codebase.

**Supersession is honest, not cosmetic.** An ADR that supersedes a prior decision must explain why the prior decision was wrong, incomplete, or no longer applicable. Supersession is not a clean-slate mechanism for avoiding the appearance of inconsistency.

**The catalogue must remain coherent.** The value of the ADR catalogue is proportional to the confidence a reader can have that it reflects the current architecture accurately. Redundant, conflicting, and silently outdated ADRs destroy that confidence. Maintaining coherence is a shared responsibility of every participant in the governance process.

**Immutability of accepted records is non-negotiable.** An accepted ADR is a historical record of a binding decision. Retroactive modification of substance — without formal supersession and review — is a governance violation that undermines the reliability of every other ADR in the catalogue.

**Governance serves the architecture, not the reverse.** The purpose of ADR governance is to produce a coherent, navigable, and trustworthy architectural record. When the governance process produces bureaucratic friction without architectural benefit, the process should be examined and simplified. The architecture is the goal; governance is the means.
