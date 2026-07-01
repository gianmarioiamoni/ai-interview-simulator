# Product Requirements Document — AI Interview Simulator V1.1 / V1.2

**Status:** V1.1 Stable (Frozen 2026-06-30) — V1.2 Scope Freeze Active (2026-07-01)  
**Version:** 1.2-K0  
**Date:** 2026-07-01  
**Owner:** Product  
**Audience:** Engineering, Product, Stakeholders

---

## 1. Product Vision

### Primary Objective

Build an AI-native personal interview coach that helps software engineering candidates prepare for technical interviews through realistic, adaptive practice sessions followed by structured, dimensional feedback.

The platform simulates real interview conditions — adaptive questioning, time pressure, multi-type challenges (Written, Coding, SQL) — and returns coaching-first evaluation reports that tell candidates not just how they scored, but why, and exactly what to study next.

### Secondary Objective

Provide a calibrated Interview Readiness Score and hiring probability estimate based on dimensional performance, enabling candidates to self-assess preparation completeness before a real interview.

### Explicitly Out of Scope

The platform is **not** an automated hiring system. It does not make or recommend hiring decisions on behalf of employers. All decision language is candidate-facing, self-improvement oriented.

---

## 2. Target Users

### Junior Engineers (0–2 years)
- **Profile:** Recent graduates, bootcamp completers, first-job seekers.
- **Pain Points:** No structured practice framework; unaware of knowledge gaps; interview anxiety; feedback from real interviews is minimal.
- **Key Value:** Guided practice with immediate coaching; gap identification before first job applications.

### Mid-Level Engineers (2–5 years)
- **Profile:** Professionals seeking promotion or lateral moves to stronger companies.
- **Pain Points:** Skill drift in areas not used day-to-day; unclear how seniority evaluators think; overconfidence in familiar domains.
- **Key Value:** Dimensional scoring reveals blind spots; realistic difficulty calibration per seniority level.

### Senior Engineers (5+ years)
- **Profile:** Engineers targeting Staff/Principal roles, FAANG-level companies, or leadership transitions.
- **Pain Points:** System design competency gaps; difficulty articulating reasoning under pressure; high-stakes cost of under-preparation.
- **Key Value:** Interview Readiness estimate; coaching on explainability and communication quality.

### Career Changers
- **Profile:** Professionals transitioning from adjacent fields (data, QA, DevOps) into software development.
- **Pain Points:** Missing formal CS foundations; credential gap anxiety; unfamiliarity with interview conventions.
- **Key Value:** Structured baseline assessment; study recommendations targeting specific deficit areas.

### Freelancers / Independent Contractors
- **Profile:** Contract developers periodically re-entering the job market.
- **Pain Points:** Skill atrophy between contracts; language/framework drift; fast re-calibration needed.
- **Key Value:** Quick readiness check; targeted refresh without exhaustive review.

### FAANG / Big-Tech Preparation
- **Profile:** Engineers specifically preparing for high-signal, algorithmically-demanding interviews.
- **Pain Points:** Practice material lacks business-context realism; generic feedback insufficient; execution correctness critical.
- **Key Value:** Executable validation with hidden test cases; dimensional scoring aligned to FAANG evaluation rubrics.

### Enterprise Readiness Prep
- **Profile:** Candidates interviewing at large enterprise technology organisations with structured, panel-based interview processes.
- **Pain Points:** SQL and system-design depth; domain-specific question exposure (FINTECH, HEALTHCARE, SAAS); communication formality.
- **Key Value:** Business context profiles; SQL engine with domain-realistic schemas.

---

## 3. Product Positioning

### Market Context

| Competitor | Strength | Weakness |
|---|---|---|
| Pramp | Free peer-to-peer practice | Dependent on peer availability; inconsistent feedback quality |
| Interviewing.io | Real interviewer access | High cost; limited scalability; no async practice |
| LeetCode / HackerRank | Large problem library; known brand | Execution-only; no coaching; no conversational simulation |
| ChatGPT (raw) | Flexible; zero cost | No evaluation structure; hallucination risk; no dimensional scoring; session-stateless |

### Differentiators

1. **Coaching-First Architecture** — every session produces a structured coaching report, not just a score. The report diagnoses cause, not just symptom.
2. **Dimensional Scoring Engine** — performance is measured across independently weighted dimensions (correctness, communication, reasoning, problem decomposition), not a single numeric grade.
3. **Executable Validation** — coding and SQL answers are validated against hidden test cases with deterministic execution. Feedback references actual test failures, not LLM guesses.
4. **Explainability by Design** — every score is traceable to a specific evaluation constant in `infrastructure/config/evaluation.py`. Scoring policy is auditable and version-controlled.
5. **Business Context Realism** — questions adapt to FINTECH, ECOMMERCE, SAAS, HEALTHCARE, GENERIC contexts. SQL schemas and question framing match the target industry.
6. **Adaptive Interview Engine** — question path adjusts dynamically based on real-time performance. Poor answers generate easier follow-up probes; strong answers escalate difficulty.
7. **Signal Enrichment Strategy B** — LLM-generated qualitative signals supplement raw scores, enabling nuanced gap analysis beyond dimensional averages.

