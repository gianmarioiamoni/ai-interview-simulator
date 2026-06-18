# ADR-011 — Evaluation Governance Centralization

**Status:** Accepted
**Date:** 2026-06-18
**Owner:** Infra

---

## Context

Scoring policy constants — hire decision thresholds, dimension gate rules, per-question quality bands, signal extractor weights, feedback confidence values, report classification bands, and adaptive retrieval thresholds — were defined as inline literals scattered across multiple service files. This made it impossible to audit the effective scoring policy without reading every service, and any policy change required locating and modifying several files with no guarantee of consistency.

## Decision

All evaluation governance constants are consolidated in `infrastructure/config/evaluation.py`, which is the single source of truth for the scoring policy. No service, node, or utility may define a scoring constant inline; all must import from this module.

## Rationale

A single module boundary provides:
- **Auditability**: the complete scoring policy is readable in one file.
- **Consistency**: changing a threshold in one place propagates to every consumer automatically.
- **Reviewability**: scoring policy changes produce a diff confined to a single file, making peer review straightforward.
- **Testability**: tests that verify scoring behaviour can be written against named constants rather than magic numbers.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Constants defined in each consuming service | Divergence risk; policy changes require multi-file edits with no enforcement |
| Database-backed configuration | Significant operational complexity for values that change only on deliberate policy decisions; adds a runtime dependency |
| Environment variables | Appropriate for deployment-time configuration, not for scoring policy that must be audited and version-controlled |

## Consequences

### Positive
- Full scoring policy is auditable in a single 160-line file.
- Policy changes are atomic and produce a minimal diff.
- Named constants eliminate magic numbers throughout evaluation services.
- Static analysis tools can detect unused or duplicate constants.

### Negative / Risks
- All evaluation services carry a hard import dependency on `infrastructure/config/evaluation.py`; a syntax error in that file breaks the entire evaluation subsystem.
- Constants are statically typed floats/ints; runtime policy variation (e.g., per-role thresholds) requires additional design.

## Implementation Evidence

- `infrastructure/config/evaluation.py` — hire thresholds, dimension gates, per-question scoring bands, signal weights, feedback confidence constants, report thresholds, narrative classification bands, adaptive retrieval thresholds, follow-up score threshold
- `services/decision_engine/decision_policy.py` — imports hire/lean-hire thresholds
- `services/interview_evaluation_service.py` — imports dimension gate and scoring constants
- `services/ai_feedback_service/` — imports feedback confidence constants
- `services/report_builder/` — imports report threshold constants

## Related Documents

- `docs/architecture/evaluation-pipeline.md`
- `docs/architecture/configuration.md`

## Review Trigger

Any scoring policy change request, or introduction of per-role / per-seniority threshold variation that cannot be expressed as a single constant.
