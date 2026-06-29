# Release Notes — AI Interview Simulator V1.0

**Release date:** 2026-06-29
**Version:** 1.0.0

---

## What is AI Interview Simulator?

AI Interview Simulator is a technical interview preparation platform that helps software engineers practice and improve before real interviews.

The platform conducts full mock technical interviews — including written questions, coding challenges, and database problems — then produces a personalized coaching report that explains exactly what you did well, what held you back, and what to focus on before your next interview.

---

## What's new in V1.0

### A coaching report worth reading

The V1.0 report has been completely redesigned around one question: *"If I were the candidate, would this report genuinely help me perform better in my next interview?"*

Every section is now coaching-first:

**Interview Readiness**
Replaces the raw score with a plain-language readiness label (Interview Ready / Nearly Ready / Needs Improvement / Not Ready Yet) and a score band (EXCEPTIONAL / STRONG / ACCEPTABLE / WEAK), so you immediately understand where you stand.

**Executive Summary**
A 250–350 word coaching narrative written in the style of a Senior Engineering Manager. It names specific things you said, explains what impressed the interviewer, and tells you exactly what to fix and why — not generic advice.

**What You Did Well**
At least 3 concrete observations tied to your actual answers. References specific technologies, methodologies, or reasoning patterns you demonstrated. Never generic praise.

**What Held You Back**
Each item explains three things: what you did, why interviewers care about it, and how it affected your evaluation. This is the most actionable section — it answers "why did I lose points?"

**Knowledge Gap Summary**
Missing knowledge grouped by category (Architecture, Distributed Systems, Databases, System Design, etc.). Only includes gaps supported by your interview answers. If you didn't show a gap, it won't appear.

**Next Interview Strategy**
Exactly 3 priorities, each with a clear reason and an expected impact level (High / Medium / Low). Answers: "If I interview again next week, what should I do differently?"

### Score bands on everything

Every score — overall, per-dimension, per-question — now shows a band label alongside the number. You can see at a glance whether a 72 is ACCEPTABLE or STRONG.

### Fair evaluation for written-only interviews

Signal Enrichment Strategy B ensures that candidates who answer only written (non-coding) questions are evaluated on the quality of their answers alone. Previously, the absence of an execution signal could unfairly reduce scores.

### Reliable coding question generation

Coding questions now use field-aware JSON repair. Reference solutions are never corrupted during generation. Consistency improved from ~30% to >90%.

### Reliable written evaluation

Written answers are no longer lost to JSON parsing failures. Markdown-fenced responses from the LLM are now handled correctly.

---

## Known limitations (V1.1 roadmap)

The following items are known and intentionally deferred:

- **Section overlap (~40%):** "What Held You Back" and "Next Interview Strategy" sometimes reference the same gaps from different angles. Deduplication is planned for V1.1.
- **No time-horizon in readiness:** The Readiness section does not yet estimate how long preparation might take ("1 week vs 3 months"). Coming in V1.1.
- **Conservative hiring threshold:** The HIRE threshold (85/100) reflects a senior FAANG-style bar. Good candidates typically land in LEAN_HIRE (70–84). This is intentional but may be configurable in a future release.
- **Humanizer follow-up questions disabled:** The follow-up question capability exists but is gated off. It will be enabled in V1.1 after additional validation.
- **No concrete study resources:** Next Interview Strategy names skill areas but does not yet link to books, platforms, or practice exercises. Planned for V2.0.

---

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # populate OPENAI_API_KEY and CORPUS_HF_REPO
python -m app.main
```

Full setup instructions: see `README.md`.

---

## Feedback

This is V1.0. If something feels off — a score that doesn't make sense, a coaching section that seems generic, a knowledge gap that wasn't real — that feedback is valuable. The evaluation pipeline improves with evidence.