### Unique Value Proposition

> An AI interview coach that simulates real technical interview conditions, scores performance across multiple dimensions with auditable governance, and returns a coaching-first report that tells candidates exactly what to fix and why — within minutes, at zero cost.

---

## 4. Product Principles

### Coaching-First
Every evaluation output prioritises improvement guidance over verdict delivery. Scores are contextualised with specific feedback. Reports name knowledge gaps and map them to study resources.

### Transparent Scoring
All scoring thresholds, dimension weights, and decision policies are centralised in a single auditable configuration (`infrastructure/config/evaluation.py`). No magic numbers exist in evaluation logic. Changes to scoring policy are atomic, reviewable, and version-controlled.

### Explainability
Every dimension score is accompanied by a rationale. Every report section is traceable to a specific evaluation signal. Candidates understand why they scored what they scored.

### Fairness
Scoring constants apply uniformly across all sessions. Role, seniority, and business context influence question selection and difficulty calibration, not evaluation standards. Follow-up question caps (`MAX_FOLLOW_UPS_PER_INTERVIEW = 2`) prevent session length unfairness.

### Security
Prompt injection attack surface is minimised through a dedicated Prompt Security Layer. User-supplied answer content is isolated from system prompt context. API inputs are validated with Pydantic v2 schemas before reaching evaluation services.

### Enterprise Reliability
LangGraph graph topology is pinned to a stable version. State transitions are deterministic. LLM failures degrade gracefully (fallback to raw question prompt; partial evaluation with confidence flags). All evaluation paths have documented failure modes.

### Low Hallucination Rate
The Hybrid Question Intelligence architecture (ADR-004) limits generation to contexts where retrieval is structurally insufficient. Retrieval remains the primary signal for question diversity and difficulty calibration. Executable validation closes the hallucination loop for coding and SQL output.

---

## 5. Roadmap Summary

### V1.1 Headline Features
- Humanizer Follow-Up Engine activated (`HUMANIZER_FOLLOW_UP_ENABLED=True`)
- Multi-language Coding Support (JavaScript, TypeScript added alongside Python)
- Prompt Security Layer (injection detection, answer isolation)
- LLM Reliability Framework (retry policy, structured output enforcement, fallback chain)
- Coding Reliability Hardening (reference self-validation, hidden test JSON constraints)

### V1.2 Headline Features (Scope Frozen 2026-07-01)
- **Language Independence Layer** — Python/JS/TS as first-class language config (Python-only / JS-TS-only / Mixed)
- **Candidate Knowledge Model** — `ProfileFeature` activation: `NarrativeGenerator` and `ReportBuilder` consume `CandidateProfile`
- **Observation Layer** — typed `ObservationStore` with lifecycle, decay, and expiry
- **Narrative Generator V2** — profile-feature-aware coaching language
- **Coaching Engine** — Study Recommendations Engine with gap-to-resource mapping
- **Evidence Freshness** — observation decay preventing profile distortion
- **Calibration Framework** — CI-integrated scoring constant validation
- **Enterprise Extensibility** — tenant-context placeholder for V2 migration
- **Interview Replay** (session persistence, full transcript review)
- **Progress Tracking** (cross-session dimensional trends)
- **Cost Optimisation Framework** (model routing, token budgeting, caching)

### V2 Future Vision
- REST API surface for third-party integrations
- Enterprise Analytics dashboard (recruiter-facing, aggregated readiness metrics)
- Multi-modal input (screen sharing, video answer capture)
- Peer benchmarking (anonymised percentile ranking within seniority cohort)
- SaaS packaging (subscription model, organisation accounts, team dashboards)

---

## 6. EPICS

---

### EPIC-01: Adaptive Interview Engine

**Purpose:** Deliver a realistic, dynamically routed interview experience that adjusts question difficulty and area coverage based on real-time candidate performance.

**Business Value:** Core platform differentiator. Enables personalised practice sessions that surface actual skill gaps rather than following a static question sequence.

**User Story:** As a candidate, I want the interview to challenge me appropriately based on how I am performing, so that I neither coast through easy questions nor drown in questions beyond my current level.

**Functional Requirements:**
- LangGraph `StateGraph` routes question selection based on prior answer quality signals.
- Adaptive navigation node adjusts planned area coverage when weak performance is detected.
- Question type branching (Written / Coding / SQL) is deterministic and stable.
- `InterviewState` propagates all decision signals through session lifecycle.
- Session termination respects configured question count and area coverage requirements.

**Non-Functional Requirements:**
- Graph compilation completes in < 500ms on cold start.
- Node execution latency p95 < 3s per question generation step.
- Zero state corruption across 100 sequential session runs.

**Dependencies:** LangGraph (pinned version), `infrastructure/config/evaluation.py`, `services/question_intelligence/`.

