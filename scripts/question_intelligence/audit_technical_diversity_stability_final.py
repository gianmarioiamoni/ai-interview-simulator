# scripts/question_intelligence/audit_technical_diversity_stability_final.py

# Phase 7C-FINAL — Technical Diversity Stability Audit (read-only, 100 interviews).

from __future__ import annotations

import json
import random
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from infrastructure.llm.llm_adapter import DefaultLLMAdapter
from scripts.question_intelligence import audit_cross_interview_diversity as diversity_audit
from services.question_intelligence.question_intelligence_provider import (
    QuestionIntelligenceProvider,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "scripts/question_intelligence/output"

INTERVIEW_COUNT = 100
RANDOM_SEED = 20260611

TECH_AREAS = [
    "technical_background",
    "technical_technical_knowledge",
    "technical_case_study",
    "technical_coding",
    "technical_database",
]

EXPECTED_QUESTIONS_PER_INTERVIEW = 5

BASELINES = {
    "t0_technical_b2d": {
        "interviews": 20,
        "total_prompts": 100,
        "unique_prompts": 63,
        "reuse_pct": 37.0,
        "unique_rate_pct": 63.0,
        "technical_case_study_reuse_pct": 35.0,
        "technical_background_reuse_pct": 65.0,
        "technical_technical_knowledge_reuse_pct": 45.0,
    },
    "t2b_validation": {
        "interviews": 20,
        "total_prompts": 100,
        "unique_prompts": 83,
        "reuse_pct": 17.0,
        "unique_rate_pct": 83.0,
    },
    "t1b_validation": {
        "interviews": 20,
        "total_prompts": 100,
        "unique_prompts": 82,
        "reuse_pct": 18.0,
        "unique_rate_pct": 82.0,
        "technical_case_study_unique": 17,
        "technical_case_study_reuse_pct": 15.0,
    },
}


def _build_interview_configs() -> list[tuple[RoleType, SeniorityLevel]]:
    roles = [
        RoleType.BACKEND_ENGINEER,
        RoleType.FULLSTACK_ENGINEER,
        RoleType.FRONTEND_ENGINEER,
        RoleType.DATA_ENGINEER,
        RoleType.DEVOPS_ENGINEER,
        RoleType.QA_ENGINEER,
        RoleType.ML_ENGINEER,
    ]
    seniorities = list(SeniorityLevel)

    pool = [(role, seniority) for role in roles for seniority in seniorities]

    rng = random.Random(RANDOM_SEED)
    configs: list[tuple[RoleType, SeniorityLevel]] = []

    for _ in range(INTERVIEW_COUNT):
        configs.append(rng.choice(pool))

    return configs


def _area_metrics(rows: list[diversity_audit.DeliveredQuestion]) -> dict:
    by_area: dict[str, dict] = {}

    for area in TECH_AREAS:
        area_rows = [row for row in rows if row.area == area]
        metrics = diversity_audit._global_metrics(area_rows)

        doc_counts = Counter(
            row.document_id for row in area_rows if row.document_id is not None
        )
        top_doc_share = 0.0

        if doc_counts and area_rows:
            top_doc_share = round(
                (doc_counts.most_common(1)[0][1] / len(area_rows)) * 100,
                1,
            )

        by_area[area] = {
            "total_prompts": metrics.total_prompts,
            "unique_prompts": metrics.unique_prompts,
            "reuse_pct": metrics.reuse_pct,
            "top_document_share_pct": top_doc_share,
            "top_prompt_share_pct": metrics.top_repeated[0]["reuse_pct"]
            if metrics.top_repeated
            else 0.0,
        }

    return by_area


def _profile_overlap(rows: list[diversity_audit.DeliveredQuestion]) -> list[dict]:
    grouped: dict[tuple[str, str], list[diversity_audit.DeliveredQuestion]] = defaultdict(
        list
    )

    for row in rows:
        grouped[(row.role, row.seniority)].append(row)

    profiles: list[dict] = []

    for (role, seniority), bucket in grouped.items():
        interviews = Counter(row.interview_id for row in bucket)

        if len(interviews) <= 1:
            continue

        prompt_counts = Counter(row.prompt_normalized for row in bucket)
        doc_counts = Counter(
            row.document_id for row in bucket if row.document_id is not None
        )
        total = len(bucket)
        unique = len(prompt_counts)
        repeated_doc_total = sum(c for c in doc_counts.values() if c > 1)

        profiles.append(
            {
                "profile": f"technical/{role}/{seniority}",
                "interviews": len(interviews),
                "total_prompts": total,
                "unique_prompts": unique,
                "overlap_pct": round(((total - unique) / total) * 100, 1),
                "repeated_document_share_pct": round(
                    (repeated_doc_total / total) * 100,
                    1,
                ),
            }
        )

    profiles.sort(key=lambda item: item["overlap_pct"], reverse=True)
    return profiles


def _corpus_zero_match_cells() -> dict:
    load_dotenv(PROJECT_ROOT / ".env")

    vectorstore = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(PROJECT_ROOT / "storage/chroma/interview_corpus"),
    )

    result = vectorstore._collection.get(
        where={"area": "technical_case_study"},
        include=["metadatas"],
    )

    zero_cells = 0
    case_study_cells: list[str] = []

    for role in RoleType:
        for seniority in SeniorityLevel:
            count = sum(
                1
                for metadata in result.get("metadatas") or []
                if metadata
                and metadata.get("role") == role.value
                and metadata.get("seniority") == seniority.value
                and 2 <= int(metadata.get("difficulty", 3)) <= 4
            )

            if count == 0:
                zero_cells += 1
                case_study_cells.append(f"{role.value}/{seniority.value}")

    all_areas_zero = 0

    for area in TECH_AREAS:
        area_result = vectorstore._collection.get(
            where={"area": area},
            include=["metadatas"],
        )

        for role in RoleType:
            for seniority in SeniorityLevel:
                count = sum(
                    1
                    for metadata in area_result.get("metadatas") or []
                    if metadata
                    and metadata.get("role") == role.value
                    and metadata.get("seniority") == seniority.value
                    and 2 <= int(metadata.get("difficulty", 3)) <= 4
                )

                if count == 0:
                    all_areas_zero += 1

    return {
        "technical_case_study_zero_match_cells": zero_cells,
        "all_technical_areas_zero_match_cells": all_areas_zero,
        "case_study_zero_slices": case_study_cells,
    }


