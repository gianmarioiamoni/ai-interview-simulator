# scripts/question_corpus/build_technical_case_study_expansion.py

# Phase 7C-T1 — Technical case study corpus expansion (data/qa/ml × junior/mid).

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPANSION_PATH = (
    PROJECT_ROOT / "datasets/curated/local_import/technical_case_study_expansion.json"
)
VALIDATION_PATH = (
    PROJECT_ROOT / "scripts/question_intelligence/output/phase_7c_t1_expansion_report.json"
)

SOURCE = "manual_seed/technical_case_study_expansion_7c_t1"
AREA = "technical_case_study"

SENIORITY_DIFFICULTY = {
    "junior": 2,
    "mid": 3,
}

ROLE_DOMAINS = {
    "data_engineer": "data_engineering",
    "qa_engineer": "quality_assurance",
    "ml_engineer": "machine_learning",
}

NEW_QUESTIONS: list[dict] = [
    # data_engineer / junior (8)
    {
        "id": "tcs_de_junior_late_events_001",
        "question": "A daily sales aggregation pipeline is missing revenue from orders that arrive after midnight UTC. How would you redesign ingestion and partitioning so late-arriving events are captured without full reprocessing every day?",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["late_arriving_data", "partitioning", "idempotency"],
        "tags": ["etl", "batch"],
    },
    {
        "id": "tcs_de_junior_dup_rows_002",
        "question": "Analysts report duplicate customer records in the warehouse after a new upstream feed launched. Walk through how you would trace the pipeline, identify the deduplication gap, and propose a fix with validation checks.",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["data_quality", "deduplication", "lineage"],
        "tags": ["warehouse", "debugging"],
    },
    {
        "id": "tcs_de_junior_schema_migrate_003",
        "question": "Product added nullable JSON attributes to an events table used by five downstream dashboards. How would you plan a backward-compatible schema migration without breaking existing SQL models?",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["schema_evolution", "compatibility", "rollout"],
        "tags": ["schema", "migration"],
    },
    {
        "id": "tcs_de_junior_backfill_004",
        "question": "An upstream API was down for six hours and you need to backfill missing events into the lake. Describe your backfill strategy, ordering guarantees, and how you prevent double-counting metrics.",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["backfill", "idempotency", "recovery"],
        "tags": ["pipeline", "reliability"],
    },
    {
        "id": "tcs_de_junior_dq_checks_005",
        "question": "Finance flagged inconsistent totals between raw and curated layers. Design a set of automated data-quality checks you would run between ingestion and publishing to catch this class of issue early.",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["data_quality", "validation", "monitoring"],
        "tags": ["dq", "checks"],
    },
    {
        "id": "tcs_de_junior_log_partition_006",
        "question": "Application logs grew 10× in one quarter. How would you choose a partitioning and retention scheme for the data lake that balances query performance, storage cost, and compliance retention?",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["partitioning", "retention", "cost"],
        "tags": ["data_lake", "logs"],
    },
    {
        "id": "tcs_de_junior_cost_query_007",
        "question": "A recurring analyst query scans an entire fact table and is driving warehouse cost up. What steps would you take to diagnose the query pattern and recommend a cheaper architecture or materialization?",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["cost_optimization", "materialization", "query_patterns"],
        "tags": ["warehouse", "performance"],
    },
    {
        "id": "tcs_de_junior_csv_ingest_008",
        "question": "A partner delivers daily CSV drops via SFTP with occasional malformed rows. How would you design an ingestion job that quarantines bad records, alerts owners, and still loads clean data on schedule?",
        "role": "data_engineer",
        "seniority": "junior",
        "expected_topics": ["ingestion", "error_handling", "alerting"],
        "tags": ["etl", "files"],
    },
    # data_engineer / mid (8)
    {
        "id": "tcs_de_mid_stream_batch_001",
        "question": "Product wants near-real-time inventory counts but finance requires audited daily snapshots. How would you architect streaming and batch paths that share one source of truth without conflicting numbers?",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["lambda_architecture", "consistency", "audit"],
        "tags": ["streaming", "batch"],
    },
    {
        "id": "tcs_de_mid_scd2_002",
        "question": "Customer attributes change over time and marketing needs historical segmentation. Explain how you would model slowly changing dimensions and expose both current and point-in-time views.",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["scd", "modeling", "historical_analysis"],
        "tags": ["warehouse", "modeling"],
    },
    {
        "id": "tcs_de_mid_lineage_003",
        "question": "Compliance asks which dashboards depend on a column that may contain PII. How would you implement lineage capture and impact analysis across ingestion, transforms, and BI layers?",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["lineage", "pii", "impact_analysis"],
        "tags": ["governance", "compliance"],
    },
    {
        "id": "tcs_de_mid_multi_tenant_004",
        "question": "Your platform onboarded enterprise tenants that must never see each other's data. Describe isolation options at storage, query, and orchestration layers and the trade-offs of each.",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["multi_tenancy", "isolation", "security"],
        "tags": ["architecture", "enterprise"],
    },
    {
        "id": "tcs_de_mid_freshness_sla_005",
        "question": "Executives want a 15-minute freshness SLA for revenue metrics while batch costs must stay flat. How would you evaluate incremental models, streaming aggregates, and caching to hit the SLA?",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["sla", "freshness", "trade_offs"],
        "tags": ["metrics", "cost"],
    },
    {
        "id": "tcs_de_mid_cdc_006",
        "question": "You need to replicate OLTP changes into the warehouse with minimal load on production databases. Compare CDC approaches and outline the end-to-end pipeline you would implement.",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["cdc", "replication", "oltp"],
        "tags": ["pipeline", "database"],
    },
    {
        "id": "tcs_de_mid_data_contract_007",
        "question": "Upstream teams ship breaking schema changes without notice. How would you introduce data contracts, versioning, and enforcement so downstream pipelines fail safely instead of silently corrupting metrics?",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["data_contracts", "versioning", "enforcement"],
        "tags": ["governance", "schema"],
    },
    {
        "id": "tcs_de_mid_dr_warehouse_008",
        "question": "Regional outage took the primary warehouse offline for four hours. Describe a disaster-recovery design including backup frequency, replay procedures, and RPO/RTO targets you would commit to.",
        "role": "data_engineer",
        "seniority": "mid",
        "expected_topics": ["disaster_recovery", "rpo_rto", "replication"],
        "tags": ["reliability", "operations"],
    },
    # qa_engineer / junior (8)
    {
        "id": "tcs_qa_junior_release_strategy_001",
        "question": "A mobile team ships weekly releases with shrinking manual test time. How would you design a risk-based test strategy that prioritizes critical user journeys while keeping release confidence high?",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["test_strategy", "risk_based", "mobile"],
        "tags": ["release", "planning"],
    },
    {
        "id": "tcs_qa_junior_api_regression_002",
        "question": "A REST API grew to 120 endpoints with frequent breaking changes. Outline how you would structure automated regression tests, test data, and CI gates for pull requests.",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["api_testing", "automation", "ci"],
        "tags": ["regression", "api"],
    },
    {
        "id": "tcs_qa_junior_bug_triage_003",
        "question": "Production bug reports spiked after a feature flag rollout. Describe your triage workflow from intake to reproducible test case, including severity assignment and developer handoff.",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["bug_triage", "reproduction", "severity"],
        "tags": ["process", "incident"],
    },
    {
        "id": "tcs_qa_junior_test_data_004",
        "question": "Integration tests fail intermittently because shared staging data is mutated by other teams. How would you design isolated test data provisioning for parallel CI runs?",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["test_data", "isolation", "ci"],
        "tags": ["staging", "fixtures"],
    },
    {
        "id": "tcs_qa_junior_smoke_ci_005",
        "question": "Deployments happen multiple times per day. What smoke test suite would you run in CI immediately after deploy, and how would you keep it fast enough to avoid blocking releases?",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["smoke_tests", "deployment", "fast_feedback"],
        "tags": ["ci", "cd"],
    },
    {
        "id": "tcs_qa_junior_exploratory_006",
        "question": "A redesigned checkout flow launches tomorrow with incomplete documentation. How would you plan exploratory testing sessions to uncover high-risk gaps before go-live?",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["exploratory_testing", "charters", "risk"],
        "tags": ["ux", "checkout"],
    },
    {
        "id": "tcs_qa_junior_defect_escape_007",
        "question": "Defect escape rate doubled last quarter. Walk through how you would analyze escaped defects, identify systemic gaps in coverage, and propose measurable improvements.",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["defect_analysis", "coverage_gaps", "metrics"],
        "tags": ["quality", "metrics"],
    },
    {
        "id": "tcs_qa_junior_cross_browser_008",
        "question": "Users report layout bugs only on Safari mobile. How would you design a cross-browser test approach that balances device coverage with maintainability?",
        "role": "qa_engineer",
        "seniority": "junior",
        "expected_topics": ["cross_browser", "mobile", "test_design"],
        "tags": ["frontend", "compatibility"],
    },
    # qa_engineer / mid (8)
    {
        "id": "tcs_qa_mid_e2e_framework_001",
        "question": "E2E tests are brittle and owned by multiple squads. How would you design a shared framework with page objects, stable selectors, and clear ownership boundaries?",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["e2e", "framework", "maintainability"],
        "tags": ["automation", "architecture"],
    },
    {
        "id": "tcs_qa_mid_perf_strategy_002",
        "question": "Checkout latency regressions reached production twice this year. Describe a performance testing strategy covering load profiles, environments, thresholds, and release gates.",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["performance_testing", "thresholds", "gates"],
        "tags": ["load", "sla"],
    },
    {
        "id": "tcs_qa_mid_env_provision_003",
        "question": "Teams wait days for staging environments with correct dependencies. How would you design on-demand environment provisioning integrated with test pipelines?",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["test_environments", "provisioning", "dependencies"],
        "tags": ["infra", "ci"],
    },
    {
        "id": "tcs_qa_mid_release_gate_004",
        "question": "Leadership wants objective release quality criteria instead of subjective sign-off. What metrics, test tiers, and waiver process would you institutionalize as a release gate?",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["release_gates", "metrics", "governance"],
        "tags": ["process", "quality"],
    },
    {
        "id": "tcs_qa_mid_flaky_tests_005",
        "question": "Thirty percent of nightly failures are flaky tests ignored by engineers. How would you detect, quarantine, and systematically reduce flakiness without hiding real defects?",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["flaky_tests", "quarantine", "reliability"],
        "tags": ["ci", "stability"],
    },
    {
        "id": "tcs_qa_mid_security_testing_006",
        "question": "A security audit found auth bypass paths missed by functional tests. How would you integrate security test cases and tooling into the SDLC without blocking all delivery?",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["security_testing", "sdlc", "auth"],
        "tags": ["security", "integration"],
    },
    {
        "id": "tcs_qa_mid_contract_testing_007",
        "question": "Microservices break each other via undocumented API changes. Explain how you would introduce contract testing between providers and consumers in CI.",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["contract_testing", "microservices", "ci"],
        "tags": ["api", "pact"],
    },
    {
        "id": "tcs_qa_mid_test_observability_008",
        "question": "When E2E fails in CI, engineers cannot tell whether the app, test, or environment broke. What observability signals and artifacts would you attach to test runs for faster diagnosis?",
        "role": "qa_engineer",
        "seniority": "mid",
        "expected_topics": ["observability", "debugging", "artifacts"],
        "tags": ["ci", "diagnostics"],
    },
    # ml_engineer / junior (8)
    {
        "id": "tcs_ml_junior_imbalance_split_001",
        "question": "A fraud model trains on a dataset with 0.3% positive labels. How would you design train/validation/test splits and sampling strategy so offline metrics reflect production behavior?",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["class_imbalance", "sampling", "evaluation"],
        "tags": ["training", "metrics"],
    },
    {
        "id": "tcs_ml_junior_feature_pipeline_002",
        "question": "Batch predictions need features built from raw clickstream with a 24-hour window. Outline a feature pipeline that is reproducible between training and batch inference.",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["feature_pipeline", "reproducibility", "batch"],
        "tags": ["features", "inference"],
    },
    {
        "id": "tcs_ml_junior_monitor_basics_003",
        "question": "A recommendation model shipped last month with no monitoring. What minimum online metrics and alerts would you add first to detect obvious failure modes?",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["monitoring", "alerts", "recommendation"],
        "tags": ["production", "ops"],
    },
    {
        "id": "tcs_ml_junior_data_drift_004",
        "question": "Input feature distributions shifted after a product UI change. Describe how you would detect drift, assess impact on model quality, and decide whether to retrain.",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["data_drift", "detection", "retraining"],
        "tags": ["monitoring", "quality"],
    },
    {
        "id": "tcs_ml_junior_ab_rollout_005",
        "question": "You must roll out a new ranking model without harming core engagement metrics. How would you design an A/B experiment, success criteria, and rollback triggers?",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["ab_testing", "rollout", "rollback"],
        "tags": ["experimentation", "deployment"],
    },
    {
        "id": "tcs_ml_junior_labeling_006",
        "question": "Human labelers disagree on 25% of moderation cases. How would you design a labeling workflow, adjudication process, and quality metrics before training?",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["labeling", "inter_annotator_agreement", "workflow"],
        "tags": ["data", "quality"],
    },
    {
        "id": "tcs_ml_junior_baseline_007",
        "question": "Stakeholders want a new churn model but no baseline exists. What simple baselines would you implement first and how would you justify moving to a complex model?",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["baselines", "model_selection", "justification"],
        "tags": ["evaluation", "churn"],
    },
    {
        "id": "tcs_ml_junior_offline_metrics_008",
        "question": "Product cares about ranking quality at the top of results, not average error. Which offline metrics would you choose for a search relevance model and why?",
        "role": "ml_engineer",
        "seniority": "junior",
        "expected_topics": ["ranking_metrics", "ndcg", "evaluation"],
        "tags": ["search", "metrics"],
    },
    # ml_engineer / mid (8)
    {
        "id": "tcs_ml_mid_realtime_infer_001",
        "question": "A fraud scoring service must respond in under 50ms at peak checkout traffic. How would you architect feature lookup, model serving, and fallback behavior to meet latency SLOs?",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["real_time_inference", "latency", "serving"],
        "tags": ["architecture", "fraud"],
    },
    {
        "id": "tcs_ml_mid_feature_store_002",
        "question": "Training and serving teams compute different versions of the same features. Design a feature store approach that guarantees point-in-time correctness for training and online lookup.",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["feature_store", "point_in_time", "consistency"],
        "tags": ["features", "platform"],
    },
    {
        "id": "tcs_ml_mid_retrain_pipeline_003",
        "question": "Model quality decays as user behavior shifts seasonally. Outline a scheduled retraining pipeline including data validation, champion/challenger evaluation, and safe promotion.",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["retraining", "champion_challenger", "promotion"],
        "tags": ["mlops", "pipeline"],
    },
    {
        "id": "tcs_ml_mid_multi_model_serve_004",
        "question": "Personalization requires ensemble models per segment with different SLAs. How would you design multi-model serving, routing, and capacity planning on shared infrastructure?",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["model_serving", "routing", "capacity"],
        "tags": ["ensemble", "scale"],
    },
    {
        "id": "tcs_ml_mid_explainability_005",
        "question": "Regulators require explainability for credit risk decisions. How would you integrate interpretability methods into training, evaluation, and the customer-facing decision API?",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["explainability", "compliance", "risk"],
        "tags": ["governance", "api"],
    },
    {
        "id": "tcs_ml_mid_cost_latency_006",
        "question": "GPU inference costs doubled after model size increased. Compare optimization options—distillation, batching, hardware tiering—and how you would measure trade-offs before committing.",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["cost_optimization", "latency", "distillation"],
        "tags": ["serving", "efficiency"],
    },
    {
        "id": "tcs_ml_mid_experiment_tracking_007",
        "question": "Researchers cannot reproduce experiments from three months ago. Design an experiment tracking system covering datasets, code versions, hyperparameters, and artifact storage.",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["experiment_tracking", "reproducibility", "artifacts"],
        "tags": ["mlops", "research"],
    },
    {
        "id": "tcs_ml_mid_concept_drift_008",
        "question": "Conversion model precision dropped while data drift alerts stayed green. How would you detect concept drift, isolate affected cohorts, and coordinate retraining with product stakeholders?",
        "role": "ml_engineer",
        "seniority": "mid",
        "expected_topics": ["concept_drift", "cohort_analysis", "retraining"],
        "tags": ["monitoring", "production"],
    },
]