**Acceptance Criteria:**
- Adaptive path produces measurably different question sequences for high-vs-low performing simulated inputs.
- All 15 graph nodes execute without error across Written, Coding, and SQL session types.
- Partial session completion (user exits mid-session) produces a valid partial report.

**Risks:** LangGraph API breaking change; state propagation edge cases in adaptive navigation.

**Priority:** P0  
**Estimated Complexity:** L  
**Expected Release:** V1.0 (complete)

---

### EPIC-02: Knowledge Gap Engine

**Purpose:** Identify and quantify specific knowledge deficits from session performance, producing dimensional gap maps that feed coaching reports and study recommendations.

**Business Value:** The gap map is the analytical foundation for all coaching output. Without it, reports are generic; with it, reports are specific and actionable.

**User Story:** As a candidate, I want to know exactly which knowledge areas I underperformed in, and by how much, so I can focus my study time efficiently.

**Functional Requirements:**
- Per-dimension scoring produces named gap signals (e.g., "SQL JOIN correctness: LOW").
- Signal Enrichment Strategy B appends LLM-generated qualitative gap descriptors to raw scores.
- Gap signals are ranked by severity and mapped to knowledge area taxonomy.
- Gap map is persisted in session state and consumed by the Report Builder.

**Non-Functional Requirements:**
- Gap computation adds < 500ms to report generation time.
- LLM enrichment failures degrade gracefully (raw score preserved; enrichment skipped).

**Dependencies:** EPIC-01 (session state), `services/interview_evaluation_service.py`, `infrastructure/config/evaluation.py`.

**Acceptance Criteria:**
- Sessions with synthetic low-quality answers produce gap signals in all evaluated dimensions.
- Gap severity ranking is consistent with configured dimension weights.
- Partial sessions (< full question count) produce a valid gap map covering completed questions.

**Risks:** LLM enrichment hallucination contaminating gap signals; signal weight misconfiguration.

**Priority:** P0  
**Estimated Complexity:** M  
**Expected Release:** V1.0 (complete)

---

### EPIC-03: Follow-up Question Engine

**Status: COMPLETED — V1.1 M1 (Frozen 2026-06-30)**

**Purpose:** Enable the Humanizer subsystem to generate contextual follow-up questions anchored to the candidate's previous answer, deepening conversational realism and probing candidate depth.

**Business Value:** Elevates the platform from a static question list to a genuine conversational interview simulation. High-quality candidate answers deserve deeper exploration — matching real interviewer behaviour.

**User Story:** As a candidate who gives a strong answer, I want the AI to probe deeper with a contextual follow-up, so that I can demonstrate — and stress-test — the full extent of my knowledge.

**Shipped Implementation (V1.1 M1):**
- `FollowUpSelector` pre-selects eligible question indices once at session start (slot-based, deterministic).
- Dedicated follow-up pipeline: `FollowUpPromptBuilder` → external `follow_up_generation.txt` prompt → LLM → STRICT `FollowUpParser` → `FollowUpGuard` (17 deterministic rules).
- `HumanizerService.generate_follow_up()` added without modifying existing `humanize()`.
- `QuestionNode` checks `follow_up_eligible_indices`, `supports_follow_up`, and `follow_up_count < max` before entering V1.1 path.
- Graceful fallback to V1.0 on any failure (parse error, guard rejection, missing context, LLM exception).
- `FollowUpTriggeredEvent` and `FollowUpSkippedEvent` emitted on `state.events`.
- `settings.py` is the single source of truth for all 12 follow-up configuration parameters.
- Maximum 2 follow-ups per interview (`settings.max_follow_ups_per_interview`).
- Follow-ups are slot-gated (selector pre-selects indices); no consecutive indices selected.
- All 44 M1-3 Acceptance Gates verified PASS.
- 186 dedicated tests; 1,760 total tests passing.

**Intentional V1.1 Design Decisions (deferred to M2):**
- Score gating on V1.1 path intentionally omitted (ADR-E). Slot-based triggering sufficient for V1.1.
- Guard retry not implemented (ADR-F). Planned for V1.2.

**Dependencies:** `services/humanizer/selector/`, `services/humanizer/follow_up/`, `services/humanizer/guards/`, `app/graph/nodes/question_node.py`, `app/ui/state_handlers/start.py`, `infrastructure/config/settings.py`.

**Priority:** P0  
**Estimated Complexity:** S  
**Expected Release:** V1.1

---

### EPIC-04: Interview Reasoner

**Purpose:** Provide structured, explainable reasoning for each dimensional score, connecting raw evaluation signals to candidate-facing coaching language.

**Business Value:** Differentiates the platform from tools that return opaque numeric scores. Candidates understand why they scored what they scored, enabling targeted improvement.

**User Story:** As a candidate reviewing my report, I want each dimension score to be accompanied by a clear rationale, so that I understand what I did well and what specifically I missed.

