# /docs/architecture/evaluation-pipeline.md

# Evaluation Pipeline

**Version:** V1.0
**Last updated:** R7.9 milestone

# Overview

The evaluation system is built around:

- executable validation (Coding / SQL)
- structured LLM evaluation with field-aware JSON repair
- dimensional scoring with signal enrichment (Strategy B)
- coaching-first report generation

---

# Core Pipeline

```
Answer
  ↓
Execution (Coding/SQL only)
  ↓
Evaluation (LLM-based, with markdown-fence stripping and field-aware repair)
  ↓
Hint Generation
  ↓
Feedback Generation
  ↓
Decision (retry / next / report)
  ↓
Interview Aggregation
  ↓
Signal Enrichment (Strategy B)
  ↓
Weight Normalization
  ↓
Hire Decision + Gating
  ↓
Narrative + Coaching Report
```

---

# Execution Layer

## Coding Questions

Uses:
- Python sandbox
- visible tests (shown to candidate)
- hidden tests (oracle-generated)

Execution outputs:
- passed / failed tests
- execution time
- execution status

**JSON Repair (R6.16):** Field-aware repair is applied to LLM-generated question JSON. Python tuple-to-array normalization is applied only to `args`/`expected`/`visible_tests`/`hidden_tests` fields. It is never applied to `reference_solution`, `prompt`, `explanation`, or any field containing Python source code. This prevents corruption of valid reference solutions.

---

## SQL Questions

Uses:
- SQLite execution
- executable validation

---

# Evaluation Layer

## Written Questions

Handled by `WrittenEvaluationNode` → `WrittenQuestionEvaluator`.

**Parser (R6.9.2):** The LLM response is pre-processed to strip markdown fences (` ```json ` / ` ``` `) before JSON parsing. This eliminates the parsing failures observed when the model wraps its output in a code block.

**Calibration (R7.1.1):** The evaluation prompt explicitly instructs the LLM that question difficulty determines expected depth, not the scoring scale. An excellent answer on a MEDIUM-difficulty question can and should score in the STRONG/EXCEPTIONAL band. The full 0–100 range is encouraged.

---

## Coding / SQL

Handled by `EvaluationNode`.

Consumes:
- execution results
- question metadata (entrypoint, visible tests, expected outputs)

---

# Source of Truth

Primary source of truth: `QuestionResult`

Contains:
- question
- execution (optional, Coding/SQL only)
- evaluation
- metadata

---

# Dimension Scoring

## DimensionScorer

Aggregates per-question `QuestionEvaluation` scores into dimension-level scores.

Current dimensions:
- Technical Depth
- Problem Solving
- System Design

---

## Signal Enrichment — Strategy B (R6.26)

`SignalEnrichmentStep.enrich_scores()` receives `execution_dims: set[str]` — the set of dimensions that received at least one execution-based signal.

**Rule:**
- If a dimension is **not** in `execution_dims` → enriched score = base score (no blending)
- If a dimension **is** in `execution_dims` → enriched score = `base * (1 - α) + signal * 100 * α` (α = 0.30)

This ensures written-only candidates are never penalized by a missing execution signal treated as a failed execution. Without Strategy B, written-only candidates were capped around LEAN_HIRE regardless of answer quality.

---

## Weight Normalization

`WeightNormalizationStep` applies role-specific dimension weights (see `ROLE_WEIGHTS` in `domain/contracts/user/role.py`).

---

# Decision Engine

`HiringDecisionEngine` applies gating rules and maps overall score to a hire decision.

Thresholds (see `infrastructure/config/evaluation.py`):

| Decision | Minimum score |
|---|---|
| HIRE | ≥ 85 |
| LEAN_HIRE | ≥ 70 |
| LEAN_NO_HIRE | ≥ 60 |
| NO_HIRE | < 60 |

Gating rules reduce the score if a critical dimension (System Design < 60 or Technical Depth < 50) falls below threshold.

**Calibration note (R6.28):** Thresholds are intentionally slightly conservative. A HIRE requires 85+, which reflects senior interview bar. LEAN_HIRE (70–84) is the expected outcome for good-but-not-exceptional candidates.

