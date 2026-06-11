# scripts/question_corpus/build_technical_case_study_gap_closure.py

# Phase 7C-T1B — Case study gap closure (11 zero-match slices × 4 docs).

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPANSION_PATH = (
    PROJECT_ROOT / "datasets/curated/local_import/technical_case_study_gap_closure.json"
)
REPORT_PATH = (
    PROJECT_ROOT / "scripts/question_intelligence/output/phase_7c_t1b_expansion_report.json"
)

SOURCE = "manual_seed/technical_case_study_gap_closure_7c_t1b"
AREA = "technical_case_study"

SENIORITY_DIFFICULTY = {
    "junior": 2,
    "mid": 3,
    "senior": 4,
}

ROLE_DOMAINS = {
    "backend_engineer": "backend_engineering",
    "frontend_engineer": "frontend_engineering",
    "fullstack_engineer": "fullstack_engineering",
    "devops_engineer": "devops",
    "data_engineer": "data_engineering",
    "qa_engineer": "quality_assurance",
    "ml_engineer": "machine_learning",
    "other": "general_engineering",
}

ZERO_MATCH_SLICES = [
    ("backend_engineer", "junior"),
    ("frontend_engineer", "junior"),
    ("fullstack_engineer", "junior"),
    ("fullstack_engineer", "senior"),
    ("devops_engineer", "junior"),
    ("data_engineer", "senior"),
    ("qa_engineer", "senior"),
    ("ml_engineer", "senior"),
    ("other", "junior"),
    ("other", "mid"),
    ("other", "senior"),
]

