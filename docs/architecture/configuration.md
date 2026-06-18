# Configuration Reference

**Status:** STUB — populate from `infrastructure/config/settings.py` and `infrastructure/config/evaluation.py`
**Owner:** Infra
**SSOT For:** All env vars, model settings, feature flags, evaluation governance constants
**Update Trigger:** Any change to `settings.py` or `evaluation.py`
**ADR:** ADR-011

---

## Sections (to fill)

### 1. Environment Variables

<!-- TODO: Table of all env vars from settings.py -->
<!-- Columns: Variable | Type | Default | Required | Description -->

#### Credentials
- `OPENAI_API_KEY`
- `HF_TOKEN`

#### Model Configuration
- `CHAT_MODEL`
- Embedding models (OpenAI + local SentenceTransformer)
- Temperatures

#### Retry & Limits
- LLM JSON retry count
- Coding/SQL pipeline retry counts
- Test generation retry count
- `JOB_DESCRIPTION_MAX_CHARS`
- `COMPANY_DESCRIPTION_MAX_CHARS`

#### Feature Flags (settings.py)
- `CODING_DOMAIN_PROFILE_ENABLED`
- `CODING_SCENARIO_ANCHOR_ENABLED`
- `CODING_DOMAIN_VOCABULARY_ENABLED`

### 2. Runtime State Flags

<!-- TODO: Flags set on InterviewState at runtime (not env vars) -->
<!-- Columns: Flag | Default | Set By | Effect -->

- `enable_humanizer` — default `True`
- `adaptive_interview_enabled` — default `False`

### 3. Decision Engine Flags

<!-- TODO: Flags in services/decision_engine/decision_policy.py POLICY["global"] -->

- `enable_penalties`
- `enable_downgrade`

### 4. Evaluation Governance Constants

<!-- TODO: All constants from infrastructure/config/evaluation.py -->
<!-- Group by: hire thresholds | dimension gates | scoring bands | signal weights | feedback confidence | adaptive retrieval | follow-up thresholds -->

### 5. `.env.example`

<!-- TODO: Template with all required keys and safe placeholder values -->
<!-- Note: .env.example file should also be created at project root -->

---

## Cross-References

- `feature-flags.md` — flags-only view
- ADR-011 — rationale for centralization
- `evaluation-pipeline.md` — how constants are applied