---

# Interview Aggregation

`EvaluationAggregateNode` orchestrates the full pipeline.

Produces `InterviewEvaluation` containing:
- `overall_score` — final adjusted score
- `raw_score` — pre-gating score
- `adjusted_score` — post-gating score (candidate-facing)
- `level` — recomputed from `adjusted_score` (POOR / AVERAGE / STRONG / EXCELLENT)
- `hire_decision`
- `dimension_scores`, `dimension_signals`, `weighted_breakdown`
- `performance_dimensions` (with LLM-generated justifications)
- `improvement_suggestions`
- `went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy` — coaching sections (V1.0)

**Level label fix (R7.9):** `level` is computed from `adjusted_score`, not the raw pre-gating score. This ensures the label shown to the candidate matches the score they see.

---

# Report Generation

## Narrative Assembly

`EvaluationNarrativeAssembler` coordinates:
- `NarrativeGenerator` — single LLM call returning dimension justifications, improvement suggestions, and all 4 coaching sections
- `ExecutiveSummaryGenerator` — separate LLM call for the 250–350 word coaching-first Executive Summary
- `DecisionExplanationGenerator`
- `PercentileCalculator`
- `ConfidenceCalculator`

## Coaching Report Sections (V1.0 — R7.7)

`NarrativeGenerator` now returns 4 additional structured sections in its JSON response:

| Field | Purpose | Constraints |
|---|---|---|
| `went_well` | Reinforce confidence | ≥ 3 concrete observations, evidence-bound |
| `held_you_back` | Explain why weaknesses mattered | ≥ 3 items, each with `behaviour` / `why_it_matters` / `impact` |
| `knowledge_gaps` | Group missing knowledge by category | 2–5 items, evidence-only, no invented gaps |
| `next_strategy` | Concrete priorities before next interview | Exactly 3, each with `priority` / `why` / `expected_improvement` / `impact` |

## Executive Summary (V1.0 — R7.6)

250–350 words. Structured around 5 ideas:
1. Overall impression
2. What most impressed the interviewer (2–3 concrete observations)
3. Main limiting factors (explains *why* they reduced evaluation)
4. Interview Readiness (natural language, not a label)
5. Next interview focus (2–3 priorities)

Style: professional, warm, honest. No bullet lists. No HR clichés.

---

# Candidate-Facing Report (V1.0 — R7.5)

Internal metrics removed from the candidate report:
- `hiring_probability` — not shown
- `confidence` — not shown
- `gating_triggered` / `gating_reason` — not shown

Shown instead:
- **Interview Readiness** label (Interview Ready / Nearly Ready / Needs Improvement / Not Ready Yet)
- Score band label (EXCEPTIONAL / STRONG / ACCEPTABLE / WEAK / INCORRECT) on overall, dimension, and question scores
- Plain-English percentile: "You performed better than approximately X% of Senior Backend candidates."

Section order:
1. Interview Readiness
2. Executive Summary
3. What You Did Well
4. What Held You Back
5. Knowledge Gap Summary
6. Next Interview Strategy
7. Performance Dimensions
8. Question-by-Question Analysis
9. Interview Benchmark
10. Decision Details
11. Execution Signals (if present)

---

# Feedback Pipeline

`FeedbackNode` builds a `FeedbackBundle` containing:
- blocks (per-answer feedback)
- severity
- confidence
- quality
- dimension signals

---

# Hint System

`HintNode` → `AIHintService`: generates adaptive, quality-aware hints shown between attempts.

---

# Planned Improvements (V1.1+)

- Deduplication between "What Held You Back" and "Next Strategy" (~40% thematic overlap)
- Readiness time-horizon framing ("1 week vs 3 months away")
- `HUMANIZER_FOLLOW_UP_ENABLED` activation
- Percentile distribution calibration (currently slightly conservative at mid-range)
- Enforce `invoke_json` on `LLMPort` interface (currently silent fallback on raw LLM path)