NEW_QUESTIONS: list[dict] = [
    # backend_engineer / junior (4)
    {
        "id": "tcs_be_junior_api_design_001",
        "question": "Your team is building a REST API for a todo app used by mobile clients. How would you design resource endpoints, pagination, and error responses so the API stays simple for junior developers to extend?",
        "role": "backend_engineer",
        "seniority": "junior",
        "expected_topics": ["api_design", "pagination", "errors"],
        "tags": ["rest", "backend"],
    },
    {
        "id": "tcs_be_junior_cache_layer_002",
        "question": "Read-heavy product pages are overloading the database. Propose a caching layer for a small backend service, including what to cache, TTL choices, and how you would validate cache correctness.",
        "role": "backend_engineer",
        "seniority": "junior",
        "expected_topics": ["caching", "read_load", "ttl"],
        "tags": ["redis", "performance"],
    },
    {
        "id": "tcs_be_junior_auth_flow_003",
        "question": "A startup needs email/password login with session tokens for a web app. Walk through the backend components you would implement and the security pitfalls you would avoid as a first version.",
        "role": "backend_engineer",
        "seniority": "junior",
        "expected_topics": ["authentication", "sessions", "security"],
        "tags": ["auth", "backend"],
    },
    {
        "id": "tcs_be_junior_job_queue_004",
        "question": "Users can export large CSV reports that time out when generated synchronously. How would you introduce a background job queue and status polling endpoint without blocking HTTP workers?",
        "role": "backend_engineer",
        "seniority": "junior",
        "expected_topics": ["job_queue", "async_processing", "exports"],
        "tags": ["workers", "backend"],
    },
    # frontend_engineer / junior (4)
    {
        "id": "tcs_fe_junior_form_validation_001",
        "question": "A multi-step signup form loses user input when validation fails on step three. How would you redesign state management and validation so users can recover without re-entering earlier steps?",
        "role": "frontend_engineer",
        "seniority": "junior",
        "expected_topics": ["forms", "validation", "state"],
        "tags": ["react", "ux"],
    },
    {
        "id": "tcs_fe_junior_list_virtual_002",
        "question": "A dashboard renders ten thousand rows and the browser freezes. Describe how you would implement list virtualization and loading indicators while keeping keyboard navigation usable.",
        "role": "frontend_engineer",
        "seniority": "junior",
        "expected_topics": ["virtualization", "performance", "accessibility"],
        "tags": ["rendering", "ui"],
    },
    {
        "id": "tcs_fe_junior_design_tokens_003",
        "question": "Designers shipped inconsistent button styles across pages. How would you introduce design tokens and a small component library so new screens stay visually consistent?",
        "role": "frontend_engineer",
        "seniority": "junior",
        "expected_topics": ["design_system", "components", "consistency"],
        "tags": ["css", "ui"],
    },
    {
        "id": "tcs_fe_junior_api_client_004",
        "question": "Frontend teams duplicate fetch logic and error handling in every screen. Outline a typed API client layer with retry rules and user-friendly error surfacing.",
        "role": "frontend_engineer",
        "seniority": "junior",
        "expected_topics": ["api_client", "error_handling", "typing"],
        "tags": ["fetch", "architecture"],
    },
    # fullstack_engineer / junior (4)
    {
        "id": "tcs_fs_junior_crud_app_001",
        "question": "You must deliver a small internal CRUD tool in two weeks covering UI, API, and database. How would you scope the MVP schema, API contracts, and UI flows to ship safely on deadline?",
        "role": "fullstack_engineer",
        "seniority": "junior",
        "expected_topics": ["mvp", "crud", "scoping"],
        "tags": ["fullstack", "delivery"],
    },
    {
        "id": "tcs_fs_junior_file_upload_002",
        "question": "Users need to upload profile images with preview and size limits. Describe an end-to-end design from browser upload through storage, virus scanning hook, and CDN delivery.",
        "role": "fullstack_engineer",
        "seniority": "junior",
        "expected_topics": ["file_upload", "storage", "cdn"],
        "tags": ["fullstack", "media"],
    },
    {
        "id": "tcs_fs_junior_search_feature_003",
        "question": "Product wants basic search across notes with autocomplete. Explain how you would implement indexing, API query parameters, and debounced UI search without over-engineering.",
        "role": "fullstack_engineer",
        "seniority": "junior",
        "expected_topics": ["search", "autocomplete", "indexing"],
        "tags": ["fullstack", "search"],
    },
    {
        "id": "tcs_fs_junior_feature_flag_004",
        "question": "A feature flag should expose a beta dashboard to 10% of users. How would you wire flag evaluation on backend and frontend and verify behavior in staging?",
        "role": "fullstack_engineer",
        "seniority": "junior",
        "expected_topics": ["feature_flags", "rollout", "testing"],
        "tags": ["fullstack", "flags"],
    },
    # fullstack_engineer / senior (4)
    {
        "id": "tcs_fs_senior_platform_migrate_001",
        "question": "A monolith powers five product lines and release risk is rising. How would you plan an incremental strangler migration to services while keeping shared auth and billing stable?",
        "role": "fullstack_engineer",
        "seniority": "senior",
        "expected_topics": ["strangler", "migration", "platform"],
        "tags": ["architecture", "decomposition"],
    },
    {
        "id": "tcs_fs_senior_multi_region_002",
        "question": "Leadership wants active-active deployment in two regions with session continuity for travelers. Describe the full-stack changes to routing, data replication, and conflict handling.",
        "role": "fullstack_engineer",
        "seniority": "senior",
        "expected_topics": ["multi_region", "sessions", "replication"],
        "tags": ["availability", "global"],
    },
    {
        "id": "tcs_fs_senior_realtime_collab_003",
        "question": "Teams want Google Docs-style co-editing on project specs. Outline websocket architecture, operational transform strategy, and permission model across API and UI.",
        "role": "fullstack_engineer",
        "seniority": "senior",
        "expected_topics": ["realtime", "collaboration", "websockets"],
        "tags": ["fullstack", "sync"],
    },
    {
        "id": "tcs_fs_senior_observability_004",
        "question": "Incidents take hours to trace across frontend, API, and workers. How would you design unified tracing, structured logging, and SLO dashboards for a fullstack platform?",
        "role": "fullstack_engineer",
        "seniority": "senior",
        "expected_topics": ["observability", "tracing", "slo"],
        "tags": ["operations", "platform"],
    },
    # devops_engineer / junior (4)
    {
        "id": "tcs_do_junior_ci_basics_001",
        "question": "Developers merge broken builds frequently. How would you design a CI pipeline for a small Node service with lint, unit tests, and artifact caching on pull requests?",
        "role": "devops_engineer",
        "seniority": "junior",
        "expected_topics": ["ci", "pipeline", "quality_gates"],
        "tags": ["devops", "ci"],
    },
    {
        "id": "tcs_do_junior_container_deploy_002",
        "question": "A team wants to move from manual server deploys to containers. Describe your first Docker-based deployment path, secrets handling, and rollback plan suitable for a junior on-call rotation.",
        "role": "devops_engineer",
        "seniority": "junior",
        "expected_topics": ["containers", "deployment", "rollback"],
        "tags": ["docker", "release"],
    },
    {
        "id": "tcs_do_junior_monitoring_003",
        "question": "Production lacks basic uptime monitoring. Propose metrics, alerts, and a runbook template for a single microservice without adopting a full observability suite on day one.",
        "role": "devops_engineer",
        "seniority": "junior",
        "expected_topics": ["monitoring", "alerting", "runbooks"],
        "tags": ["sre", "basics"],
    },
    {
        "id": "tcs_do_junior_env_parity_004",
        "question": "Staging behaves differently from production because configs drift. How would you structure environment variables, config validation, and promotion checks to improve parity?",
        "role": "devops_engineer",
        "seniority": "junior",
        "expected_topics": ["configuration", "environments", "parity"],
        "tags": ["devops", "config"],
    },
    # data_engineer / senior (4)
    {
        "id": "tcs_de_senior_lakehouse_001",
        "question": "Analytics teams outgrew the warehouse but lake queries are too slow for executives. How would you architect a lakehouse layer with governed gold tables and cost controls?",
        "role": "data_engineer",
        "seniority": "senior",
        "expected_topics": ["lakehouse", "governance", "performance"],
        "tags": ["data_platform", "architecture"],
    },
    {
        "id": "tcs_de_senior_privacy_002",
        "question": "GDPR deletion requests must propagate across twenty downstream datasets within 72 hours. Design lineage-aware deletion orchestration and audit evidence collection.",
        "role": "data_engineer",
        "seniority": "senior",
        "expected_topics": ["privacy", "deletion", "compliance"],
        "tags": ["gdpr", "lineage"],
    },
    {
        "id": "tcs_de_senior_streaming_sla_003",
        "question": "Real-time fraud features need five-minute freshness while batch finance needs daily reconciliation. Explain dual-path architecture with reconciliation checks between streams and warehouse.",
        "role": "data_engineer",
        "seniority": "senior",
        "expected_topics": ["streaming", "reconciliation", "sla"],
        "tags": ["lambda", "fraud"],
    },
    {
        "id": "tcs_de_senior_cost_govern_004",
        "question": "Warehouse spend doubled after self-serve BI adoption. How would you implement query attribution, budget alerts, and guardrails without blocking legitimate exploration?",
        "role": "data_engineer",
        "seniority": "senior",
        "expected_topics": ["cost_governance", "attribution", "guardrails"],
        "tags": ["finops", "warehouse"],
    },
    # qa_engineer / senior (4)
    {
        "id": "tcs_qa_senior_quality_strategy_001",
        "question": "Quality is reactive across twelve squads with duplicated test suites. How would you define a platform QA strategy with shared services, metrics, and squad autonomy boundaries?",
        "role": "qa_engineer",
        "seniority": "senior",
        "expected_topics": ["quality_strategy", "platform", "metrics"],
        "tags": ["leadership", "qa"],
    },
    {
        "id": "tcs_qa_senior_chaos_002",
        "question": "Leadership asks whether the payment flow survives dependency failures. Design a chaos testing program with blast radius controls, success criteria, and production learning loops.",
        "role": "qa_engineer",
        "seniority": "senior",
        "expected_topics": ["chaos_testing", "resilience", "payments"],
        "tags": ["reliability", "testing"],
    },
    {
        "id": "tcs_qa_senior_test_data_platform_003",
        "question": "Synthetic data generation is inconsistent and PII leaks into lower environments. Propose a centralized test data platform with masking, refresh SLAs, and consumption APIs for QA.",
        "role": "qa_engineer",
        "seniority": "senior",
        "expected_topics": ["test_data", "masking", "platform"],
        "tags": ["data", "compliance"],
    },
    {
        "id": "tcs_qa_senior_shift_left_004",
        "question": "Defects cluster in integration gaps between teams shipping independently. How would you institutionalize contract tests, quality gates, and defect budgets in the release train?",
        "role": "qa_engineer",
        "seniority": "senior",
        "expected_topics": ["shift_left", "contracts", "release_train"],
        "tags": ["process", "quality"],
    },
    # ml_engineer / senior (4)
    {
        "id": "tcs_ml_senior_platform_001",
        "question": "Ten product teams train models with incompatible tooling. How would you design an internal ML platform covering feature store, training pipelines, registry, and deployment standards?",
        "role": "ml_engineer",
        "seniority": "senior",
        "expected_topics": ["ml_platform", "registry", "standards"],
        "tags": ["mlops", "platform"],
    },
    {
        "id": "tcs_ml_senior_responsible_ai_002",
        "question": "A credit model must meet fairness and explainability requirements in multiple countries. Outline evaluation frameworks, monitoring, and human review workflows before production promotion.",
        "role": "ml_engineer",
        "seniority": "senior",
        "expected_topics": ["fairness", "explainability", "governance"],
        "tags": ["responsible_ai", "compliance"],
    },
    {
        "id": "tcs_ml_senior_multimodal_003",
        "question": "Support wants automated ticket routing using text and attachments. Describe architecture for multimodal ingestion, labeling, model versioning, and safe fallback to human agents.",
        "role": "ml_engineer",
        "seniority": "senior",
        "expected_topics": ["multimodal", "routing", "fallback"],
        "tags": ["nlp", "vision"],
    },
    {
        "id": "tcs_ml_senior_llm_ops_004",
        "question": "Product teams want LLM features with strict latency and cost caps. How would you design prompt management, caching, evaluation harnesses, and incident response for generative workloads?",
        "role": "ml_engineer",
        "seniority": "senior",
        "expected_topics": ["llm_ops", "evaluation", "cost_control"],
        "tags": ["generative", "production"],
    },
    # other / junior (4)
    {
        "id": "tcs_ot_junior_debug_prod_001",
        "question": "You joined a team and production errors spiked after your first deploy. Walk through how you would triage logs, isolate your change, and communicate status to stakeholders as a new engineer.",
        "role": "other",
        "seniority": "junior",
        "expected_topics": ["incident_response", "triage", "communication"],
        "tags": ["onboarding", "debugging"],
    },
    {
        "id": "tcs_ot_junior_code_review_002",
        "question": "Your pull request received extensive review comments on tests and naming. How would you prioritize fixes, ask clarifying questions, and prevent similar feedback on future changes?",
        "role": "other",
        "seniority": "junior",
        "expected_topics": ["code_review", "learning", "quality"],
        "tags": ["collaboration", "process"],
    },
    {
        "id": "tcs_ot_junior_estimation_003",
        "question": "A PM asks for an estimate on a vaguely defined feature. Describe how you would break down unknowns, propose milestones, and flag risks without over-committing.",
        "role": "other",
        "seniority": "junior",
        "expected_topics": ["estimation", "scoping", "communication"],
        "tags": ["planning", "delivery"],
    },
    {
        "id": "tcs_ot_junior_documentation_004",
        "question": "Runbooks for a critical service are outdated and onboarding takes weeks. Propose a lightweight documentation plan you could execute alongside feature work in your first quarter.",
        "role": "other",
        "seniority": "junior",
        "expected_topics": ["documentation", "onboarding", "runbooks"],
        "tags": ["knowledge", "ops"],
    },
    # other / mid (4)
    {
        "id": "tcs_ot_mid_cross_team_001",
        "question": "Two teams disagree on API ownership causing duplicate endpoints. How would you facilitate alignment on boundaries, deprecation, and a shared integration test plan?",
        "role": "other",
        "seniority": "mid",
        "expected_topics": ["cross_team", "api_ownership", "alignment"],
        "tags": ["collaboration", "architecture"],
    },
    {
        "id": "tcs_ot_mid_tech_debt_002",
        "question": "Leadership wants velocity up but engineers cite mounting tech debt. How would you quantify debt hotspots, propose incremental remediation, and tie improvements to measurable outcomes?",
        "role": "other",
        "seniority": "mid",
        "expected_topics": ["tech_debt", "prioritization", "metrics"],
        "tags": ["engineering", "strategy"],
    },
    {
        "id": "tcs_ot_mid_incident_lead_003",
        "question": "You are incident commander for a partial outage affecting checkout. Outline communication cadence, role delegation, mitigation sequencing, and post-incident follow-up.",
        "role": "other",
        "seniority": "mid",
        "expected_topics": ["incident_command", "communication", "mitigation"],
        "tags": ["operations", "leadership"],
    },
    {
        "id": "tcs_ot_mid_vendor_eval_004",
        "question": "Engineering must choose between building an internal tool or buying a SaaS vendor. Describe evaluation criteria, proof-of-concept design, and recommendation framing for leadership.",
        "role": "other",
        "seniority": "mid",
        "expected_topics": ["build_vs_buy", "evaluation", "decision"],
        "tags": ["strategy", "vendor"],
    },
    # other / senior (4)
    {
        "id": "tcs_ot_senior_org_design_001",
        "question": "Engineering growth created unclear ownership between platform and product teams. How would you propose team topology, interfaces, and metrics that reduce coordination tax?",
        "role": "other",
        "seniority": "senior",
        "expected_topics": ["org_design", "ownership", "platform"],
        "tags": ["leadership", "structure"],
    },
    {
        "id": "tcs_ot_senior_roadmap_002",
        "question": "Executives want a one-year technical roadmap balancing reliability, features, and compliance. Explain how you would gather inputs, sequence bets, and communicate trade-offs.",
        "role": "other",
        "seniority": "senior",
        "expected_topics": ["roadmap", "prioritization", "stakeholders"],
        "tags": ["strategy", "planning"],
    },
    {
        "id": "tcs_ot_senior_arch_review_003",
        "question": "A proposed architecture introduces a new data store for every feature team. Facilitate an architecture review covering consistency, operability, security, and long-term platform cost.",
        "role": "other",
        "seniority": "senior",
        "expected_topics": ["architecture_review", "governance", "cost"],
        "tags": ["review", "platform"],
    },
    {
        "id": "tcs_ot_senior_outage_postmortem_004",
        "question": "A major outage had multiple contributing factors across teams. How would you run a blameless postmortem and drive systemic fixes that stick beyond immediate patches?",
        "role": "other",
        "seniority": "senior",
        "expected_topics": ["postmortem", "blameless", "systemic_fixes"],
        "tags": ["reliability", "culture"],
    },
]


