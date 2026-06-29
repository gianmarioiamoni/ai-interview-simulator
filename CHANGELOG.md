# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-06-29

### Added

**Coaching-first report (R7.5–R7.7)**
- Interview Readiness label replaces raw internal hire decision for candidates (Interview Ready / Nearly Ready / Needs Improvement / Not Ready Yet)
- Score band labels on overall score, dimensions, and per-question scores (EXCEPTIONAL / STRONG / ACCEPTABLE / WEAK / INCORRECT)
- Plain-English Interview Benchmark (percentile without statistical jargon)
- Four new structured coaching sections:
  - What You Did Well — ≥ 3 concrete, evidence-bound observations
  - What Held You Back — explains *why* each weakness mattered to the interviewer
  - Knowledge Gap Summary — missing concepts grouped by category
  - Next Interview Strategy — exactly 3 priorities with expected impact level
- Internal metrics removed from candidate view (hiring_probability, confidence, gating reason)
- Report section order redesigned: Readiness → Executive Summary → Coaching → Dimensions → Questions → Benchmark

**Executive Summary redesign (R7.6)**
- Rewritten from 3–4 lines to 250–350 words
- Structured around 5 ideas: overall impression, concrete strengths, why weaknesses mattered, readiness assessment, next steps
- Reads like feedback from a Senior Engineering Manager
- Personalized using job description and company context when available

**Signal Enrichment Strategy B (R6.26)**
- Written-only dimensions are no longer penalized by a missing execution signal
- Enrichment alpha (0.30) applied only to dimensions with real execution-based evidence
- Written-only excellent candidates can now reach HIRE decision

**Coding pipeline reliability (R6.14–R6.17)**
- Field-aware JSON repair: tuple-to-array normalization no longer applied to `reference_solution` or any Python source code field
- Reference solution corruption eliminated
- Coding question consistency improved from ~30% to >90% pass rate

**Written evaluation parser (R6.9.2)**
- Markdown-fenced JSON (`\`\`\`json ... \`\`\``) now stripped before parsing
- Parsing failure rate dropped from ~100% to near zero

**Evaluation calibration (R7.1.1)**
- Written evaluation prompt updated: question difficulty determines expected depth, not the scoring scale
- Full 0–100 range encouraged; excellent answers on MEDIUM questions score in STRONG/EXCEPTIONAL band

### Fixed

- Level label now computed from adjusted score (post-gating) rather than raw pre-gating score (R7.9)
- Hiring decision monotonicity verified across all candidate profiles (R6.27)

### Changed

- `narrative_generator.txt` prompt extended with 4 new structured output fields
- `NarrativeGenerator` parses and defaults all new coaching fields
- `InterviewEvaluation` and `FinalReportDTO` carry 4 new optional coaching fields
- `InterviewEvaluationService` recomputes `level` from `adjusted_score`

### Documentation

- `README.md` updated to describe coaching-first product
- `docs/architecture/evaluation-pipeline.md` rewritten to V1.0 (all R6/R7 milestones)
- `docs/architecture/configuration.md` now documents hire/gate/level thresholds and Strategy B

---

## [0.9.0] — Pre-release (R5.x–R6.25)

- LangGraph interview graph with adaptive question flow
- Humanizer subsystem (DIRECT_QUESTION and REMARK_PLUS_QUESTION)
- Dimensional scoring (Technical Depth, Problem Solving, System Design)
- Coding execution sandbox with visible and hidden tests
- SQL execution via SQLite
- Chroma vector corpus with HF Dataset backup/restore
- Gradio UI deployable locally and on Hugging Face Spaces
- PDF and JSON report export
- Business context profiles (Fintech, Healthcare, Startup, E-commerce)
- Hiring decision engine with gating rules
- Written evaluation with structured LLM scoring
