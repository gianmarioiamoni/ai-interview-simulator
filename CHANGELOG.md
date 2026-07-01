# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0-rc1] — 2026-07-01

### Architecture

- DDD layered architecture formalised: `interface → app → services → domain ← infrastructure`
- 67 Architecture Decision Records registered (ADR-001 through ADR-067)
- Platform Engineering Manifest established as engineering constitution
- LangGraph interview graph extended to 16 nodes with deterministic routing
- `InterviewMemory` 5-substructure composition formalised (EvidenceStore, CandidateProfile, ReasoningHistory, RetrievalMemory, SessionMetrics)
- All M1 and M2 public APIs frozen with `extra=forbid` and `schema_version="1.0"` on critical contracts

### Humanizer & Follow-Up Engine (M1 — Frozen)

- `FollowUpSelector` — deterministic pre-selection of eligible question indices (ADR-027)
- `FollowUpPromptBuilder` — LLM follow-up generation with dedicated prompt file (ADR-026)
- `FollowUpParser` — STRICT-mode JSON parser for LLM follow-up output
- `FollowUpGuard` — 17-rule validation layer; all guard failures fall back to SKIP
- `HumanizerService.generate_follow_up()` — integrated into `QuestionNode` with feature-flag gate
- `FollowUpTriggeredEvent` / `FollowUpSkippedEvent` — typed domain events for follow-up lifecycle
- 44/44 acceptance gates pass; 186 follow-up tests implemented

### Interview Reasoner (M2 — Frozen)

- `ReasonerService` — deterministic, LLM-free reasoning pipeline
- `ReasoningContextBuilder` — `InterviewState → ReasonerInput` builder
- `EvaluationSignalWriter` — maps evaluation scores to typed `EvidenceSignal` entries with idempotency guard
- Same-cycle visibility contract: evaluation signals written before `ReasonerService.reason()` is called (ADR-052)
- `CandidateProfileEngine` — accumulates dimension traces, coverage, trends across the session
- `PatternDetectorRegistry` — plugin-architecture detector pipeline (ADR-051)
- `ReasonerDecision` — fully structured advisory output; no free text (ADR-035)
- Failure-safe `reasoner_node`: reasoning failure never stops the interview (ADR-030)

### Detector Framework (M2-7A through M2-7J — Frozen)

- 13 active detectors in priority order: EvaluationSignalDetector (5), CoverageDetector (10), ConsistencyDetector (20), TrendDetector (30), ReasoningDepthDetector (40), EngineeringJudgmentDetector (50), CommunicationDetector (60), BehavioralPatternDetector (70), ConsistencyAcrossInterviewDetector (80), ConfidenceCalibrationDetector (90), LeadershipDetector (100), CollaborationDetector (110), AdaptabilityDetector (120)
- Detector extensibility contract frozen (ADR-051, ADR-053, ADR-054, ADR-058, ADR-059, ADR-060, ADR-061)
- `EvaluationBridgeDetector` deprecated per ADR-059 deprecation policy; removed from registry

### Behavioral Intelligence (M2-7F)

- `LeadershipDetector` — initiative, influence, ownership signal pattern detection
- `CollaborationDetector` — cross-functional, alignment, conflict-resolution patterns
- `AdaptabilityDetector` — recovery-from-failure detection algorithm (ADR-065)
- Behavioral detector family responsibility matrix frozen (ADR-062)
- Behavioral Observation Model and CoachingEngine pipeline reserved for V1.2 (ADR-055, ADR-066, ADR-067)

### Documentation

- `PLATFORM_ENGINEERING_MANIFEST.md` — engineering constitution (engineering philosophy, workflow, invariants, quality standards, release policy, technical debt policy)
- `README.md` — fully rewritten as enterprise open-source project documentation
- `TDS-V1.1-V1.2.md` — sections §9 (revised), §17, §18, §20, §21 added and frozen
- `INDEX.md` — updated to v1.6 with complete ADR registry and freeze status tables
- `docs/technical-debt-register.md` — Technical Debt Register formalised (M2-8)
- 16 architecture docs under `docs/architecture/`

### Engineering Process

- Structured milestone workflow adopted: Architecture → Contracts → ADRs → Implementation → Tests → Audit → Freeze → Certification
- M2-9 Release Candidate Certification audit completed: 2,802 tests / 0 failures
- M2-9A Architectural Compliance audit completed: layering verified, ownership map confirmed
- M2-9B Repository Identity completed: VERSION=1.1.0, README rewritten

### Testing

- 2,802 tests passing / 0 failures at RC tag
- 280 test modules covering services, domain, graph nodes, UI, infrastructure, hardening, integration
- Factories and fakes for deterministic test isolation

### Technical Debt

- Technical Debt Register formalised with 25+ registered items
- All V1.1 P0 blockers resolved (EvaluationSignalWriter, questions_answered counter, EvaluationBridgeDetector registry removal)
- All remaining items accepted as V1.2 or V1.3 evolution

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