def _to_entry(spec: dict) -> dict:
    question = spec["question"].strip()
    seniority = spec["seniority"]
    role = spec["role"]

    return {
        "id": spec["id"],
        "question": question,
        "role": role,
        "seniority": seniority,
        "area": AREA,
        "domains": [ROLE_DOMAINS.get(role, AREA)],
        "difficulty": spec.get("difficulty", SENIORITY_DIFFICULTY[seniority]),
        "source": SOURCE,
        "quality_score": 0.9,
        "tags": list(spec.get("tags", [])),
        "expected_topics": list(spec.get("expected_topics", [])),
        "follow_up_hints": [],
    }


def _validate_entries(entries: list[dict]) -> dict:
    errors: list[str] = []
    ids = [entry["id"] for entry in entries]

    if len(ids) != len(set(ids)):
        errors.append("duplicate_ids")

    slice_counts: Counter[tuple[str, str]] = Counter()

    for index, entry in enumerate(entries):
        if entry.get("area") != AREA:
            errors.append(f"wrong_area_{index}")

        difficulty = int(entry.get("difficulty", 0))

        if not 2 <= difficulty <= 4:
            errors.append(f"difficulty_out_of_range_{index}")

        slice_counts[(entry["role"], entry["seniority"])] += 1

    for role, seniority in ZERO_MATCH_SLICES:
        if slice_counts.get((role, seniority), 0) != 4:
            errors.append(f"slice_{role}_{seniority}_not_four")

    return {
        "entry_count": len(entries),
        "unique_ids": len(set(ids)),
        "schema_valid": len(errors) == 0,
        "errors": errors,
        "slice_counts": {
            f"{role}/{seniority}": slice_counts.get((role, seniority), 0)
            for role, seniority in ZERO_MATCH_SLICES
        },
    }