**Functional Requirements:**
- Each evaluated dimension produces a reasoning summary in natural language.
- Reasoning references observable answer characteristics (e.g., missing edge case, incomplete SQL clause).
- Reasoning is generated by LLM with structured output enforcement (Pydantic v2 schema).
- Confidence signals are attached to reasoning output; low-confidence reasoning is flagged in the report.
- `CandidateProfile` evolves across the session via `CandidateProfileEngine` (M2-6C).
- Pattern detectors (M2-7+) surface evidence gaps, reasoning depth, and behavioral patterns.
- `NarrativeGenerator` (M2-8) reads `CandidateProfile` to produce coaching language.

**Non-Functional Requirements:**
- Structured output schema validation must pass before reasoning is written to state.
- Reasoning generation latency does not increase total report generation time beyond 8s p95.
- Full detector pipeline must complete within 50ms per cycle (ADR-054).

**Dependencies:** `services/ai_feedback_service/`, `infrastructure/config/evaluation.py`, EPIC-02.

**Acceptance Criteria:**
- 100% of evaluated sessions produce non-empty reasoning for each scored dimension.
- Pydantic v2 schema parse failure rate < 1% across 500 test sessions with synthetic answers.
- Reasoning content references answer-specific signals, not generic templates.
- `CandidateProfile` evolves on every reasoning cycle (never frozen).
- All 7 M2-7x detectors pass performance budget tests (ADR-054).

**Risks:** LLM reasoning hallucination; structured output parse failures at schema boundary.

**Milestones:**

| Milestone | Deliverable | Status |
|---|---|---|
| M2-1 through M2-5 | Domain layer, core infrastructure, detectors, service, graph | **Completed** |
| M2-6A | Stabilization sprint (P0/P1 fixes) | **Completed** |
| M2-6B | Behavioural validation (15 scenarios) | **Completed** |
| M2-6C/D | CandidateProfileEngine + behavioural revalidation (20 scenarios) | **Completed** |
| M2-7A | Advanced detector architecture freeze | **Completed** |
| M2-7B | EvaluationSignalDetector + ReasoningDepthDetector | **Completed** |
| M2-7C | EngineeringJudgmentDetector | **Completed** |
| M2-7D | CommunicationDetector | **Completed** |
| M2-7E | BehavioralPatternDetector | **Completed** |
| M2-7F | ConsistencyAcrossInterviewDetector | **Completed** |
| M2-7G/K | ConfidenceCalibrationDetector | **Completed** |
| M2-7H | LeadershipDetector | **Completed** |
| M2-7I | CollaborationDetector | **Completed** |
| M2-7J | AdaptabilityDetector | **Completed** |
| M2-8 | Reasoner Consolidation & API Freeze | **Completed** |
| M2-9 (NarrativeGenerator reads CandidateProfile) | NarrativeGenerator | **Deferred — V1.2** |
| M2-9 (ReportBuilder reads ProfileFeatures) | ReportBuilder | **Deferred — V1.2** |

**Priority:** P1  
**Estimated Complexity:** L  
**Expected Release:** V1.1 (core), V1.2 (ProfileFeatures + reserved detectors)

---

### EPIC-05: Prompt Security Layer

**Purpose:** Protect evaluation integrity and system prompt confidentiality from prompt injection attacks embedded in candidate answer content.

**Business Value:** Preserves scoring fairness and prevents adversarial manipulation of evaluation output. Required for any enterprise or public deployment.

**User Story:** As the platform, I want candidate-supplied answer text to be isolated from system prompt context, so that a malicious or accidental injection attempt cannot alter evaluation behaviour.

**Functional Requirements:**
- Answer content is inserted into evaluation prompts through a structured, isolated slot — never concatenated into system prompt context.
- Injection pattern detection layer scans answer content before LLM submission; detected patterns are flagged and sanitised.
- Flagged injections are logged with session ID and pattern type.
- Evaluation proceeds with sanitised input; candidate is not notified of flag.

**Non-Functional Requirements:**
- Injection detection adds < 50ms per answer evaluation.
- False positive rate < 0.5% on clean answer corpus.
- Detection coverage for common injection patterns: jailbreak prefix, role override, instruction injection.

**Dependencies:** `services/ai_feedback_service/`, prompt templates (`infrastructure/prompts/`), Pydantic v2 input validation.

**Acceptance Criteria:**
- Standard jailbreak and role-override injection patterns are detected in > 99% of test cases.
- Clean answer corpus injection false positive rate < 0.5%.
- Session proceeds without visible disruption when injection is sanitised.

**Risks:** Novel injection patterns evading detection; excessive false positives degrading valid answers.

**Priority:** P0  
**Estimated Complexity:** M  
**Expected Release:** V1.1

---

### EPIC-06: LLM Reliability Framework

**Purpose:** Ensure consistent, high-quality LLM output across all evaluation, generation, and reasoning calls through structured output enforcement, retry policy, and fallback chains.

**Business Value:** Eliminates silent evaluation failures caused by malformed LLM output. Enables reliable session completion rate targets.

