# Documentation Index — AI Interview Simulator v1

## Documentation Tree

```
docs/
├── INDEX.md                              ← THIS FILE (master index)
├── technical-debt-register.md            ← TD tracker [Required]
│
├── architecture/
│   ├── ARCHITECTURE-INDEX.md             ← cross-reference map [Required]
│   ├── system_overview.md                ← system vision & layers [Required]
│   ├── runtime-flow.md                   ← LangGraph pipeline [Required]
│   ├── ui-architecture.md                ← UI state machine [Required]
│   ├── evaluation-pipeline.md            ← eval/feedback/decision chain [Required]
│   ├── question-intelligence.md          ← pipelines/registries/retrieval [Required] MISSING
│   ├── graph-nodes.md                    ← per-node contract reference [Required] MISSING
│   ├── ingestion.md                      ← adapter ABC & registry guide [Recommended] MISSING
│   ├── configuration.md                  ← env vars & constants reference [Required] MISSING
│   ├── feature-flags.md                  ← all flags, defaults, locations [Recommended] MISSING
│   ├── domain-contracts.md               ← 67-contract index [Recommended] MISSING
│   ├── storage.md                        ← SQLite + Chroma split [Optional] MISSING
│   ├── testing-strategy.md               ← layer coverage policy [Recommended] MISSING
│   └── questions/
│       └── open_issues.md                ← active TD items [Required]
│
├── decisions/
│   ├── ADR-TEMPLATE.md                   ← template [Required]
│   ├── adr-001-intent-vs-last-action.md  ← [Accepted]
│   ├── adr-002-output-contract-refactor.md ← [Accepted]
│   ├── adr-003-state-driven-ui.md        ← [Accepted]
│   ├── adr-004-hybrid-question-intelligence.md [Proposed] MISSING
│   ├── adr-005-dual-embedding-strategy.md      [Proposed] MISSING
│   ├── adr-006-business-context-profiles.md    [Proposed] MISSING
│   ├── adr-007-domain-layer-exceptions.md      [Proposed] MISSING
│   ├── adr-008-dual-decision-policy.md         [Proposed] MISSING
│   ├── adr-009-adaptive-interview-path.md      [Proposed] MISSING
│   ├── adr-010-humanizer-follow-up-system.md   [Proposed] MISSING
│   ├── adr-011-evaluation-governance.md        [Proposed] MISSING
│   ├── adr-012-prompt-centralization.md        [Proposed] MISSING
│   ├── adr-013-partial-adapter-registry.md     [Proposed] MISSING
│   ├── adr-014-langgraph-sufficiency.md        [Proposed] MISSING
│   └── adr-015-storage-backend-split.md        [Proposed] MISSING
│
├── runbooks/
│   ├── corpus-build.md                   ← Chroma corpus ops [Recommended] MISSING
│   ├── deployment-huggingface.md         ← HF Spaces deploy [Recommended] MISSING
│   └── ingestion-run.md                  ← dataset ingestion ops [Optional] MISSING
│
└── roadmap/
    └── roadmap.md                        ← feature roadmap [Required]
```

---

## Document Registry

### Architecture

| Document | Status | Owner | SSOT For | Update Trigger |
|---|---|---|---|---|
| `system_overview.md` | Exists / Partially stale | Arch | Vision, layers, stack | Major feature addition |
| `runtime-flow.md` | Exists / Current | Arch | LangGraph pipeline, intent routing | Node add/remove |
| `ui-architecture.md` | Exists / Current | Arch | UIStateMachine, UIResponseBuilder | UI refactor |
| `evaluation-pipeline.md` | Exists / Current | Arch | Eval/hint/feedback/decision chain | Pipeline change |
| `question-intelligence.md` | **MISSING** [Required] | Services | Pipelines, registries, retrieval strategy | Any QI change |
| `graph-nodes.md` | **MISSING** [Required] | Arch | Per-node inputs/outputs/side-effects | Node change |
| `ingestion.md` | **MISSING** [Recommended] | Services | Adapter ABC, registry, dataset loaders | Adapter change |
| `configuration.md` | **MISSING** [Required] | Infra | All env vars + evaluation constants | Any config change |
| `feature-flags.md` | **MISSING** [Recommended] | Arch | All flags, defaults, locations | Flag add/remove |
| `domain-contracts.md` | **MISSING** [Recommended] | Domain | 67-contract catalog + layer rules | Contract change |
| `storage.md` | **MISSING** [Optional] | Infra | SQLite + Chroma topology | Storage change |
| `testing-strategy.md` | **MISSING** [Recommended] | QA | Layer test policy, coverage targets | Test standard change |
| `open_issues.md` | Exists / Active | Arch | Active TD items (TD-001–007) | Any TD triage |

### Decisions

| ADR | Status | Owner | Decision Scope |
|---|---|---|---|
| ADR-001 | Accepted | Arch | `state.intent` as orchestration driver |
| ADR-002 | Accepted | Arch | Semantic dict output contract |
| ADR-003 | Accepted | Arch | State-driven UI |
| ADR-004 | **Proposed** | Arch | Hybrid QI (RAG + LLM + structured) |
| ADR-005 | **Proposed** | Infra | Dual embedding strategy |
| ADR-006 | **Proposed** | Services | Business-context profile registries |
| ADR-007 | **Proposed** | Domain | Domain layer boundary exceptions |
| ADR-008 | **Proposed** | Domain | Two DecisionPolicy concepts |
| ADR-009 | **Proposed** | Arch | Adaptive interview path |
| ADR-010 | **Proposed** | Services | Humanizer follow-up system |
| ADR-011 | **Proposed** | Infra | Evaluation governance centralization |
| ADR-012 | **Proposed** | Services | Prompt centralization |
| ADR-013 | **Proposed** | Services | Partial adapter registry |
| ADR-014 | **Proposed** | Arch | LangGraph sufficiency |
| ADR-015 | **Proposed** | Infra | SQLite + Chroma split backends |

### Runbooks

| Document | Status | Owner | Update Trigger |
|---|---|---|---|
| `corpus-build.md` | **MISSING** [Recommended] | Infra | `scripts/question_corpus/` change |
| `deployment-huggingface.md` | **MISSING** [Recommended] | Ops | Deployment config change |
| `ingestion-run.md` | **MISSING** [Optional] | Services | Ingestion pipeline change |

---

## Priority Creation Order

1. `configuration.md` — P0, blocks onboarding
2. `question-intelligence.md` — P1, strategic SSOT
3. `graph-nodes.md` — P1, runtime reference
4. `ingestion.md` — P1, extension guide
5. ADR-004, ADR-007, ADR-008, ADR-011 — P1, highest-value undocumented decisions
6. `feature-flags.md` — P2
7. `domain-contracts.md` — P2
8. Remaining ADRs — P2
9. Runbooks — P2
10. `storage.md`, `testing-strategy.md` — P3

## Documentation Update Policy

Update documentation only when:

- a new subsystem is introduced
- an architectural decision is finalized
- a new extension point is added
- a new BusinessContext is added
- a new execution language is added
- a new registry/factory is introduced

Do not update documentation for normal feature work.