def _load_case_study_items() -> list[dict]:
    from services.question_corpus.loaders.folder_corpus_loader import FolderCorpusLoader

    loader = FolderCorpusLoader()
    roots = [
        "datasets/curated/hf_import",
        "datasets/curated/interview_seed",
        "datasets/curated/local_import",
    ]

    items: list[dict] = []

    for root in roots:
        corpus = loader.load(str(PROJECT_ROOT / root))

        for question in corpus.questions:
            if question.area.value != AREA:
                continue

            items.append(
                {
                    "role": question.role.value,
                    "seniority": question.seniority.value,
                    "difficulty": question.difficulty,
                }
            )

    return items


def _survival_stats(items: list[dict]) -> dict:
    from domain.contracts.user.role import RoleType
    from domain.contracts.user.seniority_level import SeniorityLevel

    zero_match = 0
    slice_counts: dict[str, int] = {}

    for role in RoleType:
        for seniority in SeniorityLevel:
            count = sum(
                1
                for item in items
                if item["role"] == role.value
                and item["seniority"] == seniority.value
                and 2 <= int(item["difficulty"]) <= 4
            )
            slice_counts[f"{role.value}/{seniority.value}"] = count

            if count == 0:
                zero_match += 1

    role_counts = Counter(item["role"] for item in items)
    seniority_counts = Counter(item["seniority"] for item in items)

    return {
        "total_documents": len(items),
        "zero_match_cells": zero_match,
        "role_distribution": dict(role_counts),
        "seniority_distribution": dict(seniority_counts),
        "slice_counts": slice_counts,
        "previously_empty_slices_min": min(
            slice_counts[f"{role}/{seniority}"]
            for role, seniority in ZERO_MATCH_SLICES
        ),
    }