def _make_id(question: str, area: str) -> str:
    digest = hashlib.sha256(f"{area}:{question}".encode()).hexdigest()[:16]
    return f"tcs_{digest}"


def _to_entry(spec: dict) -> dict:
    question = spec["question"].strip()
    seniority = spec["seniority"]
    role = spec["role"]

    return {
        "id": spec.get("id") or _make_id(question, AREA),
        "question": question,
        "role": role,
        "seniority": seniority,
        "area": AREA,
        "domains": [ROLE_DOMAINS.get(role, AREA)],
        "difficulty": spec.get("difficulty", SENIORITY_DIFFICULTY[seniority]),
        "source": spec.get("source", SOURCE),
        "quality_score": 0.9,
        "tags": list(spec.get("tags", [])),
        "expected_topics": list(spec.get("expected_topics", [])),
        "follow_up_hints": [],
    }


def _validate_entries(entries: list[dict]) -> dict:
    required_keys = {
        "id",
        "question",
        "role",
        "seniority",
        "area",
        "domains",
        "difficulty",
        "source",
    }

    errors: list[str] = []
    ids = [entry["id"] for entry in entries]

    if len(ids) != len(set(ids)):
        errors.append("duplicate_ids_detected")

    slice_counts: Counter[tuple[str, str]] = Counter()

    for index, entry in enumerate(entries):
        missing = required_keys - set(entry.keys())

        if missing:
            errors.append(f"entry_{index}_missing_{sorted(missing)}")

        if entry.get("area") != AREA:
            errors.append(f"entry_{index}_wrong_area")

        if not 2 <= int(entry.get("difficulty", 0)) <= 4:
            errors.append(f"entry_{index}_difficulty_out_of_fresh_start_range")

        slice_counts[(entry["role"], entry["seniority"])] += 1

    target_slices = {
        ("data_engineer", "junior"),
        ("data_engineer", "mid"),
        ("qa_engineer", "junior"),
        ("qa_engineer", "mid"),
        ("ml_engineer", "junior"),
        ("ml_engineer", "mid"),
    }

    slice_validation = {
        f"{role}/{seniority}": slice_counts.get((role, seniority), 0)
        for role, seniority in sorted(target_slices)
    }

    for role, seniority in target_slices:
        if slice_counts.get((role, seniority), 0) < 8:
            errors.append(f"slice_{role}_{seniority}_under_8")

    return {
        "entry_count": len(entries),
        "unique_ids": len(set(ids)),
        "schema_valid": len(errors) == 0,
        "errors": errors,
        "slice_counts": slice_validation,
    }


