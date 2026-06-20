# Architecture Index & Cross-Reference Map

**Owner:** Arch
**Update Policy:** Updated when subsystem SSOT changes or new doc is added

---

## Subsystem → SSOT Map

| Subsystem | SSOT Document | Code SSOT | ADR |
|---|---|---|---|
| System vision & layers | `system_overview.md` | — | — |
| LangGraph pipeline / intent routing | `runtime-flow.md` | `app/graph/interview_graph.py` | ADR-001 |
| Graph node contracts | `graph-nodes.md` | `app/graph/nodes/` | ADR-014 |
| UI state machine | `ui-architecture.md` | `app/ui/` | ADR-002, ADR-003 |
| Eval/hint/feedback/decision chain | `evaluation-pipeline.md` | `app/graph/nodes/evaluation_node.py` + decision chain | — |
| Question intelligence pipelines | `question-intelligence.md` | `services/question_intelligence/` | ADR-004 |
| Embedding strategy | `question-intelligence.md` | `infrastructure/config/settings.py` | ADR-005 |
| Business-context profiles | `business-context.md` | `services/question_intelligence/coding_domain_profile_registry.py` | ADR-006 |
| SQL engine schemas & strategy | `sql-engine.md` | `services/sql_engine/schema_registry.py` | ADR-004, ADR-006 |
| Coding engine framing | `coding-engine.md` | `services/question_intelligence/pipelines/coding_question_pipeline.py` | ADR-004, ADR-006 |
| Dataset ingestion & adapters | `ingestion.md` | `services/question_ingestion/` | ADR-013 |
| Configuration & env vars | `configuration.md` | `infrastructure/config/settings.py` | ADR-011 |
| Evaluation governance constants | `configuration.md` | `infrastructure/config/evaluation.py` | ADR-011 |
| Feature flags | `feature-flags.md` | `settings.py` + `interview_state/base.py` + `decision_policy.py` | ADR-009, ADR-010 |
| Domain contracts catalog | `domain-contracts.md` ⚠️ MISSING | `domain/contracts/` (67 files) | ADR-007 |
| Domain layer boundary rules | `domain-contracts.md` ⚠️ MISSING | — | ADR-007 |
| Storage topology | `storage.md` ⚠️ MISSING | `infrastructure/persistence/` + `infrastructure/vector_store/` | ADR-015 |
| Adaptive interview path | `runtime-flow.md` (partial) | `services/interview_selection/lazy_adaptive_interview_service.py` | ADR-009 |
| Humanizer system | `feature-flags.md` + ADR-010 | `services/humanizer/` | ADR-010 |
| Prompt catalog | ADR-012 | `app/prompts/` | ADR-012 |
| Technical debt tracker | `technical-debt-register.md` + `questions/open_issues.md` | — | — |
| ADR registry | `docs/INDEX.md` + `docs/decisions/` | — | — |
| Roadmap | `roadmap/roadmap.md` | — | — |

---

## Cross-Reference Map

### `runtime-flow.md` ←→

| References | Referenced By |
|---|---|
| `system_overview.md` (layers) | `graph-nodes.md` (per-node detail) |
| ADR-001 (intent) | `evaluation-pipeline.md` (eval node) |
| `ui-architecture.md` (output) | `question-intelligence.md` (question node) |

### `evaluation-pipeline.md` ←→

| References | Referenced By |
|---|---|
| `runtime-flow.md` (node sequence) | `configuration.md` (governance constants) |
| ADR-011 (governance centralization) | `technical-debt-register.md` (TD-TC-001) |

### `question-intelligence.md` ←→ (MISSING)

| References | Referenced By |
|---|---|
| `ingestion.md` (upstream) | `runtime-flow.md` (question node) |
| ADR-004, ADR-005, ADR-006 | `configuration.md` (settings) |
| `technical-debt-register.md` (TD-001, TD-002, TD-005, TD-006, TD-007) | |

### `business-context.md` ←→ (MISSING)

| References | Referenced By |
|---|---|
| ADR-006 (parallel registries) | `question-intelligence.md` (profile lookup) |
| `sql-engine.md` (schema selection) | ADR-004 (strategy selection) |
| `coding-engine.md` (framing) | |

### `sql-engine.md` ←→ (MISSING)

| References | Referenced By |
|---|---|
| `business-context.md` (context → schema) | `question-intelligence.md` (SQL pipeline) |
| ADR-004, ADR-006 | |

### `coding-engine.md` ←→ (MISSING)

| References | Referenced By |
|---|---|
| `business-context.md` (context → framing) | `question-intelligence.md` (coding pipeline) |
| ADR-004, ADR-006 | |

### `configuration.md` ←→ (MISSING)

| References | Referenced By |
|---|---|
| `infrastructure/config/settings.py` | All subsystems |
| `infrastructure/config/evaluation.py` | `evaluation-pipeline.md` |
| ADR-011 | `feature-flags.md` |

---

## Document Dependency Order (creation priority)

```
system_overview.md (exists)
    └── runtime-flow.md (exists)
            ├── graph-nodes.md          
            └── evaluation-pipeline.md (exists)
                    └── configuration.md [P0]

question-intelligence.md [P1]
    ├── ingestion.md                    [P1]
    └── configuration.md               [P0]

domain-contracts.md [P2 — MISSING]
    └── ADR-007

feature-flags.md [P2 — MISSING]
    └── configuration.md

storage.md [P3 — MISSING]
    └── ADR-015
```

---

## Legend

- ⚠️ MISSING — document does not exist yet; see `docs/INDEX.md` for creation priority
- (exists) — document present and current
- (partial) — document exists but coverage is incomplete