**User Story:** As a candidate, I want my session to complete successfully even if the LLM returns an unexpected or malformed response, so that I always receive a usable evaluation report.

**Functional Requirements:**
- All LLM calls producing structured output enforce a Pydantic v2 output schema.
- Retry policy: 3 attempts with exponential backoff on schema parse failure.
- Fallback chain: structured output failure → simplified schema → plain-text extraction → graceful degradation message.
- LLM call failures are logged with model, prompt hash, attempt count, and error type.
- Partial evaluation output (some dimensions scored, some failed) is supported.

**Non-Functional Requirements:**
- Session completion rate > 99.5% across 1,000 consecutive test sessions.
- Total retry overhead < 6s per session in the worst case (3 retries, all question generation calls).

**Dependencies:** `services/question_intelligence/`, `services/ai_feedback_service/`, all LLM-calling nodes.

**Acceptance Criteria:**
- Simulated LLM schema parse failure at 10% rate produces session completion in > 95% of runs.
- Retry mechanism correctly resolves transient parse failures without surfacing errors to the candidate.
- All retry and fallback events are captured in structured logs.

**Risks:** Fallback chain producing lower-quality evaluation output; retry overhead exceeding latency budget.

**Priority:** P0  
**Estimated Complexity:** M  
**Expected Release:** V1.1

---

### EPIC-07: Cost Optimisation Framework

**Purpose:** Reduce per-session LLM cost through intelligent model routing, prompt token budgeting, and caching of stable generation artefacts.

**Business Value:** Enables sustainable unit economics as session volume scales. Prevents runaway inference costs from verbose prompts or unnecessary model upgrades.

**User Story:** As the platform operator, I want per-session LLM spend to remain within budget targets as usage scales, so that the platform remains economically viable.

**Functional Requirements:**
- Model routing: low-complexity calls (humanizer framing, simple enrichment) routed to cheaper model tier; high-complexity calls (evaluation reasoning, coding validation) remain on `gpt-4o-mini` or better.
- Token budget enforcement: prompt templates are audited for token count; templates exceeding budget are flagged and refactored.
- Caching layer: question retrieval results (Chroma) are cached per (role, seniority, context) key for session duration.
- Cost telemetry: per-call token usage logged with call type, model, and session ID.

**Non-Functional Requirements:**
- Target: < $0.05 per completed session at `gpt-4o-mini` pricing.
- Cache hit rate > 60% for question retrieval within a session.
- Cost telemetry adds < 5ms overhead per LLM call.

**Dependencies:** All LLM-calling services, `infrastructure/config/settings.py`, Chroma retrieval layer.

**Acceptance Criteria:**
- Cost telemetry dashboard shows per-call breakdown for a representative session sample.
- Caching layer produces measurably fewer Chroma queries per session with cache enabled.
- Model routing configuration is centralised and overridable via environment variable.

**Risks:** Cheaper model tier producing lower-quality evaluation output; cache invalidation logic errors.

**Priority:** P1  
**Estimated Complexity:** M  
**Expected Release:** V1.2

---

### EPIC-08: Coding Multi-language Support (Python, JavaScript, TypeScript)

**Purpose:** Extend the coding evaluation pipeline to support JavaScript and TypeScript in addition to Python, enabling candidates to practise in their primary language.

**Business Value:** Removes a significant adoption blocker for frontend engineers and full-stack candidates for whom Python is not their primary language.

**User Story:** As a frontend engineer, I want to write coding solutions in JavaScript or TypeScript, so that my interview practice reflects my actual working language and skill set.

**Functional Requirements:**
- Language selection available at session configuration (Python / JavaScript / TypeScript).
- Per-language execution sandbox: Node.js runtime for JS/TS; existing Python runtime for Python.
- Question generation pipeline produces language-appropriate starter code stubs and constraints.
- Hidden test cases are authored in the target language.
- Evaluation rubric applies uniformly across languages; language-specific idioms do not penalise correctness.
- TypeScript: transpilation step before execution; type error output included in feedback.

**Non-Functional Requirements:**
- Code execution timeout: 10s per test case, consistent across languages.
- Execution sandbox isolation: no file system access, no network access, no inter-session state.
- JS/TS execution environment version pinned in `pyproject.toml` equivalent.

**Dependencies:** EPIC-06 (reliability), coding execution infrastructure, `services/question_intelligence/pipelines/coding_question_pipeline.py`.

**Acceptance Criteria:**
- Python, JavaScript, and TypeScript sessions all complete without error on a standard coding problem set.
- TypeScript type errors are surfaced in evaluation feedback.
- Execution sandbox isolation verified: no cross-session data leakage.
- Language selection persists correctly through adaptive navigation.

**Risks:** Node.js sandbox security surface; TypeScript transpilation adding latency; test case authoring overhead for JS/TS.

**Priority:** P0  
**Estimated Complexity:** L  
**Expected Release:** V1.1

---

### EPIC-09: Interview Replay

**Purpose:** Enable candidates to review complete past sessions — full question transcript, their answers, dimensional scores, and coaching notes — to track learning and revisit feedback.