def _load_case_study_from_roots() -> list[dict]:
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
                    "id": question.id,
                    "area": question.area.value,
                    "role": question.role.value,
                    "seniority": question.seniority.value,
                    "difficulty": question.difficulty,
                }
            )

    return items


def _strict_filter_survival(items: list[dict]) -> dict:
    from domain.contracts.user.role import RoleType
    from domain.contracts.user.seniority_level import SeniorityLevel

    zero_match = 0
    lte_3 = 0
    gte_10 = 0

    for role in RoleType:
        for seniority in SeniorityLevel:
            count = sum(
                1
                for item in items
                if item["role"] == role.value
                and item["seniority"] == seniority.value
                and 2 <= int(item["difficulty"]) <= 4
            )

            if count == 0:
                zero_match += 1
            elif count <= 3:
                lte_3 += 1
            elif count >= 10:
                gte_10 += 1

    role_counts = Counter(item["role"] for item in items)
    seniority_counts = Counter(item["seniority"] for item in items)
    total = len(items)

    return {
        "total_documents": total,
        "zero_match_cells": zero_match,
        "lte_3_cells": lte_3,
        "gte_10_cells": gte_10,
        "role_distribution": dict(role_counts),
        "seniority_distribution": dict(seniority_counts),
        "role_concentration_pct": {
            role: round(count / total * 100, 1) for role, count in role_counts.items()
        },
        "seniority_concentration_pct": {
            level: round(count / total * 100, 1)
            for level, count in seniority_counts.items()
        },
        "target_slices": {
            f"{role}/{seniority}": sum(
                1
                for item in items
                if item["role"] == role
                and item["seniority"] == seniority
                and 2 <= int(item["difficulty"]) <= 4
            )
            for role, seniority in [
                ("data_engineer", "junior"),
                ("data_engineer", "mid"),
                ("qa_engineer", "junior"),
                ("qa_engineer", "mid"),
                ("ml_engineer", "junior"),
                ("ml_engineer", "mid"),
            ]
        },
    }


