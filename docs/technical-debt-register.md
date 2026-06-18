# Technical Debt Register

**SSOT:** This file + `docs/architecture/questions/open_issues.md` (active QI-specific items)
**Owner:** Arch
**Update Policy:** Updated at every sprint close; items closed when fix is merged

---

## Status Legend

| Status | Meaning |
|---|---|
| `OPEN` | Unresolved |
| `IN-PROGRESS` | Being worked |
| `CLOSED` | Resolved (keep for history) |
| `DEFERRED` | Intentionally postponed with rationale |

---

## Active Items

### Domain Layer

| ID | Item | Location | Severity | Status | ADR |
|---|---|---|---|---|---|
| TD-DL-001 | Domain imports `services/` and `app/` — layer violation | `domain/contracts/interview_state/base.py`, `question_bank_item.py`, `question_runtime_lineage.py` | High | OPEN | ADR-007 |
| TD-DL-002 | Duplicate `allowed_actions` field declaration | `domain/contracts/interview_state/base.py` lines 55 & 85 | Medium | OPEN | — |
| TD-DL-003 | Duplicate `LLMPort` Protocol | `app/ports/llm_port.py` + `infrastructure/llm/llm_adapter.py` | Medium | OPEN | — |

### Question Intelligence

| ID | Item | Location | Severity | Status | ADR |
|---|---|---|---|---|---|
| TD-008 | Unused `CodingDomainProfile.entity_hint` — defined but not consumed by any prompt builder or hidden-test generation component | `services/question_intelligence/coding_domain_profile_registry.py` | Low | DEFERRED | — |
| TD-001 | Semantic diversity embeddings unavailable at retrieval time | Retrieval pipeline | High | OPEN | ADR-005 |
| TD-002 | Double embedding generation in corpus build | `scripts/question_corpus/build_chroma_corpus.py` | Medium | OPEN | ADR-005 |
| TD-005 | Extract `TargetAreaResolver` | `services/question_intelligence/` | Low | OPEN | — |
| TD-006 | `domains=[area.value]` mapper — area conflated with domain | Mapper layer | Medium | OPEN | — |
| TD-007 | `_ACTIONABLE_SQL_PATTERN` filter excludes valid DB questions | SQL ingestion | Medium | OPEN | — |

### Ingestion / Adapters

| ID | Item | Location | Severity | Status | ADR |
|---|---|---|---|---|---|
| TD-IN-001 | `AdapterRegistry` — 7+ adapters exist, only 3 registered | `services/question_ingestion/adapters/adapter_registry.py` | Medium | OPEN | ADR-013 |
| TD-IN-002 | No semantic tags / skill extraction in `GenericDatasetAdapter` | `generic_dataset_adapter.py` | Low | OPEN | — |
| TD-IN-003 | Missing `batch_id`, `dataset_name`, `origin_url` on `RawQuestionRecord` | `raw_question_record.py` | Low | OPEN | — |

### Type Safety

| ID | Item | Location | Severity | Status |
|---|---|---|---|---|
| TD-TS-001 | `Any` on report types | `services/report_export_service.py` | Medium | OPEN |
| TD-TS-002 | `Any` in `observing_llm_adapter.py` | `infrastructure/llm/` | Low | OPEN |
| TD-TS-003 | `Any` in `decision_explanation_generator.py` | `services/decision_engine/` | Low | OPEN |

### Documentation

| ID | Item | Severity | Status |
|---|---|---|---|
| TD-DOC-001 | `README.md` describes wrong product | High | OPEN |
| TD-DOC-002 | `system_overview.md` states Chroma "planned" — already implemented | Low | OPEN |
| TD-DOC-003 | No `.env.example` | High | OPEN |
| TD-DOC-004 | No configuration reference doc | High | OPEN |

### Test Coverage

| ID | Item | Location | Severity | Status |
|---|---|---|---|---|
| TD-TC-001 | Decision engine untested | `services/decision_engine/` | High | OPEN |
| TD-TC-002 | Planning phases untested | `services/interview_planning/phases/` | High | OPEN |
| TD-TC-003 | `evaluation_aggregate_node` no dedicated test | `app/graph/nodes/` | Medium | OPEN |
| TD-TC-004 | SQLite persistence untested | `infrastructure/persistence/sqlite/` | Medium | OPEN |
| TD-TC-005 | All `domain/events/` untested | `domain/events/` | Low | OPEN |
| TD-TC-006 | `NavigationPolicy`, `DecisionPolicy` untested | `domain/policies/` | Medium | OPEN |
| TD-TC-007 | `AdaptiveNavigationNode` no direct test | `app/graph/nodes/` | Medium | OPEN |
| TD-TC-008 | Feedback aggregation untested | `services/feedback_aggregation/` | Medium | OPEN |
| TD-TC-009 | `ReportExportService` untested | `services/report_export_service.py` | Low | OPEN |

---

## Closed Items

| ID | Item | Closed In | Notes |
|---|---|---|---|
| TD-003 | Duplicate RetrievalDocument contracts | — | Legacy retrieval removed |
| TD-004 | Legacy `services/retrieval` | — | Removed |

---

## Diversity Debt (Phase 7C-T)

| Slice | Issue | Status |
|---|---|---|
| `technical_background` | Cross-interview diversity objectives not met | OPEN |
| `technical_technical_knowledge` | Cross-interview diversity objectives not met | OPEN |

---

## Deferred Items

| ID | Item | Reason | Target |
|---|---|---|---|
| — | LangGraph follow-up wiring | V1.1 scope | V1.1 |
| TD-IN-001 | Full adapter registry migration | V1.1 scope | V1.1 |
| TD-008 | Unused `CodingDomainProfile.entity_hint` — introduce `entity_hint` prompt block or remove the field | No active consumer; low risk | V1.1 |