**Business Value:** Transforms the platform from a single-use practice tool to a learning compendium. Repeat users derive long-term value from session history.

**User Story:** As a returning candidate, I want to replay any past session to review my answers and scores side-by-side with the coaching feedback, so that I can measure my improvement and internalise past mistakes.

**Functional Requirements:**
- Session state is persisted to durable storage on session completion.
- Replay UI renders full session transcript: question → answer → score → coaching note per question.
- Dimensional scores are displayed per-question and aggregated at session level.
- Sessions are listed in reverse chronological order with summary metadata (date, role, score, readiness level).
- Replay is read-only; no re-submission of answers from replay view.

**Non-Functional Requirements:**
- Session storage schema supports forward-compatible extension (new fields do not break existing records).
- Replay load time < 2s for sessions up to 20 questions.
- Storage backend: SQLite for local deployment (ADR-015 alignment).

**Dependencies:** ADR-015 (storage backend split), EPIC-01, EPIC-02, session state serialisation.

**Acceptance Criteria:**
- 10 consecutive completed sessions are all retrievable and render correctly in replay view.
- Replay view for a session with 15 questions loads in < 2s.
- Session records survive application restart.

**Risks:** Session state schema migration complexity; storage growth management for long-term users.

**Priority:** P1  
**Estimated Complexity:** L  
**Expected Release:** V1.2

---

### EPIC-10: Progress Tracking

**Purpose:** Surface cross-session improvement trends at the dimension level, enabling candidates to see measurable progress over time.

**Business Value:** Progress visibility is the primary retention driver for returning users. Candidates who see improvement trends are significantly more likely to continue practising.

**User Story:** As a candidate who has completed multiple sessions, I want to see how my performance in each dimension has changed over time, so that I can validate that my preparation is working.

**Functional Requirements:**
- Dimensional scores are aggregated across sessions per (role, seniority) cohort.
- Trend charts show per-dimension score over time (last N sessions, configurable).
- Summary metrics: sessions completed, average readiness score, strongest dimension, most improved dimension, largest remaining gap.
- Progress data is computed from persisted session records (EPIC-09 dependency).
- Export: progress report available as PDF or CSV.

**Non-Functional Requirements:**
- Progress computation is read-only; does not modify session records.
- Charts render in < 1s for up to 100 sessions.

**Dependencies:** EPIC-09 (session storage), dimensional scoring data contract.

**Acceptance Criteria:**
- Synthetic session data spanning 10 sessions produces correct trend lines for all dimensions.
- Most-improved dimension calculation is consistent with raw score deltas.
- Progress view is accessible with WCAG 2.1 AA compliance (EPIC-12 dependency for full compliance).

**Risks:** Cross-role/seniority comparison producing misleading trend signals if sessions use different configurations.

**Priority:** P1  
**Estimated Complexity:** M  
**Expected Release:** V1.2

---

### EPIC-11: Study Recommendations

**Purpose:** Generate a prioritised, gap-driven study plan mapping identified knowledge weaknesses to curated learning resources.

**Business Value:** Closes the loop between assessment and preparation. Candidates leave each session with a concrete next step, not just a score.

**User Story:** As a candidate who just completed a session, I want a prioritised list of study topics with suggested resources mapped to my specific gaps, so that I know exactly what to focus on between now and my next session.

**Functional Requirements:**
- Gap map (EPIC-02) drives recommendation generation.
- Recommendations are ranked by gap severity × estimated impact on Interview Readiness Score.
- Each recommendation includes: topic name, gap description, 2–3 suggested resources (documentation, course, article), estimated study time.
- Recommendations are persisted with session record and rendered in session report.
- Resource library is curated and version-controlled; no live web scraping.

**Non-Functional Requirements:**
- Recommendation generation adds < 1s to report generation time (resource lookup is local).
- Resource library covers all knowledge areas in the question taxonomy.

**Dependencies:** EPIC-02 (gap map), EPIC-04 (reasoner output), resource library data asset.

**Acceptance Criteria:**
- Sessions with SQL gap signals produce recommendations covering SQL-specific resources.
- Sessions with zero gap signals (perfect score) produce a completion-acknowledgement message, not empty recommendations.
- Recommendation ranking is consistent with gap severity order.

**Risks:** Resource library staleness; recommendation relevance degrading as technology landscape shifts.

**Priority:** P2  
**Estimated Complexity:** M  
**Expected Release:** V1.2

---

### EPIC-12: UI Refresh (Design System, Accessibility, Dark Mode)

**Purpose:** Establish a coherent design system, achieve WCAG 2.1 AA accessibility compliance, and add dark mode to the Gradio-based interface.

**Business Value:** Reduces cognitive friction for candidates during sessions. Accessibility compliance opens the platform to a broader user population and is a prerequisite for enterprise deployments.

**User Story:** As a candidate, I want an interface that is visually clear, accessible, and comfortable to use for extended practice sessions, so that UI friction does not impair my performance.