def _before_stats() -> dict:
    return {
        "total_documents": 176,
        "zero_match_cells": 13,
        "role_distribution_top": {"backend_engineer": 163},
        "seniority_distribution_top": {"senior": 165},
        "b2d_reuse_pct": 35.0,
        "b2d_unique": 13,
    }


def main() -> None:
    entries = [_to_entry(spec) for spec in NEW_QUESTIONS]

    validation = _validate_entries(entries)

    if not validation["schema_valid"]:
        raise ValueError(f"Expansion validation failed: {validation['errors']}")

    EXPANSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPANSION_PATH.write_text(
        json.dumps(entries, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    after_items = _load_case_study_from_roots()
    survival = _strict_filter_survival(after_items)

    report = {
        "phase": "7C-T1 Technical Case Study Corpus Expansion",
        "expansion_file": str(EXPANSION_PATH.relative_to(PROJECT_ROOT)),
        "new_documents": len(entries),
        "schema_validation": validation,
        "corpus_counts": {
            "before_indexed_area_total": _before_stats()["total_documents"],
            "after_source_area_total": len(after_items),
            "delta": len(after_items) - _before_stats()["total_documents"],
        },
        "coverage": survival,
        "before_baseline": _before_stats(),
        "coverage_targets": {
            "zero_match_cells_lte_3": survival["zero_match_cells"] <= 3,
            "every_role_represented": len(survival["role_distribution"]) >= 6,
            "target_slices_gte_8": all(
                count >= 8 for count in survival["target_slices"].values()
            ),
        },
    }

    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nWrote expansion: {EXPANSION_PATH}")
    print(f"Report: {VALIDATION_PATH}")


if __name__ == "__main__":
    main()