def main() -> None:
    entries = [_to_entry(spec) for spec in NEW_QUESTIONS]

    validation = _validate_entries(entries)

    if not validation["schema_valid"]:
        raise ValueError(f"Validation failed: {validation['errors']}")

    EXPANSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPANSION_PATH.write_text(
        json.dumps(entries, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    after_items = _load_case_study_items()
    survival = _survival_stats(after_items)

    report = {
        "phase": "7C-T1B Technical Case Study Gap Closure",
        "expansion_file": str(EXPANSION_PATH.relative_to(PROJECT_ROOT)),
        "new_documents": len(entries),
        "schema_validation": validation,
        "before_baseline_t1": {
            "indexed_docs": 224,
            "zero_match_cells": 11,
            "case_study_reuse_pct": 25.0,
            "case_study_unique": 15,
            "global_technical_reuse_pct": 17.0,
            "global_technical_unique": 83,
        },
        "coverage_after_source_load": survival,
        "coverage_targets": {
            "zero_match_cells_zero": survival["zero_match_cells"] == 0,
            "every_role_represented": len(survival["role_distribution"]) >= 8,
            "every_seniority_represented": len(survival["seniority_distribution"]) >= 3,
            "previously_empty_slices_min_gte_4": survival["previously_empty_slices_min"] >= 4,
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nWrote: {EXPANSION_PATH}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