**Functional Requirements:**
- Design tokens defined for colour, typography, and spacing (light and dark themes).
- Dark mode toggle persists user preference across sessions.
- All interactive elements meet WCAG 2.1 AA contrast requirements.
- Keyboard navigation is fully functional for all session flows.
- Screen reader compatibility for session transcript and report sections.
- Code answer input area supports syntax highlighting for Python, JavaScript, TypeScript.

**Non-Functional Requirements:**
- Lighthouse accessibility score ≥ 90 on session and report views.
- Dark mode toggle adds zero latency to page render.
- Design system tokens are defined in a single source file.

**Dependencies:** Gradio component surface, EPIC-08 (multi-language syntax highlighting).

**Acceptance Criteria:**
- WCAG 2.1 AA audit passes for session start, in-session, and report views.
- Dark mode renders all text at ≥ 4.5:1 contrast ratio.
- Keyboard-only navigation completes a full session without mouse.

**Risks:** Gradio's design customisation constraints limiting design system fidelity; accessibility tooling compatibility with Gradio's rendering layer.

**Priority:** P2  
**Estimated Complexity:** L  
**Expected Release:** V1.2

---

### EPIC-13: Enterprise Analytics

**Purpose:** Provide an aggregated, recruiter-facing analytics dashboard showing cohort-level readiness trends, skill distribution, and benchmark comparisons.

**Business Value:** Enables the platform's enterprise use case — organisations use aggregate data to understand candidate pipeline quality and adjust their interview processes.

**User Story:** As a hiring manager, I want to see aggregated readiness scores and skill distribution for candidates who have used the platform, so that I can benchmark my candidate pipeline before investment in full interview cycles.

**Functional Requirements:**
- Aggregated dashboard showing: cohort readiness distribution, dimension-level skill heatmap, top gap areas across cohort, session volume trends.
- Data is anonymised and role/seniority segmented.
- Cohort filtering by role, seniority, business context, and date range.
- Export: CSV and PDF report formats.
- Access control: analytics access requires separate authentication token.

**Non-Functional Requirements:**
- Dashboard loads aggregate data for cohorts up to 1,000 sessions in < 3s.
- All candidate data displayed in aggregate only; no individual PII surfaced.
- Access control enforced server-side; client-side filtering is display-only.

**Dependencies:** EPIC-09 (session storage), EPIC-10 (progress data model), REST API surface (V2).

**Acceptance Criteria:**
- Dashboard correctly segments cohort data by all filter dimensions.
- Individual session data cannot be retrieved through analytics API endpoints.
- Export produces correct CSV for a synthetic 100-session cohort.

**Risks:** Privacy compliance requirements varying by deployment region; aggregate data re-identification risk with small cohorts.

**Priority:** P3  
**Estimated Complexity:** XL  
**Expected Release:** V2

---

## 7. Prioritisation Matrix

### Must Have (V1.2)

| Feature | Epic |
|---|---|
| Language Independence Layer | EPIC-00 |
| Candidate Knowledge Model (ProfileFeature activation) | EPIC-01 |
| Observation Layer (ObservationStore lifecycle) | EPIC-02 |
| Narrative Generator V2 (profile-feature-aware) | EPIC-03 |
| Session Persistence (SQLite, forward-compatible schema) | EPIC-09 |

### Should Have (V1.2)

| Feature | Epic | Target |
|---|---|---|
| Coaching Engine (Study Recommendations) | EPIC-04 | V1.2 |
| Evidence Freshness (observation decay) | EPIC-05 | V1.2 |
| Calibration Framework (CI gate) | EPIC-06 | V1.2 |
| Interview Replay UI | EPIC-09 | V1.2 |
| Progress Tracking | EPIC-10 | V1.2 |
| Cost Optimisation Framework | EPIC-07 | V1.2 |

### Could Have (V1.2)

| Feature | Epic |
|---|---|
| Enterprise Extensibility (tenant-context placeholder) | EPIC-07 (V1.2) |
| UI Refresh (design system, accessibility, dark mode) | EPIC-12 |

### Won't Have (Post-V2)

| Feature | Epic |
|---|---|
| Enterprise Analytics dashboard | EPIC-13 |
| REST API public surface | — |
| Multi-modal input (video, screen share) | — |
| SaaS subscription and organisation accounts | — |
| Peer benchmarking (anonymised percentile ranking) | — |

---

## 8. Release Plan

### V1.1

#### Milestone M1 — Follow-Up Question Engine (FROZEN 2026-06-30)

**Status: COMPLETED**

**Delivered:**
- EPIC-03: Follow-up Question Engine — fully implemented and integrated.
  - `FollowUpSelector`, `FollowUpPromptBuilder`, STRICT `FollowUpParser`, `FollowUpGuard` (17 rules).
  - `HumanizerService.generate_follow_up()`, `QuestionNode` integration, runtime events.
  - Graceful fallback; 44/44 Acceptance Gates PASS; 186 dedicated tests.

