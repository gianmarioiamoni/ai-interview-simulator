# Configuration Reference

**Status:** Active
**Owner:** Infra
**SSOT For:** All env vars, model settings, feature flags, evaluation governance constants
**Update Trigger:** Any change to `settings.py` or `evaluation.py`
**ADR:** ADR-011

---

## 1. Environment Variables

### Credentials

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `OPENAI_API_KEY` | `str` | — | **Yes** | OpenAI API key. Startup fails if missing. |
| `HF_TOKEN` | `str` | `None` | No | Hugging Face access token. Required only for private HF repos. |

### Corpus

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `CORPUS_HF_REPO` | `str` | `None` | Yes (if no local corpus) | HF Dataset repo ID containing `chroma_corpus.tar.gz`. Used by `ensure_corpus()` at startup when no local corpus is present. Example: `username/interview-corpus`. |

### Model Configuration

| Variable | Type | Default | Description |
|---|---|---|---|
| `CHAT_MODEL` | `str` | `gpt-4o-mini` | LangChain LLM model name |
| `CHAT_TEMPERATURE` | `float` | `0.0` | Temperature for primary LangChain LLM (deterministic) |
| `OPENAI_CLIENT_TEMPERATURE` | `float` | `0.3` | Temperature for direct OpenAI SDK client |
| `OPENAI_EMBEDDING_MODEL` | `str` | `text-embedding-3-small` | OpenAI embedding model for corpus build/retrieval |
| `LOCAL_EMBEDDING_MODEL` | `str` | `all-MiniLM-L6-v2` | Local SentenceTransformer model for semantic dedup |

### Retry & Limits

| Variable | Type | Default | Description |
|---|---|---|---|
| `LLM_JSON_RETRY_ATTEMPTS` | `int` | `2` | JSON parse/validation retries in `DefaultLLMAdapter.invoke_json` |
| `CODING_JSON_RETRY_ATTEMPTS` | `int` | `3` | JSON parse retries in `CodingQuestionGenerator` |
| `CODING_PIPELINE_RETRY_ATTEMPTS` | `int` | `2` | Full-generation retries in `CodingQuestionPipeline` |
| `SQL_PIPELINE_RETRY_ATTEMPTS` | `int` | `2` | Full-generation retries in `SQLQuestionPipeline` |
| `TEST_GENERATION_RETRY_ATTEMPTS` | `int` | `2` | Generation retries in `AITestGenerator` |
| `JOB_DESCRIPTION_MAX_CHARS` | `int` | `500` | Max characters of job description injected into prompts |
| `COMPANY_DESCRIPTION_MAX_CHARS` | `int` | `200` | Max characters of company description injected into prompts |
| `BUSINESS_CONTEXT_MIN_KEYWORD_SCORE` | `int` | `2` | Min keyword score for `BusinessContext` classification; below threshold falls back to GENERIC |

### Feature Flags

| Variable | Type | Default | Description |
|---|---|---|---|
| `HUMANIZER_ENABLED` | `bool` | `True` | Enable the Humanizer subsystem (conversational question framing) |
| `HUMANIZER_FOLLOW_UP_ENABLED` | `bool` | `False` | Enable FOLLOW_UP decisions in Humanizer policy engine (requires `HUMANIZER_ENABLED=True`; disabled until V1.1) |
| `CODING_DOMAIN_PROFILE_ENABLED` | `bool` | `True` | Enable `CodingDomainProfile`-driven framing in coding question prompts |
| `CODING_SCENARIO_ANCHOR_ENABLED` | `bool` | `True` | Enable scenario anchor sampling from `CodingDomainProfile.scenario_anchor_pool` |
| `CODING_DOMAIN_VOCABULARY_ENABLED` | `bool` | `True` | Enable domain vocabulary injection from `CodingDomainProfile.vocabulary_hint` |

### Runtime / Server (not in settings.py)

| Variable | Default | Description |
|---|---|---|
| `PORT` | `7860` | Gradio server port |
| `SERVER_HOST` | `0.0.0.0` | Gradio server bind address |

---

## 2. Runtime State Flags

Set on `InterviewState` at runtime (not env vars):

| Flag | Default | Set By | Effect |
|---|---|---|---|
| `enable_humanizer` | `True` | UI session init | Activates Humanizer subsystem for the session |
| `adaptive_interview_enabled` | `False` | UI session init | Enables adaptive difficulty adjustment |

---

## 3. Decision Engine Flags

Configured in `services/decision_engine/decision_policy.py` `POLICY["global"]`:

| Flag | Description |
|---|---|
| `enable_penalties` | Apply penalty scoring for weak answers |
| `enable_downgrade` | Allow difficulty downgrade on consecutive weak answers |

---

## 4. Evaluation Governance Constants

All constants live in `infrastructure/config/evaluation.py`. They are **never overridden by environment variables** — changes require a code deploy.

### Hire Decision Thresholds

| Decision | Score band | Notes |
|---|---|---|
| HIRE | ≥ 85 | Intentionally high; reflects senior interview bar |
| LEAN_HIRE | 70–84 | Expected outcome for good-but-not-exceptional candidates |
| LEAN_NO_HIRE | 60–69 | Needs improvement |
| NO_HIRE | < 60 | Significant gaps |

### Dimension Gate Rules

Applied by `HiringDecisionEngine` before assigning the final decision. A gate failure applies a score penalty.

| Dimension | Gate threshold | Penalty |
|---|---|---|
| System Design | < 60 | × 0.90 |
| Technical Depth | < 50 | × 0.95 |

### Level Labels

Recomputed from `adjusted_score` (post-gating) — not from the raw pre-gating score.

| Level | Score band |
|---|---|
| EXCELLENT | ≥ 80 |
| STRONG | 65–79 |
| AVERAGE | 50–64 |
| POOR | < 50 |

### Signal Enrichment (Strategy B — R6.26)

Enrichment alpha: `ENRICHMENT_ALPHA = 0.30`

Applied only to dimensions that received at least one execution-based signal (`execution_dims`). Dimensions without execution evidence use the base score unchanged. This prevents written-only candidates from being penalized by a missing signal.

### Calibration Note (R6.28)

The HIRE threshold (85) is intentionally conservative. In a synthetic population of 200 candidates, approximately 8% fall in the HIRE band. This aligns with FAANG-style hiring bar. For a mid-size company context, the threshold may be adjusted in a future release.

---

## 5. `.env.example`

```dotenv
# Required
OPENAI_API_KEY=sk-...

# Required if no local corpus is present
CORPUS_HF_REPO=username/interview-corpus

# Optional — required only for private HF repos
HF_TOKEN=hf_...

# Optional — model configuration
# CHAT_MODEL=gpt-4o-mini
# CHAT_TEMPERATURE=0.0
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Optional — feature flags
# HUMANIZER_ENABLED=true
# HUMANIZER_FOLLOW_UP_ENABLED=false
```

---

## Cross-References

- `feature-flags.md` — flags-only view
- ADR-011 — rationale for centralization
- `evaluation-pipeline.md` — how evaluation constants are applied
- `infrastructure/config/settings.py` — Pydantic settings class (source of truth)