def _compare_phase(baseline: dict, after: dict) -> dict:
    return {
        "total_prompts": {
            "before": baseline.get("total_prompts"),
            "after": after["total_prompts"],
        },
        "unique_prompts": {
            "before": baseline.get("unique_prompts"),
            "after": after["unique_prompts"],
            "delta": after["unique_prompts"] - baseline.get("unique_prompts", 0),
        },
        "reuse_pct": {
            "before": baseline.get("reuse_pct"),
            "after": after["reuse_pct"],
            "delta": round(after["reuse_pct"] - baseline.get("reuse_pct", 0), 1),
        },
        "unique_rate_pct": {
            "before": baseline.get("unique_rate_pct"),
            "after": after["unique_rate_pct"],
            "delta": round(
                after["unique_rate_pct"] - baseline.get("unique_rate_pct", 0),
                1,
            ),
        },
    }


def run_audit() -> dict:
    load_dotenv()
    configs = _build_interview_configs()
    corpus_by_prompt = diversity_audit._load_corpus_index()

    llm = DefaultLLMAdapter()
    provider = QuestionIntelligenceProvider(llm)

    batch_rows: list[diversity_audit.DeliveredQuestion] = []
    failures: list[dict] = []
    partial_interviews = 0
    runtime_zero_match = 0

    print(f"Running {INTERVIEW_COUNT} technical interviews (seed={RANDOM_SEED})...", flush=True)

    for index, (role, level) in enumerate(configs, start=1):
        interview_id = f"final-{index:03d}-{uuid.uuid4().hex[:8]}"

        if index % 10 == 0 or index == 1:
            print(f"[{index}/{INTERVIEW_COUNT}] {role.value} {level.value}", flush=True)

        try:
            questions = diversity_audit._run_batch_interview(
                provider,
                InterviewType.TECHNICAL,
                role,
                level,
            )
        except Exception as exc:
            failures.append(
                {
                    "interview_index": index,
                    "role": role.value,
                    "seniority": level.value,
                    "error": str(exc),
                }
            )
            continue

        if len(questions) < EXPECTED_QUESTIONS_PER_INTERVIEW:
            partial_interviews += 1

        rows = diversity_audit._collect_delivered(
            interview_id=interview_id,
            path="batch_generate",
            interview_type=InterviewType.TECHNICAL,
            role=role,
            level=level,
            questions=questions,
            corpus_by_prompt=corpus_by_prompt,
        )

        for row in rows:
            if row.document_id is None and row.generated_vs_retrieved == "retrieved":
                runtime_zero_match += 1

        batch_rows.extend(rows)

    global_metrics = diversity_audit._global_metrics(batch_rows)
    unique_rate = round(
        (global_metrics.unique_prompts / global_metrics.total_prompts) * 100,
        1,
    ) if global_metrics.total_prompts else 0.0

    doc_counts = Counter(
        row.document_id for row in batch_rows if row.document_id is not None
    )
    top_doc_share = 0.0

    if doc_counts and batch_rows:
        top_doc_share = round(
            (doc_counts.most_common(1)[0][1] / len(batch_rows)) * 100,
            1,
        )

    top_prompt_share = (
        global_metrics.top_repeated[0]["reuse_pct"]
        if global_metrics.top_repeated
        else 0.0
    )

    global_summary = {
        "total_prompts": global_metrics.total_prompts,
        "unique_prompts": global_metrics.unique_prompts,
        "reuse_pct": global_metrics.reuse_pct,
        "unique_rate_pct": unique_rate,
        "top_document_share_pct": top_doc_share,
        "top_prompt_share_pct": top_prompt_share,
    }

    corpus_zero = _corpus_zero_match_cells()

    success = {
        "completion_rate_100": len(failures) == 0 and partial_interviews == 0,
        "failures_zero": len(failures) == 0,
        "zero_match_cells_zero": corpus_zero["all_technical_areas_zero_match_cells"] == 0,
        "technical_reuse_lte_20": global_metrics.reuse_pct <= 20.0,
        "technical_unique_rate_gte_80": unique_rate >= 80.0,
        "top_doc_share_lte_5": top_doc_share <= 5.0,
    }

    role_distribution = Counter(role.value for role, _ in configs)
    seniority_distribution = Counter(level.value for _, level in configs)

    return {
        "audit": "Phase 7C-FINAL Technical Diversity Stability",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "methodology": "QuestionIntelligenceProvider.generate() batch path",
        "interview_count": INTERVIEW_COUNT,
        "random_seed": RANDOM_SEED,
        "expected_prompts": INTERVIEW_COUNT * EXPECTED_QUESTIONS_PER_INTERVIEW,
        "completion": {
            "completed_interviews": INTERVIEW_COUNT - len(failures),
            "failures": len(failures),
            "partial_interviews": partial_interviews,
            "completion_rate_pct": round(
                ((INTERVIEW_COUNT - len(failures)) / INTERVIEW_COUNT) * 100,
                1,
            ),
            "failure_details": failures[:10],
        },
        "global": global_summary,
        "by_area": _area_metrics(batch_rows),
        "profile_overlap": _profile_overlap(batch_rows),
        "corpus_zero_match": corpus_zero,
        "runtime_zero_match_occurrences": runtime_zero_match,
        "sample_distribution": {
            "role": dict(role_distribution),
            "seniority": dict(seniority_distribution),
        },
        "success_criteria": success,
        "success_criteria_all_pass": all(success.values()),
        "comparison": {
            "vs_t0": _compare_phase(BASELINES["t0_technical_b2d"], global_summary),
            "vs_t2b": _compare_phase(BASELINES["t2b_validation"], global_summary),
            "vs_t1b": _compare_phase(BASELINES["t1b_validation"], global_summary),
        },
        "area_comparison_t0_vs_final": {
            area: {
                "t0_reuse_pct_est": BASELINES["t0_technical_b2d"].get(
                    f"{area}_reuse_pct",
                    BASELINES["t0_technical_b2d"]["reuse_pct"],
                ),
                "final_reuse_pct": _area_metrics(batch_rows)[area]["reuse_pct"],
            }
            for area in [
                "technical_background",
                "technical_technical_knowledge",
                "technical_case_study",
            ]
            if area in _area_metrics(batch_rows)
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = run_audit()

    output_path = OUTPUT_DIR / "phase_7c_final_technical_stability_audit.json"
    output_path.write_text(json.dumps(report, indent=2))

    summary_path = OUTPUT_DIR / "phase_7c_final_summary.json"
    summary_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"\nFull report: {output_path}", flush=True)


if __name__ == "__main__":
    main()