**M1 Architecture Baseline:** Frozen. All future follow-up improvements target M2 or V1.2.

---

#### Milestone M2 — Conversation Depth (Weeks 3–4)

**Features:**
- EPIC-03: Follow-up Question Engine — **COMPLETED in M1**. M2 adds: score gating, guard retry, `humanizer_v2.txt` area anchoring, event field alignment, batch-mode selector refinement.
- EPIC-04: Interview Reasoner — per-dimension reasoning with structured output schema.

**Success Criteria:**
- Follow-up triggers correctly in > 98% of sessions with ≥ 2 optimal-quality answers.
- Follow-up cap of 2 enforced in 100% of test sessions.
- Reasoning output passes Pydantic v2 schema validation in > 99% of sessions.

---

#### Milestone M3 — Language Expansion (Weeks 5–7)

**Features:**
- EPIC-08: Multi-language Coding Support — JavaScript and TypeScript execution sandboxes, language-appropriate question generation, hidden test cases.

**Success Criteria:**
- Python, JavaScript, and TypeScript sessions complete without error on full coding question set.
- TypeScript type error feedback is surfaced correctly in evaluation output.
- Execution sandbox isolation verified: no cross-session data access.

---

#### Milestone M4 — V1.1 Validation and Release (Week 8)

**Activities:**
- End-to-end regression suite across all session types (Written, Coding/Python, Coding/JS, Coding/TS, SQL × all business contexts).
- Security penetration test on Prompt Security Layer.
- Performance benchmarking: session latency p50/p95 at expected concurrent load.
- Documentation update: ADR reviews, README, deployment guide.

**Success Criteria:**
- Zero P0/P1 open issues at release gate.
- All V1.1 acceptance criteria from EPIC-03, EPIC-05, EPIC-06, EPIC-08 satisfied.
- Latency p95 < 12s for complete session (all LLM calls inclusive).

---

### V1.2

#### Milestone M1 — Persistence Layer (Weeks 1–2)

**Features:**
- EPIC-09: Session storage schema design and implementation (SQLite, ADR-015 alignment).
- Session serialisation and deserialisation with forward-compatible schema versioning.

**Success Criteria:**
- 100 consecutive sessions stored and retrieved without data loss.
- Schema migration from empty database to V1.2 schema succeeds on clean install.

---

#### Milestone M2 — Replay and Progress (Weeks 3–5)

**Features:**
- EPIC-09: Interview Replay UI (transcript, scores, coaching notes).
- EPIC-10: Progress Tracking (dimensional trend charts, summary metrics, export).

**Success Criteria:**
- Replay renders correctly for sessions with 5 to 20 questions.
- Trend charts produce correct output for synthetic 10-session dataset.
- Progress export (CSV) matches raw session data.

---

#### Milestone M3 — Recommendations and Cost (Weeks 6–8)

**Features:**
- EPIC-11: Study Recommendations Engine (gap-to-resource mapping, ranking, resource library).
- EPIC-07: Cost Optimisation Framework (model routing, token budgeting, retrieval caching).

**Success Criteria:**
- Recommendations present in 100% of sessions with identified gaps.
- Recommendations correctly reference gap-specific resources (verified on 5 representative gap types).
- Cost telemetry logs per-call token usage for all LLM calls.
- Cache hit rate > 60% for question retrieval within a session.

---

#### Milestone M4 — UI Refresh and V1.2 Release (Weeks 9–11)

**Features:**
- EPIC-12: UI design system, WCAG 2.1 AA compliance, dark mode, syntax highlighting.

**Success Criteria:**
- Lighthouse accessibility score ≥ 90 on all primary views.
- Dark mode contrast ratio ≥ 4.5:1 on all text elements.
- Keyboard-only navigation completes full session without mouse.
- Zero P0/P1 open issues at V1.2 release gate.

---

### V2 Future Vision

V2 transitions the platform from a personal practice tool to an enterprise-grade assessment infrastructure. Key directions:

- **REST API Surface:** Authenticated API endpoints exposing session creation, question delivery, answer submission, and evaluation report retrieval. Enables third-party integrations (ATS systems, LMS platforms, enterprise HR tools).
- **SaaS Packaging:** Multi-tenant architecture, subscription tiers, organisation account management, and per-seat billing.
- **Enterprise Analytics:** Cohort-level readiness dashboards for hiring managers. Aggregated, anonymised, segmented by role/seniority/business context.
- **Peer Benchmarking:** Anonymised percentile ranking within seniority cohort, enabling candidates to contextualise their absolute scores.
- **Multi-modal Input:** Optional video answer capture with transcript extraction; screen sharing for live coding observation.
- **Evaluated Follow-up (Model B):** Full evaluation pipeline extension to treat follow-up answers as independently scored question attempts, with dimensional score contribution (ADR-010 Model B, deferred from V1.1).

V2 architecture will require a storage backend upgrade (PostgreSQL), an authentication layer, and a REST API gateway. These infrastructure requirements are out of scope for V1.x.
